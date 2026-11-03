#!/usr/bin/env python3
"""Prepare closed plugins from plugin-owned canonical files; never touch agent host configuration."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import posixpath
import re
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
PORTABLE_REFERENCES = {
    f"references/{name}.md"
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


def plugin_path(relative: str, ids: set[str]) -> tuple[str, str]:
    if (not isinstance(relative, str) or relative.startswith("/") or "\\" in relative
            or posixpath.normpath(relative) != relative):
        raise ValueError(f"Provenance source path is not canonical: {relative}")
    parts = relative.split("/")
    if len(parts) < 3 or parts[0] != "plugins" or parts[1] not in ids:
        raise ValueError(f"Canonical source must belong to a declared plugin: {relative}")
    return parts[1], "/".join(parts[2:])


def canonical_records(manifest):
    authored = manifest["authored_skills"] + manifest.get("authored_resources", [])
    return manifest["files"] + [record for entry in authored for record in entry["files"]]


def load_source(root: Path):
    for path in (root, root / "plugins", root / "provenance", root / "provenance/skill-sources.json", root / "catalog.json"):
        if path.is_symlink():
            raise ValueError(f"Canonical source root/input must not be a symlink: {path}")
    if (root / "source").exists() or (root / "hooks").exists():
        raise ValueError("Legacy source/ or hooks/ authoring trees must be migrated to their plugin owners")
    catalog = json.loads((root / "catalog.json").read_text())
    if catalog.get("schema_version") != 1 or not IDENTIFIER.fullmatch(catalog.get("marketplace", "")):
        raise ValueError("Invalid catalog schema or marketplace identity")
    if not SEMVER.fullmatch(catalog.get("version", "")):
        raise ValueError("Catalog version must be an explicit semantic version")
    plugins = catalog.get("plugins", [])
    ids = [p["id"] for p in plugins]
    if len(ids) != len(set(ids)) or any(not IDENTIFIER.fullmatch(p) for p in ids):
        raise ValueError("Invalid or duplicate plugin identity")
    ids = set(ids)
    owners = {}
    for plugin in plugins:
        for required in plugin.get("requires", []):
            if required not in ids or required == plugin["id"]:
                raise ValueError(f"Invalid bundle dependency: {required}")
        for skill in plugin["skills"]:
            if not IDENTIFIER.fullmatch(skill) or skill in owners:
                raise ValueError(f"Invalid or duplicate skill owner: {skill}")
            owners[skill] = plugin["id"]
    if {p.name for p in (root / "plugins").iterdir() if p.is_dir()} != ids:
        raise ValueError("Plugin directories differ from declared catalog identities")
    for path in (root / "plugins").rglob("*"):
        if path.is_symlink():
            raise ValueError(f"Canonical/plugin files must not be symlinks: {path}")
    actual = {(plugin["id"], p.name) for plugin in plugins
              for p in (root / "plugins" / plugin["id"] / "skills").glob("*") if p.is_dir()}
    expected = {(owner, name) for name, owner in owners.items()}
    if actual != expected:
        raise ValueError(f"Skill ownership differs from canonical source: {expected ^ actual}")
    manifest = json.loads((root / "provenance/skill-sources.json").read_text())
    if manifest.get("version") != 2:
        raise ValueError("Canonical provenance must use repository-relative version 2 paths")
    records = canonical_records(manifest)
    recorded = set()
    shared = {}
    for record in records:
        relative = record["local"]
        pid, target = plugin_path(relative, ids)
        if relative in recorded:
            raise ValueError(f"Duplicate canonical provenance source: {relative}")
        recorded.add(relative)
        if target.startswith("skills/"):
            if len(target.split("/")) < 3 or owners.get(target.split("/")[1]) != pid:
                raise ValueError(f"Canonical skill has the wrong owner: {relative}")
        elif target in PORTABLE_REFERENCES or target.startswith("licenses/"):
            if target in shared:
                raise ValueError(f"Duplicate canonical resource owner: {target}")
            shared[target] = relative
        elif pid == "common" and re.fullmatch(r"exports/codex/agents/[a-z0-9-]+\.toml", target):
            pass
        elif relative != "plugins/session-guidance/hooks/session-start.sh":
            raise ValueError(f"Resource is not declared canonical: {relative}")
        path = root / relative
        if not path.resolve().is_relative_to(root.resolve()) or not path.is_file():
            raise ValueError(f"Missing or escaping provenance source: {relative}")
        if digest(path.read_bytes()) != record["sha256"]:
            raise ValueError(f"Source hash mismatch: {relative}; review and record local adaptation first")
    for plugin in plugins:
        for path in (root / "plugins" / plugin["id"] / "skills").rglob("*"):
            if path.is_file() and path.relative_to(root).as_posix() not in recorded:
                raise ValueError(f"Skill resource lacks source provenance: {path.relative_to(root)}")
    hook = "plugins/session-guidance/hooks/session-start.sh"
    if "session-guidance" in ids and hook not in recorded:
        raise ValueError("Optional hook source lacks reviewed canonical provenance")
    source_ids = [entry["id"] for entry in manifest["sources"]]
    if len(source_ids) != len(set(source_ids)):
        raise ValueError("Duplicate imported source identity")
    for source in manifest["sources"]:
        if source["license"] not in recorded:
            raise ValueError(f"Missing canonical license evidence: {source['id']}")
    if any(record["source_id"] not in source_ids for record in manifest["files"]):
        raise ValueError("Imported file has an unknown source identity")
    for name, owner in owners.items():
        entry = (root / "plugins" / owner / "skills" / name / "SKILL.md").read_text()
        if not re.search(rf"^name:\s*{re.escape(name)}\s*$", entry, re.MULTILINE):
            raise ValueError(f"Skill frontmatter name differs from its canonical identity: {name}")
    return catalog, owners, manifest


def render(root: Path) -> dict[str, bytes]:
    catalog, owners, manifest = load_source(root)
    ids = {entry["id"] for entry in catalog["plugins"]}
    records = {record["local"]: record for record in canonical_records(manifest)}
    resources = {plugin_path(path, ids)[1]: path for path in records
                 if plugin_path(path, ids)[1] in PORTABLE_REFERENCES
                 or plugin_path(path, ids)[1].startswith("licenses/")}
    source_by_id = {record["id"]: record for record in manifest["sources"]}
    record_by_path = {record["local"]: record for record in manifest["files"]}
    authored = manifest["authored_skills"] + manifest.get("authored_resources", [])
    authored_by_path = {f["local"]: entry for entry in authored for f in entry["files"]}
    output: dict[str, bytes] = {}
    for plugin in catalog["plugins"]:
        pid = plugin["id"]
        payload: dict[str, bytes] = {}
        copied: dict[str, str] = {}
        cross_bundles = set(plugin.get("requires", []))
        selected_sources: set[str] = set()

        def add(path: str) -> str:
            owner, dest = plugin_path(path, ids)
            if path in copied:
                return copied[path]
            if path not in records or (owner != pid and dest not in resources):
                raise ValueError(f"Resource is not declared portable: {path}")
            copied[path] = dest
            data = (root / path).read_bytes()
            if path.endswith(".md"):
                text = data.decode()
                rewritten = rewrite(text, path, dest)
                # Only destination copies are transformed; canonical input bytes never are.
                if owner != pid:
                    data = rewritten.encode()
                for prose, line in markdown_parts(data.decode()):
                    if prose:
                        for match in re.finditer(r"shared skill `([a-z0-9-]+):([a-z0-9-]+)`", line):
                            bundle, skill = match.groups()
                            if owners.get(skill) != bundle:
                                raise ValueError(f"Unknown shared skill identity: {bundle}:{skill}")
                            if bundle != pid:
                                cross_bundles.add(bundle)
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
            try:
                owner, key = plugin_path(target, ids)
            except ValueError as error:
                raise ValueError(f"Undeclared outward resource: {path} -> {target}") from error
            if key.startswith("skills/"):
                parts = key.split("/")
                other_skill = parts[1] if len(parts) > 1 else ""
                if owners.get(other_skill) != owner:
                    raise ValueError(f"Unknown shared skill resource: {path} -> {target}")
                if target not in records:
                    raise ValueError(f"Missing or escaping resource: {path} -> {target}")
                if owner != pid:
                    cross_bundles.add(owner)
                    return (f"{label} (shared skill `{owner}:{other_skill}`; select the `{owner}` "
                            "bundle when that task boundary is in scope)")
                resolved = add(target)
            elif key in resources:
                resolved = add(resources[key])
            elif key == "provenance.json":
                resolved = key
            else:
                raise ValueError(f"Undeclared outward resource: {path} -> {target}")
            replacement = posixpath.relpath(resolved, posixpath.dirname(dest))
            if anchor:
                replacement += "#" + anchor
            return original.replace(raw, replacement, 1)

        def rewrite(text: str, path: str, dest: str) -> str:
            def reference(match):
                result = resolve(match[2], path, dest, match[1], match[0])
                if not result.startswith("["):
                    raise ValueError(f"Context lookup must be inline, not a link definition: {path}")
                return result
            return "".join(
                REFERENCE.sub(reference, INLINE.sub(lambda match: resolve(match[2], path, dest, match[1], match[0]), line))
                if prose else line for prose, line in markdown_parts(text)
            )

        for path in sorted(records):
            if plugin_path(path, ids)[0] == pid:
                add(path)
        licensed_sources = set()
        while selected_sources - licensed_sources:
            for sid in sorted(selected_sources - licensed_sources):
                add(source_by_id[sid]["license"])
                for path, record in record_by_path.items():
                    if record["source_id"] == sid and plugin_path(path, ids)[1].startswith("licenses/"):
                        add(path)
                licensed_sources.add(sid)
        role_records = []
        if pid == "common":
            for path in sorted(records):
                owner, key = plugin_path(path, ids)
                if owner != pid or not key.startswith("exports/codex/agents/"):
                    continue
                data = (root / path).read_bytes()
                role = tomllib.loads(data.decode())
                stem = Path(path).stem
                if set(role) != {"name", "description", "developer_instructions"} or role["name"] != stem:
                    raise ValueError(f"Invalid portable role: {path}")
                native = f"agents/{stem}.md"
                payload[native] = ("---\nname: " + role["name"] + "\ndescription: "
                                   + json.dumps(role["description"]) + "\n---\n\n"
                                   + role["developer_instructions"].strip() + "\n").encode()
                role_records.append({"local": native, "canonical_source": path,
                                     "source_sha256": digest(data), "payload_sha256": digest(payload[native]),
                                     "transformation": "Claude native Markdown adapter from canonical role TOML; no model or permission defaults."})
        filtered_sources = []
        for sid in sorted(selected_sources):
            record = deepcopy(source_by_id[sid])
            record["license"] = copied[record["license"]]
            record["skills"] = [skill for skill in record["skills"] if skill in plugin["skills"]]
            if "dependencies" in record:
                record["dependencies"] = {skill: deps for skill, deps in record["dependencies"].items() if skill in plugin["skills"]}
            filtered_sources.append(record)
        provenance_records = []
        authored_records = []
        extra_resources = []
        for path, dest in sorted(copied.items()):
            common = {"local": dest, "canonical_source": path,
                      "source_sha256": digest((root / path).read_bytes()),
                      "payload_sha256": digest(payload[dest]),
                      "transformation": ("Canonical plugin-owned bytes; no rewriting."
                                         if plugin_path(path, ids)[0] == pid else
                                         "Generated destination copy from its registered canonical owner; portable link rewriting only.")}
            if path in record_by_path:
                record = deepcopy(record_by_path[path])
                record.pop("local")
                record.pop("sha256")
                provenance_records.append({**record, **common})
            elif dest.startswith("skills/"):
                entry = authored_by_path[path]
                authored_records.append({"name": entry["name"], "origin": entry["origin"], **common})
            else:
                entry = authored_by_path[path]
                extra_resources.append({"origin": entry["origin"], **common})
        payload["provenance.json"] = json_bytes({
            "schema_version": 1, "bundle": pid, "version": catalog["version"],
            "sources": filtered_sources, "files": provenance_records, "authored_files": authored_records,
            "supporting_resources": extra_resources + role_records,
            "note": "upstream_sha256 is upstream; source_sha256 is the reviewed canonical local source; "
                    "payload_sha256 is the installed file. No hash proves runtime invocation or adherence.",
        })
        description = DESCRIPTIONS.get(pid, f"Reviewed {pid} engineering procedures")
        base = {"name": pid, "version": catalog["version"], "description": description,
                "author": {"name": "KongLabs"}}
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
               + "".join(f"- {source['id']}: {source['repository']} at `{source['revision']}`; license evidence `{source['license']}`.\n"
                         for source in filtered_sources)
               if filtered_sources else "This bundle contains original organization-authored material only.\n")
            + "\nNo blanket license for organization-authored material has been selected. "
              "Public publication requires a separate license review and decision.\n"
        ).encode()
        if pid == "session-guidance":
            payload["hooks/hooks.json"] = json_bytes({"hooks": {"SessionStart": [{"hooks": [{
                "type": "command", "command": 'sh "${CLAUDE_PLUGIN_ROOT}/hooks/session-start.sh"',
            }]}]}})
        payload["artifact-hashes.json"] = json_bytes({"schema_version": 1, "algorithm": "sha256",
            "files": {path: digest(data) for path, data in sorted(payload.items())}})
        for path, data in payload.items():
            output[f"plugins/{pid}/{path}"] = data
    output[".agents/plugins/marketplace.json"] = json_bytes({
        "name": catalog["marketplace"], "interface": {"displayName": "KongLabs Agent Skills"},
        "plugins": [{"name": plugin["id"], "source": {"source": "local", "path": f"./plugins/{plugin['id']}"},
                     "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                     "category": "Productivity"} for plugin in catalog["plugins"]],
    })
    output[".claude-plugin/marketplace.json"] = json_bytes({
        "name": catalog["marketplace"], "owner": {"name": "KongLabs"},
        "plugins": [{"name": plugin["id"], "source": f"./plugins/{plugin['id']}",
                     "description": DESCRIPTIONS.get(plugin["id"], plugin["id"])} for plugin in catalog["plugins"]],
    })
    unknown = sorted(path.relative_to(root).as_posix() for path in (root / "plugins").rglob("*")
                     if path.is_file() and path.relative_to(root).as_posix() not in output)
    if unknown:
        raise ValueError("Unknown plugin files lack canonical or generated ownership: " + ", ".join(unknown[:12]))
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


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(data)
        temporary.chmod(0o644)
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def build(root: Path, output: Path, check: bool = False) -> None:
    validate_output_paths(output)
    if root.is_symlink():
        raise ValueError(f"Canonical source root/input must not be a symlink: {root}")
    same_root = root.resolve() == output.resolve()
    if not same_root and (root.resolve().is_relative_to(output.resolve()) or output.resolve().is_relative_to(root.resolve())):
        raise ValueError("Source/output overlap is not allowed except explicit in-place preparation")
    rendered = render(root)
    manifest = json.loads((root / "provenance/skill-sources.json").read_text())
    canonical = {record["local"] for record in canonical_records(manifest)}
    actual = {path.relative_to(output).as_posix(): path.read_bytes()
              for path in (output / "plugins").rglob("*") if path.is_file()}
    for relative in (".agents/plugins/marketplace.json", ".claude-plugin/marketplace.json"):
        if (output / relative).is_file():
            actual[relative] = (output / relative).read_bytes()
    unknown = sorted(set(actual) - set(rendered))
    if unknown:
        raise ValueError("Unknown plugin/output files are not owned generated paths: " + ", ".join(unknown[:12]))
    for relative, data in rendered.items():
        path = output / relative
        if path.exists() and not path.is_file():
            raise ValueError(f"Managed output path has the wrong file type: {path}")
        if same_root and relative in canonical and actual.get(relative) != data:
            raise ValueError(f"Preparation would change canonical source: {relative}")
    with tempfile.TemporaryDirectory(prefix="agent-skills-build-") as temp:
        stage = Path(temp)
        for relative, data in rendered.items():
            path = stage / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        for plugin in (stage / "plugins").iterdir():
            validate_links(plugin)
        if check:
            if actual != rendered:
                changed = sorted(set(actual) ^ set(rendered) | {path for path in actual.keys() & rendered.keys() if actual[path] != rendered[path]})
                raise ValueError("Generated artifacts are stale: " + ", ".join(changed[:12]))
            return
        for relative, data in rendered.items():
            if same_root and relative in canonical:
                continue
            if actual.get(relative) != data:
                atomic_write(output / relative, data)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Compare generated bytes without writing")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    try:
        build(root, root, check=args.check)
    except (ValueError, KeyError, OSError) as error:
        parser.exit(1, f"error: {error}\n")
    print("Plugin payloads match reviewed canonical inputs." if args.check
          else "Prepared plugin metadata and resources without rewriting canonical inputs.")


if __name__ == "__main__":
    main()
