"""Offline payload and trust-boundary checks; no model, host configuration or hardware."""
from __future__ import annotations

import ast
import asyncio
import hashlib
import importlib.util
import json
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


@pytest.fixture
def source_repo(tmp_path):
    source = tmp_path / "source-repo"
    shutil.copytree(ROOT / "source", source / "source")
    shutil.copytree(ROOT / "hooks", source / "hooks")
    shutil.copy(ROOT / "catalog.json", source / "catalog.json")
    return source


def add_reviewed_markdown(source, text):
    relative = ".agents/skills/nextjs-app-router/portability.md"
    path = source / "source" / relative
    path.write_text(text)
    manifest_path = source / "source/.agents/skill-sources.json"
    manifest = json.loads(manifest_path.read_text())
    authored = next(item for item in manifest["authored_skills"] if item["name"] == "nextjs-app-router")
    authored["files"].append({"local": relative, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    manifest_path.write_text(json.dumps(manifest))


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
    path = ROOT / "source/.agents/skills/api-design-principles/assets/rest-api-template.py"
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
    assert len(names) == len(set(names)) == 41
    assert "project-bootstrap" not in names
    assert set(names) == {p.name for p in (ROOT / "source/.agents/skills").iterdir()}
    hook = next(p for p in data["plugins"] if p["id"] == "session-guidance")
    assert hook["optional"] and not hook["skills"]


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
        canonical = json.loads((ROOT / "source/.agents/skill-sources.json").read_text())
        for record in canonical["files"]:
            if record["source_id"] in selected_source_ids and record["local"].startswith(".agents/licenses/"):
                assert (plugin / record["local"].removeprefix(".agents/")).read_bytes() == (ROOT / "source" / record["local"]).read_bytes()
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
    assert "consuming repository" in ts
    assert "../../../docs/structure.md" not in ts


def test_current_outputs_match_builder():
    result = subprocess.run([sys.executable, str(ROOT / "scripts/build_plugins.py"), "--check"], cwd=ROOT,
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("failure", ["unknown-link", "missing-resource", "escaping-symlink", "duplicate-owner", "tampered-source", "unrecorded-source", "escaping-hook-symlink", "tampered-authored-resource"])
def test_invalid_source_rejected_without_partial_output(tmp_path, failure):
    source = tmp_path / "source-repo"
    source.mkdir()
    shutil.copytree(ROOT / "source", source / "source")
    shutil.copytree(ROOT / "hooks", source / "hooks")
    shutil.copy(ROOT / "catalog.json", source / "catalog.json")
    skill = source / "source/.agents/skills/nextjs-app-router"
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
        hook = source / "hooks/session-start.sh"
        hook.unlink()
        hook.symlink_to(ROOT / "hooks/session-start.sh")
    elif failure == "tampered-authored-resource":
        asset = source / "source/.agents/skills/writing-plans/assets/task-brief.md"
        asset.write_text(asset.read_text() + "\nUnreviewed original asset change.\n")
    else:
        with (skill / "SKILL.md").open("a") as stream:
            stream.write("\nUnrecorded change.\n")
    if failure in {"unknown-link", "missing-resource"}:
        manifest_path = source / "source/.agents/skill-sources.json"
        manifest = json.loads(manifest_path.read_text())
        authored = next(e for e in manifest["authored_skills"] if e["name"] == "nextjs-app-router")
        authored["files"].append({"local": ".agents/skills/nextjs-app-router/new.md",
                                  "sha256": hashlib.sha256((skill / "new.md").read_bytes()).hexdigest()})
        manifest_path.write_text(json.dumps(manifest))
    output = tmp_path / "output"
    output.mkdir()
    (output / "preserve.txt").write_text("unchanged")
    before = files(output)
    expected = {
        "unknown-link": "Undeclared outward resource",
        "missing-resource": "Missing or escaping resource",
        "escaping-symlink": "not symlinks",
        "duplicate-owner": "duplicate skill owner",
        "tampered-source": "Source hash mismatch",
        "tampered-authored-resource": "Source hash mismatch",
        "unrecorded-source": "lacks source provenance",
        "escaping-hook-symlink": "hook source is missing or escapes",
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
    source = ROOT / "source/.agents/skills/rust-best-practices/references/chapter_01.md"
    payload = tmp_path / "plugins/rust/skills/rust-best-practices/references/chapter_01.md"
    example = "// This works as a caching alternative. See: [ADR-123](link/to/adr-123)"
    assert example in source.read_text() and example in payload.read_text()
    builder().validate_links(tmp_path / "plugins/rust")


def test_recorded_notice_is_retained_with_payload_provenance(tmp_path):
    builder().build(ROOT, tmp_path)
    plugin = tmp_path / "plugins/react-ui"
    notice = plugin / "licenses/impeccable-NOTICE.md"
    canonical = ROOT / "source/.agents/licenses/impeccable-NOTICE.md"
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


@pytest.mark.parametrize("linked", [".", "source", "hooks", "catalog.json"])
def test_source_root_or_input_symlink_is_rejected(tmp_path, linked):
    source = tmp_path / "input"
    source.mkdir()
    shutil.copytree(ROOT / "source", source / "source")
    shutil.copytree(ROOT / "hooks", source / "hooks")
    shutil.copy(ROOT / "catalog.json", source / "catalog.json")
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


def test_common_native_roles_have_model_free_claude_and_explicit_codex_exports(tmp_path):
    builder().build(ROOT, tmp_path)
    plugin = tmp_path / 'plugins/common'
    for path in sorted((ROOT / 'source/agents').glob('*.toml')):
        role = tomllib.loads(path.read_text())
        assert set(role) == {'name', 'description', 'developer_instructions'}
        assert (plugin / f'exports/codex/agents/{path.name}').read_bytes() == path.read_bytes()
        claude = (plugin / f'agents/{path.stem}.md').read_text()
        assert f'name: {role["name"]}' in claude
        assert role['developer_instructions'].strip() in claude
    assert len(list((plugin / 'agents').glob('*.md'))) == 4
    assert 'extensions' not in json.loads((plugin / 'plugin.json').read_text())


def test_repeat_release_uses_catalog_version_everywhere(tmp_path):
    source = tmp_path / 'input'
    shutil.copytree(ROOT / 'source', source / 'source')
    shutil.copytree(ROOT / 'hooks', source / 'hooks')
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
    skill = (ROOT / 'source/.agents/skills/python-type-safety/SKILL.md').read_text()
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
    details = (ROOT / 'source/.agents/skills/python-type-safety/references/details.md').read_text()
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
        ROOT / "source/.agents/skills/domain-modeling/ADR-FORMAT.md"
    ).read_bytes()
    assert not (ROOT / "source/.agents/templates").exists()
    builder().validate_links(plugin)
