#!/usr/bin/env python3
"""Build closed plugin payloads from reviewed source; never touch agent host configuration."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import posixpath
import re
import shutil
import tempfile
import tomllib
from urllib.parse import unquote, urlsplit

INLINE = re.compile(r"!?\[([^\]\n]*)\]\(([^)\n]+)\)")
REFERENCE = re.compile(r"^\[([^\]\n]+)\]:\s*(\S+)", re.MULTILINE)
IDENTIFIER = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
# SemVer 2.0.0: https://semver.org/ (numeric prerelease identifiers have no leading zeroes).
SEMVER = re.compile(
    r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)"
    r"(?:-(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*)"
    r"(?:\.(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*))*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
)
# These are consuming-project contracts, not files installed from a plugin cache.
PROJECT_CONTEXT = {
    "README.md", ".agents/README.md",
    "docs/adr/README.md", "docs/specs/README.md", "docs/structure.md",
}
PORTABLE_REFERENCES = {
    f".agents/references/{name}.md"
    for name in ("engineering", "rust", "cpp-firmware", "development", "architecture", "robotics")
}
DESCRIPTIONS = {
    "common": "Task-scoped shared engineering, design, testing and review procedures",
    "python": "Python package, design, error, resource, async and testing procedures",
    "typescript": "TypeScript runtime, module, package and type boundaries",
    "react-ui": "React composition, frontend design, performance and accessibility",
    "api-contracts": "API and wire contract design and review",
    "fastapi": "FastAPI HTTP, dependency and lifecycle boundaries",
    "litestar": "Litestar HTTP, dependency and lifecycle boundaries",
    "nestjs": "NestJS modules, providers, DTO and HTTP boundaries",
    "nextjs": "Next.js App Router, server/client, data and HTTP boundaries",
    "rust": "Rust ownership, fallibility, public modules and native checks",
    "cpp-firmware": "C++ firmware ownership, timing, resources and non-actuating checks",
    "robotics": "Robot/device units, clocks, authority, freshness and safety boundaries",
    "session-guidance": "Optional advisory-only SessionStart reminder; requires separate hook trust",
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_bytes(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def local_target(raw: str) -> tuple[str, str] | None:
    target = raw.split(' "', 1)[0].strip("<>")
    decoded = unquote(target).lstrip()
    scheme = urlsplit(decoded).scheme
    if decoded.startswith(("/", "\\")) or re.match(r"^[A-Za-z]:", decoded) or scheme == "file":
        raise ValueError(f"Absolute Markdown resource is not portable: {target}")
    if not target or target.startswith("#") or scheme:
        return None
    path, _, anchor = target.partition("#")
    return unquote(path), anchor


def markdown_parts(text: str):
    """Yield prose versus fenced examples; example links are not installable resources."""
    fence = None
    for line in text.splitlines(keepends=True):
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if fence:
            yield False, line
            if marker and marker[1][0] == fence[0] and len(marker[1]) >= len(fence):
                fence = None
        elif marker:
            fence = marker[1]
            yield False, line
        else:
            yield True, line


def load_source(root: Path):
    for path in (root, root / "source", root / "hooks", root / "catalog.json"):
        if path.is_symlink():
            raise ValueError(f"Canonical source root/input must not be a symlink: {path}")
    catalog = json.loads((root / "catalog.json").read_text())
    if catalog.get("schema_version") != 1 or not IDENTIFIER.fullmatch(catalog.get("marketplace", "")):
        raise ValueError("Invalid catalog schema or marketplace identity")
    if not SEMVER.fullmatch(catalog.get("version", "")):
        raise ValueError("Catalog version must be an explicit semantic version")
    plugins = catalog.get("plugins", [])
    ids = [p["id"] for p in plugins]
    if len(ids) != len(set(ids)) or any(not IDENTIFIER.fullmatch(p) for p in ids):
        raise ValueError("Invalid or duplicate plugin identity")
    owners = {}
    for plugin in plugins:
        for required in plugin.get("requires", []):
            if required not in ids or required == plugin["id"]:
                raise ValueError(f"Invalid bundle dependency: {required}")
        for skill in plugin["skills"]:
            if not IDENTIFIER.fullmatch(skill) or skill in owners:
                raise ValueError(f"Invalid or duplicate skill owner: {skill}")
            owners[skill] = plugin["id"]
    source = root / "source"
    for path in source.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"Canonical source must contain ordinary files, not symlinks: {path}")
    actual = {p.name for p in (source / ".agents/skills").iterdir() if p.is_dir()}
    if set(owners) != actual:
        raise ValueError(f"Skill ownership differs from canonical source: {set(owners) ^ actual}")
    manifest = json.loads((source / ".agents/skill-sources.json").read_text())
    authored = manifest["authored_skills"] + manifest.get("authored_resources", [])
    records = manifest["files"] + [f for entry in authored for f in entry["files"]]
    for record in records:
        relative = record["local"]
        if relative.startswith("/") or posixpath.normpath(relative) != relative or "\\" in relative:
            raise ValueError(f"Provenance source path is not canonical: {relative}")
        path = source / relative
        if not path.resolve().is_relative_to(source.resolve()) or not path.is_file():
            raise ValueError(f"Missing or escaping provenance source: {record['local']}")
        if digest(path.read_bytes()) != record["sha256"]:
            raise ValueError(f"Source hash mismatch: {record['local']}; review and record local adaptation first")
    recorded = {record["local"] for record in records}
    for path in (source / ".agents/skills").rglob("*"):
        if path.is_file() and path.relative_to(source).as_posix() not in recorded:
            raise ValueError(f"Skill resource lacks source provenance: {path.relative_to(source)}")
    hook = root / "hooks/session-start.sh"
    if hook.is_symlink() or not hook.resolve().is_relative_to(root.resolve()) or not hook.is_file():
        raise ValueError("Optional hook source is missing or escapes this repository")
    for name in owners:
        entry = (source / f".agents/skills/{name}/SKILL.md").read_text()
        if not re.search(rf"^name:\s*{re.escape(name)}\s*$", entry, re.MULTILINE):
            raise ValueError(f"Skill frontmatter name differs from its canonical identity: {name}")
    return catalog, owners, manifest


def render(root: Path) -> dict[str, bytes]:
    catalog, owners, manifest = load_source(root)
    source = root / "source"
    output: dict[str, bytes] = {}
    source_by_id = {record["id"]: record for record in manifest["sources"]}
    record_by_path = {record["local"]: record for record in manifest["files"]}
    authored = manifest["authored_skills"] + manifest.get("authored_resources", [])
    authored_by_path = {f["local"]: entry for entry in authored for f in entry["files"]}
    for plugin in catalog["plugins"]:
        pid = plugin["id"]
        payload: dict[str, bytes] = {}
        copied: dict[str, str] = {}
        cross_bundles = set(plugin.get("requires", []))
        selected_sources: set[str] = set()

        def destination(path: str) -> str:
            if path.startswith("/") or posixpath.normpath(path) != path or "\\" in path:
                raise ValueError(f"Resource path is not canonical: {path}")
            if path.startswith(".agents/skills/"):
                return path.removeprefix(".agents/")
            if path in PORTABLE_REFERENCES or path.startswith(".agents/licenses/"):
                return path.removeprefix(".agents/")
            raise ValueError(f"Resource is not declared portable: {path}")

        def add(path: str) -> str:
            dest = destination(path)
            if path in copied:
                return dest
            real = (source / path).resolve()
            if not real.is_relative_to(source.resolve()) or not real.is_file():
                raise ValueError(f"Missing or escaping resource: {path}")
            copied[path] = dest  # Mark before recursion for same-bundle reference cycles.
            data = real.read_bytes()
            if real.suffix.lower() == ".md":
                data = rewrite(data.decode(), path, dest).encode()
            payload[dest] = data
            if path in record_by_path:
                selected_sources.add(record_by_path[path]["source_id"])
            return dest

        def resolve(raw: str, path: str, dest: str, label: str, original: str) -> str:
            parsed = local_target(raw)
            if parsed is None:
                return original
            relative, anchor = parsed
            target = posixpath.normpath(posixpath.join(posixpath.dirname(path), relative))
            if target == ".agents/skill-sources.json":
                resolved = "provenance.json"
            elif target in PROJECT_CONTEXT:
                suffix = f"#{anchor}" if anchor else ""
                return (f"{label} (look up `{target}{suffix}` in the consuming repository; "
                        "its current project guidance remains authoritative)")
            elif target.startswith(".agents/skills/"):
                parts = target.split("/")
                other_skill = parts[2] if len(parts) > 2 else ""
                if other_skill not in owners:
                    raise ValueError(f"Unknown shared skill resource: {path} -> {target}")
                owner = owners[other_skill]
                if owner != pid:
                    if not (source / target).is_file():
                        raise ValueError(f"Missing cross-bundle resource: {target}")
                    cross_bundles.add(owner)
                    return (f"{label} (shared skill `{owner}:{other_skill}`; select the `{owner}` "
                            "bundle when that task boundary is in scope)")
                resolved = add(target)
            elif target in PORTABLE_REFERENCES or target.startswith(".agents/licenses/"):
                resolved = add(target)
            else:
                raise ValueError(f"Undeclared outward resource: {path} -> {target}")
            replacement = posixpath.relpath(resolved, posixpath.dirname(dest))
            if anchor:
                replacement += "#" + anchor
            return original.replace(raw, replacement, 1)

        def rewrite(text: str, path: str, dest: str) -> str:
            # Reference definitions remain links; no current project-context definition is used.
            def reference(m):
                result = resolve(m[2], path, dest, m[1], m[0])
                if not result.startswith("["):
                    raise ValueError(f"Context lookup must be inline, not a link definition: {path}")
                return result
            return "".join(
                REFERENCE.sub(reference, INLINE.sub(lambda m: resolve(m[2], path, dest, m[1], m[0]), line))
                if prose else line for prose, line in markdown_parts(text)
            )

        for skill in plugin["skills"]:
            for path in sorted((source / ".agents/skills" / skill).rglob("*")):
                if path.is_file():
                    add(path.relative_to(source).as_posix())
        # Preserve every recorded license/NOTICE, not only the source's primary license pointer.
        licensed_sources = set()
        while selected_sources - licensed_sources:
            for sid in sorted(selected_sources - licensed_sources):
                add(source_by_id[sid]["license"])
                for record in manifest["files"]:
                    if record["source_id"] == sid and record["local"].startswith(".agents/licenses/"):
                        add(record["local"])
                licensed_sources.add(sid)
        role_records = []
        if pid == "common":
            for path in sorted((source / "agents").glob("*.toml")):
                data = path.read_bytes()
                role = tomllib.loads(data.decode())
                if set(role) != {"name", "description", "developer_instructions"} or role["name"] != path.stem:
                    raise ValueError(f"Invalid portable role: {path}")
                export = f"exports/codex/agents/{path.name}"
                native = f"agents/{path.stem}.md"
                payload[export] = data
                payload[native] = ("---\nname: " + role["name"] + "\ndescription: "
                                   + json.dumps(role["description"]) + "\n---\n\n"
                                   + role["developer_instructions"].strip() + "\n").encode()
                for target in (export, native):
                    role_records.append({"local": target, "canonical_source": f"source/agents/{path.name}",
                                         "source_sha256": digest(data), "payload_sha256": digest(payload[target]),
                                         "transformation": "Explicit Codex export or Claude native Markdown adapter; no model or permission defaults."})
        filtered_sources = []
        for sid in sorted(selected_sources):
            record = deepcopy(source_by_id[sid])
            record["license"] = copied[record["license"]]
            record["skills"] = [s for s in record["skills"] if s in plugin["skills"]]
            if "dependencies" in record:
                record["dependencies"] = {s: deps for s, deps in record["dependencies"].items() if s in plugin["skills"]}
            filtered_sources.append(record)
        provenance_records = []
        authored_records = []
        extra_resources = []
        for path, dest in sorted(copied.items()):
            common = {"local": dest, "canonical_source": f"source/{path}",
                      "source_sha256": digest((source / path).read_bytes()),
                      "payload_sha256": digest(payload[dest]),
                      "transformation": "Explicit portable link rewriting only; source bytes remain separately recorded."}
            if path in record_by_path:
                record = deepcopy(record_by_path[path])
                record.pop("local")
                record.pop("sha256")
                provenance_records.append({**record, **common})
            elif path in authored_by_path:
                authored_records.append({"name": authored_by_path[path]["name"],
                                         "origin": authored_by_path[path]["origin"], **common})
            else:
                extra_resources.append(common)
        payload["provenance.json"] = json_bytes({
            "schema_version": 1, "bundle": pid, "version": catalog["version"],
            "sources": filtered_sources, "files": provenance_records, "authored_files": authored_records,
            "supporting_resources": extra_resources + role_records,
            "note": "upstream_sha256 is upstream; source_sha256 is the reviewed canonical local source; "
                    "payload_sha256 is the transformed installed file. No hash proves runtime invocation or adherence.",
        })
        description = DESCRIPTIONS.get(pid, f"Reviewed {pid} engineering procedures")
        base = {"name": pid, "version": catalog["version"], "description": description,
                "author": {"name": "Konglabs"}}
        payload["plugin.json"] = json_bytes({"$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json", **base})
        payload[".claude-plugin/plugin.json"] = json_bytes(base)
        payload["DEPENDENCIES.md"] = (
            f"# {pid}: selection and authority\n\n"
            + ("When this workflow reaches their boundary, also select these separately owned bundles: "
               + ", ".join(f"`{name}`" for name in sorted(cross_bundles)) + ".\n\n"
               if cross_bundles else "No other bundle is a declared composition requirement.\n\n")
            + "Bundle selection is explicit; this file does not install or enable dependencies. "
              "The consuming repository's current AGENTS.md, package commands, contracts and safety rules remain "
              "authoritative. Project-context paths in skills are lookups in that repository, not plugin resources.\n"
        ).encode()
        payload["THIRD-PARTY-NOTICES.md"] = (
            f"# Third-party notices: {pid}\n\n"
            + ("Selected imported sources retain their licenses and immutable revisions in `provenance.json`:\n\n"
               + "".join(f"- {s['id']}: {s['repository']} at `{s['revision']}`; license evidence `{s['license']}`.\n"
                         for s in filtered_sources)
               if filtered_sources else "This bundle contains original organization-authored material only.\n")
            + "\nNo blanket license for organization-authored material has been selected. "
              "Public publication requires a separate license review and decision.\n"
        ).encode()
        if pid == "session-guidance":
            payload["hooks/hooks.json"] = json_bytes({"hooks": {"SessionStart": [{"hooks": [{
                "type": "command", "command": 'sh "${CLAUDE_PLUGIN_ROOT}/hooks/session-start.sh"',
            }]}]}})
            payload["hooks/session-start.sh"] = (root / "hooks/session-start.sh").read_bytes()
        payload["artifact-hashes.json"] = json_bytes({"schema_version": 1, "algorithm": "sha256",
            "files": {p: digest(data) for p, data in sorted(payload.items())}})
        for path, data in payload.items():
            output[f"plugins/{pid}/{path}"] = data
    output[".agents/plugins/marketplace.json"] = json_bytes({
        "name": catalog["marketplace"], "interface": {"displayName": "Konglabs Agent Skills"},
        "plugins": [{"name": p["id"], "source": {"source": "local", "path": f"./plugins/{p['id']}"},
                     "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                     "category": "Productivity"} for p in catalog["plugins"]],
    })
    output[".claude-plugin/marketplace.json"] = json_bytes({
        "name": catalog["marketplace"], "owner": {"name": "Konglabs"},
        "plugins": [{"name": p["id"], "source": f"./plugins/{p['id']}",
                     "description": DESCRIPTIONS.get(p["id"], p["id"])} for p in catalog["plugins"]],
    })
    return output


def validate_links(plugin: Path) -> None:
    """Validate every installed Markdown local target inside this exact cached plugin root."""
    for path in plugin.rglob("*.md"):
        text = "".join(line for prose, line in markdown_parts(path.read_text()) if prose)
        for match in list(INLINE.finditer(text)) + list(REFERENCE.finditer(text)):
            parsed = local_target(match[2])
            if parsed is None:
                continue
            target, anchor = parsed
            resolved = (path.parent / target).resolve()
            if not resolved.is_relative_to(plugin.resolve()) or not resolved.is_file():
                raise ValueError(f"Installed Markdown link escapes or is missing: {path} -> {target}")
            if anchor and resolved.suffix.lower() == ".md":
                headings = set()
                counts = {}
                for line in resolved.read_text().splitlines():
                    if not re.match(r"^#{1,6}\s", line):
                        continue
                    slug = re.sub(r"[^\w\- ]", "", re.sub(r"^#+\s+", "", line).lower()).replace(" ", "-")
                    count = counts.get(slug, 0)
                    counts[slug] = count + 1
                    headings.add(slug + (f"-{count}" if count else ""))
                if unquote(anchor) not in headings:
                    raise ValueError(f"Missing installed Markdown anchor: {path} -> {target}#{anchor}")


def validate_output_paths(output: Path) -> None:
    """Reject redirected managed paths before reading, deleting or replacing any output."""
    if ".." in output.parts:
        raise ValueError("Managed output root must not contain parent traversal")
    for relative in ("plugins", ".agents/plugins/marketplace.json", ".claude-plugin/marketplace.json"):
        target = output / relative
        path = target
        while True:
            if path.is_symlink():
                raise ValueError(f"Managed output path must not be a symlink: {path}")
            if path.exists():
                directory = path != target or relative == "plugins"
                if (directory and not path.is_dir()) or (not directory and not path.is_file()):
                    raise ValueError(f"Managed output path has the wrong file type: {path}")
            if path == output:
                break
            path = path.parent
    for path in (output / "plugins").rglob("*"):
        if path.is_symlink():
            raise ValueError(f"Managed output tree must not contain a symlink: {path}")


def build(root: Path, output: Path, check: bool = False) -> None:
    validate_output_paths(output)
    rendered = render(root)
    # Validate the complete staged payload before replacing any existing generated output.
    with tempfile.TemporaryDirectory(prefix="agent-skills-build-") as temp:
        stage = Path(temp)
        for path, data in rendered.items():
            target = stage / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        for plugin in (stage / "plugins").iterdir():
            validate_links(plugin)
        if check:
            actual = {p.relative_to(output).as_posix(): p.read_bytes() for p in (output / "plugins").rglob("*") if p.is_file()}
            for path in (".agents/plugins/marketplace.json", ".claude-plugin/marketplace.json"):
                if (output / path).is_file():
                    actual[path] = (output / path).read_bytes()
            if actual != rendered:
                changed = sorted(set(actual) ^ set(rendered) | {p for p in actual.keys() & rendered.keys() if actual[p] != rendered[p]})
                raise ValueError("Generated artifacts are stale: " + ", ".join(changed[:12]))
            return
        output.mkdir(parents=True, exist_ok=True)
        target = output / "plugins"
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(stage / "plugins", target)
        for path in (".agents/plugins/marketplace.json", ".claude-plugin/marketplace.json"):
            (output / path).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(stage / path, output / path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Compare generated bytes without writing")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    try:
        build(root, root, check=args.check)
    except (ValueError, KeyError, OSError) as error:
        parser.exit(1, f"error: {error}\n")
    print("Generated plugin payloads match reviewed sources." if args.check else "Built closed plugin payloads and host catalogs.")


if __name__ == "__main__":
    main()
