"""Offline payload and trust-boundary checks; no model, host configuration or hardware."""
from __future__ import annotations

import ast
import asyncio
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tomllib
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]


def builder():
    spec = importlib.util.spec_from_file_location("build_plugins", ROOT / "scripts/build_plugins.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def files(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}


def canonical_input_state(root):
    manifest = json.loads((root / "provenance/skill-sources.json").read_text())
    records = manifest["files"] + [record for entry in manifest["authored_skills"] + manifest["authored_resources"]
                                   for record in entry["files"]]
    paths = [root / record["local"] for record in records]
    paths += [root / "catalog.json", root / "provenance/skill-sources.json"]
    state = {}
    for path in paths:
        info = path.stat()
        state[path] = (path.read_bytes(), info.st_mtime_ns, info.st_ino)
    return state


@pytest.fixture
def source_repo(tmp_path):
    source = tmp_path / "source-repo"
    shutil.copytree(ROOT / "plugins", source / "plugins")
    shutil.copytree(ROOT / "provenance", source / "provenance")
    shutil.copy(ROOT / "catalog.json", source / "catalog.json")
    return source


def add_reviewed_markdown(source, text):
    relative = "plugins/nextjs/skills/nextjs-app-router/portability.md"
    path = source / relative
    path.write_text(text)
    manifest_path = source / "provenance/skill-sources.json"
    manifest = json.loads(manifest_path.read_text())
    authored = next(item for item in manifest["authored_skills"] if item["name"] == "nextjs-app-router")
    authored["files"].append({"local": relative, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    manifest_path.write_text(json.dumps(manifest))


def test_inplace_preparation_rejects_canonical_edit_without_replacing_it(source_repo):
    skill = source_repo / "plugins/common/skills/writing-plans/SKILL.md"
    edited = skill.read_bytes() + b"\nUnreviewed canonical change.\n"
    skill.write_bytes(edited)
    before = files(source_repo)
    with pytest.raises(ValueError, match="Source hash mismatch"):
        builder().build(source_repo, source_repo)
    assert files(source_repo) == before


def test_inplace_preparation_rejects_unrecorded_skill_file_without_deleting_it(source_repo):
    note = source_repo / "plugins/common/skills/writing-plans/local-note.txt"
    note.write_bytes(b"Unrecorded work must not be deleted.\n")
    before = files(source_repo)
    with pytest.raises(ValueError, match="(?i)provenance|unrecorded|unknown"):
        builder().build(source_repo, source_repo)
    assert files(source_repo) == before


@pytest.mark.parametrize("relative", [
    "plugins/common/references/engineering.md",
    "plugins/react-ui/licenses/impeccable-NOTICE.md",
    "plugins/common/exports/codex/agents/architect.toml",
    "plugins/session-guidance/hooks/session-start.sh",
])
def test_inplace_preparation_rejects_unreviewed_support_without_rewriting_it(source_repo, relative):
    canonical = source_repo / relative
    canonical.write_bytes(canonical.read_bytes() + b"\n# Unreviewed canonical support edit.\n")
    before = files(source_repo)
    with pytest.raises(ValueError, match="(?i)(source|canonical) hash mismatch"):
        builder().build(source_repo, source_repo)
    assert files(source_repo) == before


def test_repeated_inplace_preparation_never_writes_canonical_inputs(source_repo):
    before = canonical_input_state(source_repo)
    module = builder()
    module.build(source_repo, source_repo)
    module.build(source_repo, source_repo)
    assert canonical_input_state(source_repo) == before
    module.build(source_repo, source_repo, check=True)


def test_generated_write_failure_cannot_delete_or_rewrite_canonical_inputs(source_repo, monkeypatch):
    catalog_path = source_repo / "catalog.json"
    catalog = json.loads(catalog_path.read_text())
    catalog["version"] = "0.1.4+failure-check"
    catalog_path.write_text(json.dumps(catalog))
    before = canonical_input_state(source_repo)
    real_replace = os.replace

    def fail_generated_replace(source, destination, *args, **kwargs):
        target = Path(destination)
        if target.is_relative_to(source_repo) and target.name == "plugin.json":
            raise OSError("simulated generated metadata write failure")
        return real_replace(source, destination, *args, **kwargs)

    monkeypatch.setattr(os, "replace", fail_generated_replace)
    with pytest.raises(OSError, match="simulated generated metadata write failure"):
        builder().build(source_repo, source_repo)
    assert canonical_input_state(source_repo) == before


def test_unknown_plugin_file_is_rejected_without_deletion(source_repo):
    note = source_repo / "plugins/common/local-note.txt"
    note.write_bytes(b"Unregistered work outside the canonical skill directory.\n")
    before = files(source_repo)
    with pytest.raises(ValueError):
        builder().build(source_repo, source_repo)
    assert files(source_repo) == before


def test_canonical_record_cannot_claim_a_generated_manifest(source_repo):
    path = source_repo / "provenance/skill-sources.json"
    manifest = json.loads(path.read_text())
    generated = source_repo / "plugins/common/plugin.json"
    manifest["authored_resources"].append({
        "name": "invalid-generated-owner", "origin": "Invalid ownership fixture",
        "files": [{"local": "plugins/common/plugin.json", "sha256": hashlib.sha256(generated.read_bytes()).hexdigest()}],
    })
    path.write_text(json.dumps(manifest))
    before = files(source_repo)
    with pytest.raises(ValueError):
        builder().build(source_repo, source_repo)
    assert files(source_repo) == before


def test_shared_resource_cannot_have_two_canonical_plugin_owners(source_repo):
    path = source_repo / "provenance/skill-sources.json"
    manifest = json.loads(path.read_text())
    duplicate = source_repo / "plugins/rust/references/engineering.md"
    manifest["authored_resources"].append({
        "name": "invalid-second-reference-owner", "origin": "Invalid ownership fixture",
        "files": [{"local": "plugins/rust/references/engineering.md",
                   "sha256": hashlib.sha256(duplicate.read_bytes()).hexdigest()}],
    })
    path.write_text(json.dumps(manifest))
    before = files(source_repo)
    with pytest.raises(ValueError, match="Duplicate canonical resource owner"):
        builder().build(source_repo, source_repo)
    assert files(source_repo) == before


@pytest.mark.parametrize("damage", ["deleted", "overwritten"])
def test_generated_reference_is_repaired_from_its_registered_owner(source_repo, damage):
    owner = source_repo / "plugins/common/references/development.md"
    destination = source_repo / "plugins/rust/references/development.md"
    owner_note = b"\nCanonical owner fixture note.\n"
    expected = destination.read_bytes() + owner_note
    owner.write_bytes(owner.read_bytes() + owner_note)
    ledger = source_repo / "provenance/skill-sources.json"
    manifest = json.loads(ledger.read_text())
    record = next(record for entry in manifest["authored_resources"] for record in entry["files"]
                  if record["local"] == "plugins/common/references/development.md")
    record["sha256"] = hashlib.sha256(owner.read_bytes()).hexdigest()
    ledger.write_text(json.dumps(manifest))
    if damage == "deleted":
        destination.unlink()
    else:
        destination.write_bytes(b"Stale generated Rust reference.\n")
    before = canonical_input_state(source_repo)
    builder().build(source_repo, source_repo)
    assert destination.read_bytes() == expected
    assert canonical_input_state(source_repo) == before


@pytest.mark.parametrize("destination", ["ancestor", "descendant", "canonical-plugin"])
def test_external_output_cannot_overlap_canonical_input(source_repo, destination):
    output = {"ancestor": source_repo.parent, "descendant": source_repo / "output",
              "canonical-plugin": source_repo / "plugins/common"}[destination]
    before = files(source_repo.parent)
    with pytest.raises(ValueError, match="(?i)overlap|disjoint|inside|ancestor"):
        builder().build(source_repo, output)
    assert files(source_repo.parent) == before


@pytest.mark.parametrize("target", [
    "file:///tmp/private.md", "FILE:///tmp/private.md",
    "C:/private.md", r"C:\private.md", r"\\server\share\private.md", "//server/share/private.md",
    "%2Ftmp%2Fprivate.md", "%5C%5Cserver%5Cshare%5Cprivate.md",
    "C%3A%5Cprivate.md", "file%3A%2F%2F%2Ftmp%2Fprivate.md",
    " C:/private.md", "%20C%3A%5Cprivate.md",
])
@pytest.mark.parametrize("reference", [False, True])
def test_machine_local_markdown_is_rejected_without_output_changes(tmp_path, source_repo, target, reference):
    text = f"[private][resource]\n\n[resource]: {target}\n" if reference else f"[private]({target})\n"
    add_reviewed_markdown(source_repo, text)
    output = tmp_path / "output"
    for relative in ("plugins/common/keep.txt", ".agents/plugins/marketplace.json", ".claude-plugin/marketplace.json"):
        path = output / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"existing output")
    before = files(output)
    with pytest.raises(ValueError):
        builder().build(source_repo, output)
    assert files(output) == before


def test_external_and_fragment_markdown_links_are_preserved(tmp_path, source_repo):
    text = ("# Portable links\n\n"
            "[website](https://example.com/guide?q=yes#section)\n"
            "[email](mailto:maintainer@example.com)\n"
            "[local](#portable-links)\n\n"
            "[website-ref]: https://example.com/guide?q=yes#section\n"
            "[email-ref]: mailto:maintainer@example.com\n"
            "[local-ref]: #portable-links\n")
    add_reviewed_markdown(source_repo, text)
    output = tmp_path / "output"
    builder().build(source_repo, output)
    assert (output / "plugins/nextjs/skills/nextjs-app-router/portability.md").read_text() == text


@pytest.mark.parametrize("version", ["01.2.3", "1.2.3-.", "1.2.3-a..b", "1.2.3-01"])
def test_invalid_semantic_version_is_rejected_before_output_changes(tmp_path, source_repo, version):
    catalog_path = source_repo / "catalog.json"
    catalog = json.loads(catalog_path.read_text())
    catalog["version"] = version
    catalog_path.write_text(json.dumps(catalog))
    output = tmp_path / "output"
    output.mkdir()
    (output / "keep.txt").write_bytes(b"existing output")
    before = files(output)
    with pytest.raises(ValueError, match="explicit semantic version"):
        builder().build(source_repo, output)
    assert files(output) == before


@pytest.mark.parametrize("version", ["0.1.1-rc.1", "1.2.3-alpha.0.z-1", "1.2.3+build.01", "1.2.3-rc.1+sha.abc"])
def test_semantic_prerelease_and_build_versions_reach_generated_manifests(tmp_path, source_repo, version):
    catalog_path = source_repo / "catalog.json"
    catalog = json.loads(catalog_path.read_text())
    catalog["version"] = version
    catalog_path.write_text(json.dumps(catalog))
    output = tmp_path / "output"
    builder().build(source_repo, output)
    for plugin in catalog["plugins"]:
        for relative in ("plugin.json", ".claude-plugin/plugin.json", "provenance.json"):
            assert json.loads((output / "plugins" / plugin["id"] / relative).read_text())["version"] == version


def test_rest_api_missing_user_emits_structured_error_details():
    """Exercise the real route body, not FastAPI routing or Pydantic validation."""
    path = ROOT / "plugins/api-contracts/skills/api-design-principles/assets/rest-api-template.py"
    module = ast.parse(path.read_text())
    route = next(node for node in module.body if isinstance(node, ast.AsyncFunctionDef) and node.name == "get_user")
    # Remove only import-time FastAPI decorator/default wiring; keep the route body intact.
    route.decorator_list = []
    route.args.defaults = []

    class CapturedHTTPException(Exception):
        def __init__(self, *, status_code, detail):
            self.status_code = status_code
            self.detail = detail
            super().__init__(detail)

    namespace = {"HTTPException": CapturedHTTPException, "status": SimpleNamespace(HTTP_404_NOT_FOUND=404)}
    exec(compile(ast.Module(body=[route], type_ignores=[]), str(path), "exec"), namespace)
    with pytest.raises(CapturedHTTPException) as raised:
        asyncio.run(namespace["get_user"]("999"))
    assert raised.value.status_code == 404
    assert raised.value.detail == {
        "message": "User not found",
        "details": [{"field": "user_id", "message": "User 999 not found", "code": "not_found"}],
    }


def test_catalog_has_exact_nonoverlapping_owners():
    data = json.loads((ROOT / "catalog.json").read_text())
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]
    assert project["version"] == data["version"]
    locked = tomllib.loads((ROOT / "uv.lock").read_text())["package"]
    assert next(p["version"] for p in locked if p["name"] == project["name"]) == data["version"]
    assert len(data["plugins"]) == 13
    names = [s for p in data["plugins"] for s in p["skills"]]
    assert len(names) == len(set(names)) == 42
    assert "project-bootstrap" not in names
    assert set(names) == {p.parent.name for p in (ROOT / "plugins").glob("*/skills/*/SKILL.md")}
    hook = next(p for p in data["plugins"] if p["id"] == "session-guidance")
    assert hook["optional"] and not hook["skills"]


def test_ui_ux_search_works_from_closed_plugin_without_project_or_payload_writes(tmp_path):
    output = tmp_path / "plugin payload with spaces"
    builder().build(ROOT, output)
    script = output / "plugins/react-ui/skills/ui-ux-pro-max/scripts/search.py"
    assert script.is_file(), "react-ui must include the portable UI UX Pro Max search tool"
    project = tmp_path / "consumer project"
    home = tmp_path / "empty home"
    project.mkdir()
    home.mkdir()
    (project / "DESIGN.md").write_text("Keep the approved dark palette and operator controls.\n")
    before = files(tmp_path)
    result = subprocess.run(
        [sys.executable, "-B", str(script), "focus not obscured minimum", "--domain", "ux", "--json"],
        cwd=project, env={"PATH": os.defpath, "HOME": str(home)},
        capture_output=True, text=True, timeout=15,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert report["domain"] == "ux" and report["count"] > 0
    assert report["results"][0]["Issue"] == "Focus Not Obscured (Minimum)"
    assert files(tmp_path) == before


def test_ui_ux_design_recommendation_is_readonly_and_persistence_preserves_existing_design(tmp_path):
    output = tmp_path / "payload"
    builder().build(ROOT, output)
    script = output / "plugins/react-ui/skills/ui-ux-pro-max/scripts/search.py"
    assert script.is_file(), "react-ui must include the design recommendation tool and its data"
    project = tmp_path / "consumer"
    home = tmp_path / "empty home"
    project.mkdir()
    home.mkdir()
    command = [sys.executable, "-B", str(script), "SaaS", "--design-system",
               "--json", "-p", "Ops Console"]
    env = {"PATH": os.defpath, "HOME": str(home)}
    before = files(tmp_path)
    result = subprocess.run(command, cwd=project, env=env, capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert report["design_system"]["colors"] and report["design_system"]["typography"]
    assert report["design_system"]["reasoning_default"] is False
    assert report["design_system"]["source_identities"]["product"] == "SaaS (General)"
    assert report["design_system"]["source_identities"]["reasoning"] == "SaaS (General)"
    assert report["persistence"] is None
    assert files(tmp_path) == before

    master = project / "design-system/ops-console/MASTER.md"
    master.parent.mkdir(parents=True)
    master.write_text("Approved operator design; do not replace.\n")
    before = files(tmp_path)
    result = subprocess.run(command + ["--persist", "--output-dir", str(project)], cwd=project,
                            env=env, capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["persistence"]["status"] == "skipped_exists"
    assert files(tmp_path) == before


def test_ui_ux_design_search_discloses_unmatched_product_instead_of_claiming_a_match(tmp_path):
    builder().build(ROOT, tmp_path / "payload")
    script = tmp_path / "payload/plugins/react-ui/skills/ui-ux-pro-max/scripts/search.py"
    project = tmp_path / "consumer"
    project.mkdir()
    before = files(tmp_path)
    result = subprocess.run(
        [sys.executable, "-B", str(script), "zzzznotacatalogentryqvx", "--design-system", "--json"],
        cwd=project, env={"PATH": os.defpath, "HOME": str(project)},
        capture_output=True, text=True, timeout=15,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)["design_system"]
    assert report["reasoning_default"] is True
    assert report["source_identities"]["product"] is None
    assert report["source_identities"]["reasoning"] is None
    assert files(tmp_path) == before


def test_canonical_skills_and_support_have_no_source_mirror():
    assert (ROOT / "provenance/skill-sources.json").is_file()
    assert (ROOT / "plugins/common/references/engineering.md").is_file()
    assert (ROOT / "plugins/common/exports/codex/agents/architect.toml").is_file()
    assert (ROOT / "plugins/session-guidance/hooks/session-start.sh").is_file()
    assert not (ROOT / "source").exists()
    assert not (ROOT / "hooks").exists()


def test_authored_spec_guidance_does_not_impose_consumer_paths():
    root = ROOT / "plugins/common/skills/spec-driven-development"
    text = (root / "SKILL.md").read_text()
    form = (root / "assets/change-spec.md").read_text()
    assert "Maintain durable product/technical contracts under `docs/specs/`" not in text
    assert ".omx/plans" not in text + form
    assert "유지할 계약은 `docs/specs/`" not in form
    assert "look up `.agents/README.md`" not in text
    assert "look up `docs/adr/README.md`" not in text


def test_authored_typescript_guidance_does_not_require_consumer_template_files():
    text = (ROOT / "plugins/typescript/skills/typescript-project-structure/SKILL.md").read_text()
    assert "look up `docs/structure.md`" not in text
    assert "look up `.agents/README.md`" not in text


def test_authored_nextjs_and_robotics_do_not_assume_consumer_layout():
    nextjs = (ROOT / "plugins/nextjs/skills/nextjs-app-router/SKILL.md").read_text()
    robotics = (ROOT / "plugins/robotics/skills/robotics-software/SKILL.md").read_text()
    assert "`app/`" in nextjs
    assert "`src/app/`" in nextjs
    assert "across the Python agent, API and UI" not in robotics


@pytest.mark.parametrize("relative", [
    "common/skills/monorepo-contract-change/SKILL.md",
    "common/skills/spec-driven-development/SKILL.md",
    "typescript/skills/typescript-project-structure/SKILL.md",
    "robotics/skills/robotics-software/SKILL.md",
])
def test_authored_reference_callers_prioritize_actual_project_conventions(relative):
    text = " ".join((ROOT / "plugins" / relative).read_text().lower().split())
    assert "do not override the consuming project's actual conventions" in text


def test_shared_reference_examples_do_not_impose_template_paths():
    for bundle in ("common", "typescript", "robotics", "rust", "cpp-firmware"):
        root = ROOT / "plugins" / bundle / "references"
        for name in ("architecture.md", "development.md", "engineering.md", "robotics.md", "rust.md"):
            path = root / name
            if path.exists():
                text = path.read_text()
                assert "look up `.agents/README.md`" not in text, path
                assert "look up `docs/specs/README.md`" not in text, path
                assert "look up `docs/adr/README.md`" not in text, path
                assert "Standalone은 root `src/`를 product source의 출발점" not in text, path
    assert "apps/api/" in (ROOT / "plugins/common/references/architecture.md").read_text()


def test_plugin_sources_retain_selected_unmodified_upstream_files():
    """Unmodified upstream examples remain traceable after moving their containing tree."""
    manifest = json.loads((ROOT / "provenance/skill-sources.json").read_text())
    for local in ("plugins/react-ui/skills/ui-ux-pro-max/scripts/core.py",
                  "plugins/common/skills/domain-modeling/ADR-FORMAT.md",
                  "plugins/common/skills/domain-modeling/GLOSSARY-FORMAT.md"):
        record = next(item for item in manifest["files"] if item["local"] == local)
        assert hashlib.sha256((ROOT / local).read_bytes()).hexdigest() == record["upstream_sha256"]


@pytest.mark.parametrize("filename,upstream_hash", [
    ("design_system.py", "e7d1c94c4b2eada17c5551157668362659ccf9626d34dbd58e68142410f90103"),
    ("search.py", "9fd5acc991142fd43c3afe7be0f6720911b668f3988b34e74b5cbc41d58e7947"),
])
def test_ui_runtime_safety_adaptations_preserve_distinct_upstream_evidence(filename, upstream_hash):
    manifest = json.loads((ROOT / "provenance/skill-sources.json").read_text())
    local = f"plugins/react-ui/skills/ui-ux-pro-max/scripts/{filename}"
    record = next(item for item in manifest["files"] if item["local"] == local)
    assert record["source_id"] == "ui-ux-pro-max"
    assert record["source"] == f"src/ui-ux-pro-max/scripts/{filename}"
    assert record["upstream_sha256"] == upstream_hash
    assert record["sha256"] == hashlib.sha256((ROOT / local).read_bytes()).hexdigest()
    assert record["sha256"] != upstream_hash
    assert record["modifications"].strip()


def test_generated_brand_preserves_marketplace_identity(tmp_path):
    builder().build(ROOT, tmp_path)
    codex = json.loads((tmp_path / ".agents/plugins/marketplace.json").read_text())
    claude = json.loads((tmp_path / ".claude-plugin/marketplace.json").read_text())
    assert codex["name"] == claude["name"] == "konglabs-agent-skills"
    assert codex["interface"]["displayName"] == "KongLabs Agent Skills"
    assert claude["owner"]["name"] == "KongLabs"
    for plugin in (tmp_path / "plugins").iterdir():
        for relative in ("plugin.json", ".claude-plugin/plugin.json"):
            assert json.loads((plugin / relative).read_text())["author"]["name"] == "KongLabs"


def test_build_is_deterministic_and_closed(tmp_path):
    module = builder()
    module.build(ROOT, tmp_path / "first")
    module.build(ROOT, tmp_path / "second")
    assert files(tmp_path / "first") == files(tmp_path / "second")
    for plugin in (tmp_path / "first/plugins").iterdir():
        module.validate_links(plugin)
        assert not any(p.is_symlink() for p in plugin.rglob("*"))
        artifact = json.loads((plugin / "artifact-hashes.json").read_text())
        actual = {name: hashlib.sha256(content).hexdigest() for name, content in files(plugin).items()
                  if name != "artifact-hashes.json"}
        assert artifact["files"] == actual
        portable = json.loads((plugin / "plugin.json").read_text())
        claude = json.loads((plugin / ".claude-plugin/plugin.json").read_text())
        assert portable["name"] == claude["name"] == plugin.name
        assert portable["version"] == claude["version"] == json.loads((ROOT / "catalog.json").read_text())["version"]


def test_generated_skill_inventory_and_license_coverage(tmp_path):
    module = builder()
    module.build(ROOT, tmp_path)
    catalog = json.loads((ROOT / "catalog.json").read_text())
    for entry in catalog["plugins"]:
        plugin = tmp_path / "plugins" / entry["id"]
        assert sorted(p.parent.name for p in plugin.glob("skills/*/SKILL.md")) == sorted(entry["skills"])
        provenance = json.loads((plugin / "provenance.json").read_text())
        selected_source_ids = {source["id"] for source in provenance["sources"]}
        canonical = json.loads((ROOT / "provenance/skill-sources.json").read_text())
        for record in canonical["files"]:
            if record["source_id"] in selected_source_ids and "/licenses/" in record["local"]:
                assert (plugin / "licenses" / Path(record["local"]).name).read_bytes() == (ROOT / record["local"]).read_bytes()
        for source in provenance["sources"]:
            assert source["revision"]
            assert (plugin / source["license"]).is_file()
        for record in provenance["files"]:
            assert record["upstream_sha256"] and record["source_sha256"]
            assert hashlib.sha256((plugin / record["local"]).read_bytes()).hexdigest() == record["payload_sha256"]


def test_cross_bundle_reference_is_identity_not_escape(tmp_path):
    builder().build(ROOT, tmp_path)
    text = (tmp_path / "plugins/litestar/skills/litestar-backend/SKILL.md").read_text()
    assert "api-contracts:api-design-principles" in text
    assert "../api-design-principles/SKILL.md" not in text
    ts = (tmp_path / "plugins/typescript/skills/typescript-project-structure/SKILL.md").read_text()
    assert "common:monorepo-contract-change" in ts
    assert "react-ui:vercel-composition-patterns" in ts
    assert "../../../docs/structure.md" not in ts


def test_imported_workflow_reference_keeps_consumer_lookup_not_provider_path(tmp_path):
    builder().build(ROOT, tmp_path / "output")
    text = (tmp_path / "output/plugins/common/skills/writing-for-agents/SKILL-MECHANICS.md").read_text()
    assert "look up `.agents/README.md#required-skill-selection-and-evidence`" in text
    assert "library/README.md" not in text


def test_current_outputs_match_builder():
    result = subprocess.run([sys.executable, str(ROOT / "scripts/build_plugins.py"), "--check"], cwd=ROOT,
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("failure", ["unknown-link", "missing-resource", "escaping-symlink", "duplicate-owner", "tampered-source", "unrecorded-source", "escaping-hook-symlink", "tampered-authored-resource"])
def test_invalid_source_rejected_without_partial_output(tmp_path, source_repo, failure):
    source = source_repo
    skill = source / "plugins/nextjs/skills/nextjs-app-router"
    if failure == "unknown-link":
        (skill / "new.md").write_text("[undeclared](../../../private-guide.md)\n")
    elif failure == "missing-resource":
        (skill / "new.md").write_text("[missing](missing.md)\n")
    elif failure == "escaping-symlink":
        (skill / "outside.md").symlink_to(ROOT / "README.md")
    elif failure == "duplicate-owner":
        catalog = json.loads((source / "catalog.json").read_text())
        catalog["plugins"][0]["skills"].append("nextjs-app-router")
        (source / "catalog.json").write_text(json.dumps(catalog))
    elif failure == "unrecorded-source":
        (skill / "new.md").write_text("Unreviewed resource.\n")
    elif failure == "escaping-hook-symlink":
        hook = source / "plugins/session-guidance/hooks/session-start.sh"
        hook.unlink()
        hook.symlink_to(ROOT / "plugins/session-guidance/hooks/session-start.sh")
    elif failure == "tampered-authored-resource":
        asset = source / "plugins/common/skills/writing-plans/assets/task-brief.md"
        asset.write_text(asset.read_text() + "\nUnreviewed original asset change.\n")
    else:
        with (skill / "SKILL.md").open("a") as stream:
            stream.write("\nUnrecorded change.\n")
    if failure in {"unknown-link", "missing-resource"}:
        manifest_path = source / "provenance/skill-sources.json"
        manifest = json.loads(manifest_path.read_text())
        authored = next(e for e in manifest["authored_skills"] if e["name"] == "nextjs-app-router")
        authored["files"].append({"local": "plugins/nextjs/skills/nextjs-app-router/new.md",
                                  "sha256": hashlib.sha256((skill / "new.md").read_bytes()).hexdigest()})
        manifest_path.write_text(json.dumps(manifest))
    output = tmp_path / "output"
    output.mkdir()
    (output / "preserve.txt").write_text("unchanged")
    before = files(output)
    expected = {
        "unknown-link": "(?i)link|resource",
        "missing-resource": "(?i)link|resource",
        "escaping-symlink": "symlink",
        "duplicate-owner": "duplicate skill owner",
        "tampered-source": "(?i)(source|canonical) hash mismatch",
        "tampered-authored-resource": "(?i)(source|canonical) hash mismatch",
        "unrecorded-source": "(?i)provenance|unrecorded|unknown",
        "escaping-hook-symlink": "symlink",
    }
    with pytest.raises(ValueError, match=expected[failure]):
        builder().build(source, output)
    assert files(output) == before


def test_optional_hook_is_printf_only_and_path_with_spaces_works(tmp_path):
    builder().build(ROOT, tmp_path)
    bundle = tmp_path / "plugins/session-guidance"
    config = json.loads((bundle / "hooks/hooks.json").read_text())
    command = config["hooks"]["SessionStart"][0]["hooks"][0]["command"]
    assert command == 'sh "${CLAUDE_PLUGIN_ROOT}/hooks/session-start.sh"'
    for manifest in (bundle / "plugin.json", bundle / ".claude-plugin/plugin.json"):
        data = json.loads(manifest.read_text())
        assert "hooks" not in data and "extensions" not in data
    spaced = tmp_path / "plugin with spaces"
    shutil.copytree(bundle, spaced)
    import os
    env = dict(os.environ, CLAUDE_PLUGIN_ROOT=str(spaced))
    result = subprocess.run(["sh", "-c", command], env=env, input='{"event":"SessionStart"}',
                            capture_output=True, text=True, timeout=3)
    assert result.returncode == 0 and not result.stderr
    assert "AGENTS.md" in result.stdout and "latest user" in result.stdout
    script = (spaced / "hooks/session-start.sh").read_text()
    assert all(line.startswith(("#!", "#", "printf ", "'")) or not line.strip()
               for line in script.splitlines())


def test_fenced_reference_examples_are_preserved_not_resolved(tmp_path):
    builder().build(ROOT, tmp_path)
    source = ROOT / "plugins/rust/skills/rust-best-practices/references/chapter_01.md"
    payload = tmp_path / "plugins/rust/skills/rust-best-practices/references/chapter_01.md"
    example = "// This works as a caching alternative. See: [ADR-123](link/to/adr-123)"
    assert example in source.read_text() and example in payload.read_text()
    builder().validate_links(tmp_path / "plugins/rust")


def test_recorded_notice_is_retained_with_payload_provenance(tmp_path):
    builder().build(ROOT, tmp_path)
    plugin = tmp_path / "plugins/react-ui"
    notice = plugin / "licenses/impeccable-NOTICE.md"
    canonical = ROOT / "plugins/react-ui/licenses/impeccable-NOTICE.md"
    assert notice.is_file(), "Selected source NOTICE is recorded even when no skill links it"
    assert notice.read_bytes() == canonical.read_bytes()
    expected_hash = hashlib.sha256(canonical.read_bytes()).hexdigest()
    provenance = json.loads((plugin / "provenance.json").read_text())
    record = next(f for f in provenance["files"] if f["local"] == "licenses/impeccable-NOTICE.md")
    assert record["source_id"] == "impeccable"
    assert record["source_sha256"] == record["payload_sha256"] == expected_hash
    artifacts = json.loads((plugin / "artifact-hashes.json").read_text())
    assert artifacts["files"]["licenses/impeccable-NOTICE.md"] == expected_hash


@pytest.mark.parametrize("check", [False, True])
@pytest.mark.parametrize("managed", [".", ".agents", ".agents/plugins", ".agents/plugins/marketplace.json",
                                      ".claude-plugin", ".claude-plugin/marketplace.json",
                                      "plugins", "plugins/common/plugin.json"])
def test_output_symlink_is_rejected_before_any_existing_bytes_change(tmp_path, managed, check):
    output = tmp_path / "output"
    output.mkdir()
    (output / "plugins/common").mkdir(parents=True)
    (output / "plugins/common/keep.txt").write_bytes(b"existing generated bytes")
    outside = tmp_path / "outside"
    (outside / "plugins").mkdir(parents=True)
    (outside / "marketplace.json").write_bytes(b"outside catalog sentinel")
    (outside / "plugins/marketplace.json").write_bytes(b"outside nested catalog sentinel")
    if managed == ".":
        shutil.rmtree(output)
        output.symlink_to(outside, target_is_directory=True)
    else:
        link = output / managed
        link.parent.mkdir(parents=True, exist_ok=True)
        if link.is_dir():
            shutil.rmtree(link)
        target = outside / "marketplace.json" if link.suffix == ".json" else outside
        link.symlink_to(target, target_is_directory=target.is_dir())
    before_output, before_outside = files(output), files(outside)
    with pytest.raises(ValueError, match="symlink"):
        builder().build(ROOT, output, check=check)
    assert files(output) == before_output
    assert files(outside) == before_outside


@pytest.mark.parametrize("linked", [".", "plugins", "provenance", "catalog.json"])
def test_source_root_or_input_symlink_is_rejected(tmp_path, source_repo, linked):
    source = source_repo
    if linked == ".":
        alias = tmp_path / "input-link"
        alias.symlink_to(source, target_is_directory=True)
        source = alias
    else:
        link = source / linked
        if link.is_dir():
            shutil.rmtree(link)
        else:
            link.unlink()
        link.symlink_to(ROOT / linked, target_is_directory=linked != "catalog.json")
    output = tmp_path / "output"
    output.mkdir()
    (output / "keep.txt").write_bytes(b"unchanged output")
    before = files(output)
    with pytest.raises(ValueError, match="symlink"):
        builder().build(source, output)
    assert files(output) == before


@pytest.mark.parametrize("managed", [".agents", "plugins", ".claude-plugin/marketplace.json"])
def test_output_wrong_file_type_is_rejected_before_mutation(tmp_path, managed):
    output = tmp_path / "output"
    (output / "plugins/common").mkdir(parents=True)
    (output / "plugins/common/keep.txt").write_bytes(b"existing generated bytes")
    target = output / managed
    if target.is_dir():
        shutil.rmtree(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.suffix == ".json":
        target.mkdir()
    else:
        target.write_bytes(b"not a directory")
    before = files(output)
    with pytest.raises(ValueError, match="wrong file type"):
        builder().build(ROOT, output)
    assert files(output) == before


def test_output_root_with_parent_traversal_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="parent traversal"):
        builder().build(ROOT, tmp_path / "unused" / ".." / "output")
    assert not (tmp_path / "output").exists()


def test_portable_roles_read_applicable_host_guidance():
    for path in sorted((ROOT / 'plugins/common/exports/codex/agents').glob('*.toml')):
        instructions = tomllib.loads(path.read_text())['developer_instructions']
        assert 'AGENTS.md' in instructions and 'CLAUDE.md' in instructions
        assert 'when present' in instructions


def test_common_native_roles_have_model_free_claude_and_explicit_codex_exports(tmp_path):
    builder().build(ROOT, tmp_path)
    plugin = tmp_path / 'plugins/common'
    for path in sorted((ROOT / 'plugins/common/exports/codex/agents').glob('*.toml')):
        role = tomllib.loads(path.read_text())
        assert set(role) == {'name', 'description', 'developer_instructions'}
        assert (plugin / f'exports/codex/agents/{path.name}').read_bytes() == path.read_bytes()
        claude = (plugin / f'agents/{path.stem}.md').read_text()
        assert f'name: {role["name"]}' in claude
        assert role['developer_instructions'].strip() in claude
    assert len(list((plugin / 'agents').glob('*.md'))) == 4
    assert 'extensions' not in json.loads((plugin / 'plugin.json').read_text())


def test_repeat_release_uses_catalog_version_everywhere(tmp_path, source_repo):
    source = source_repo
    catalog = json.loads((ROOT / 'catalog.json').read_text())
    catalog['version'] = '0.1.1'
    (source / 'catalog.json').write_text(json.dumps(catalog))
    builder().build(source, tmp_path / 'out')
    for plugin in catalog['plugins']:
        root = tmp_path / 'out/plugins' / plugin['id']
        for name in ('plugin.json', '.claude-plugin/plugin.json', 'provenance.json'):
            assert json.loads((root / name).read_text())['version'] == '0.1.1'
    entries = json.loads((tmp_path / 'out/.claude-plugin/marketplace.json').read_text())['plugins']
    assert all('version' not in entry for entry in entries)


def test_python_type_examples_support_none_and_older_generic_aliases():
    import ast
    import re
    skill = (ROOT / 'plugins/python/skills/python-type-safety/SKILL.md').read_text()
    code = re.search(r'### Pattern 4: Generic Classes.*?```python\n(.*?)```', skill, re.S)[1]
    code = code.split('# Usage preserves types')[0]
    namespace = {}
    ast.parse(code, feature_version=(3, 10))
    exec(code, namespace)
    result = namespace['Result'](value=None)
    assert result.is_success and result.unwrap() is None and result.unwrap_or('fallback') is None
    with pytest.raises(ValueError):
        namespace['Result']()
    error = RuntimeError('failure')
    failed = namespace['Result'](error=error)
    assert failed.is_failure and failed.unwrap_or('fallback') == 'fallback'
    with pytest.raises(RuntimeError, match='failure'):
        failed.unwrap()
    details = (ROOT / 'plugins/python/skills/python-type-safety/references/details.md').read_text()
    block = re.search(r'# Python 3.10-3.11 style.*?\n(.*?)```', details, re.S)[1]
    ast.parse(block, feature_version=(3, 10))
    namespace = {'Request': str}
    exec(block, namespace)
    assert namespace['Handler'][int]


def test_shared_methodology_is_closed_plugin_resource_not_project_document_lookup(tmp_path):
    builder().build(ROOT, tmp_path)
    for bundle, references in {"common": ("development", "architecture"), "robotics": ("robotics",)}.items():
        plugin = tmp_path / "plugins" / bundle
        records = json.loads((plugin / "provenance.json").read_text())["supporting_resources"]
        for name in references:
            path = plugin / "references" / (name + ".md")
            assert path.is_file()
            record = next(item for item in records if item["local"] == f"references/{name}.md")
            source = ROOT / record["canonical_source"]
            assert source.is_file()
            assert hashlib.sha256(source.read_bytes()).hexdigest() == record["source_sha256"]
            assert hashlib.sha256(path.read_bytes()).hexdigest() == record["payload_sha256"]
        builder().validate_links(plugin)
    robotics = (tmp_path / "plugins/robotics/skills/robotics-software/SKILL.md").read_text()
    assert "../../references/robotics.md" in robotics


def test_common_forms_are_closed_authored_assets_without_consumer_template_dependency(tmp_path):
    builder().build(ROOT, tmp_path)
    plugin = tmp_path / "plugins/common"
    assets = ("writing-plans/assets/task-brief.md", "spec-driven-development/assets/change-spec.md",
              "docs-sync/assets/readme.md")
    provenance = json.loads((plugin / "provenance.json").read_text())
    for relative in assets:
        path = plugin / "skills" / relative
        assert path.is_file(), f"Reusable form must ship with its owning skill: {relative}"
        record = next(item for item in provenance["authored_files"] if item["local"] == f"skills/{relative}")
        assert "upstream_sha256" not in record, "Team assets are not upstream imports"
        assert hashlib.sha256((ROOT / record["canonical_source"]).read_bytes()).hexdigest() == record["source_sha256"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == record["payload_sha256"]
    for path in plugin.rglob("*.md"):
        assert ".agents/templates/" not in path.read_text(), f"Generic asset still assumes consumer form copies: {path}"
    assert (plugin / "skills/domain-modeling/ADR-FORMAT.md").read_bytes() == (
        ROOT / "plugins/common/skills/domain-modeling/ADR-FORMAT.md"
    ).read_bytes()
    assert not (ROOT / "source/templates").exists()
    builder().validate_links(plugin)
