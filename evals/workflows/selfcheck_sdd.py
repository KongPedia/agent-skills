"""Validate SDD behavioral oracles offline; repairs are never mounted for agents.

Run: uv run --locked python evals/workflows/selfcheck_sdd.py
This does NOT establish SDD process quality, which requires independent trace review.
"""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
REFERENCE = {
    "provider.py": '''def list_tasks(records, cursor=0, limit=2):
    if type(cursor) is not int or cursor < 0:
        raise ValueError("nonnegative cursor required")
    if type(limit) is not int or not 1 <= limit <= 50:
        raise ValueError("limit 1..50 required")
    ordered = sorted(records, key=lambda task: task["id"])
    items = [dict(task) for task in ordered[cursor:cursor + limit]]
    following = cursor + len(items)
    return {"items": items, "next_cursor": following if following < len(ordered) else None}
''',
    "web.py": '''from provider import list_tasks

def render_tasks(records, limit=2):
    return [task["title"] for task in list_tasks(records, limit=limit)["items"]]
''',
    "export.py": '''from provider import list_tasks

def export_ids(records):
    result, cursor = [], 0
    while True:
        page = list_tasks(records, cursor=cursor)
        result.extend(task["id"] for task in page["items"])
        cursor = page["next_cursor"]
        if cursor is None:
            return result
''',
    "labels.py": '''def display_label(value):
    return " ".join(value.replace("_", " ").split()).title()
''',
}


def run_check(manifest, workspace):
    result = subprocess.run(
        [sys.executable, "-B", str((ROOT / "tasks" / manifest["check"]).resolve()), str(workspace)],
        capture_output=True, text=True, timeout=10,
    )
    markers = [line[len("EVAL_RESULT: "):] for line in result.stdout.splitlines() if line.startswith("EVAL_RESULT: ")]
    assert len(markers) == 1, result.stderr or result.stdout
    report = json.loads(markers[0])
    assert set(report["checks"]) == set(manifest["expected_checks"]), report
    assert all(type(value) is bool for value in report["checks"].values()), report
    assert result.returncode == (0 if report["status"] == "pass" else 1), report
    return report


def main():
    catalog = json.loads((ROOT.parents[1] / "catalog.json").read_text())
    providers = {plugin["id"]: plugin for plugin in catalog["plugins"]}
    for path in sorted((ROOT / "tasks").glob("sdd-*.json")):
        manifest = json.loads(path.read_text())
        for bundle in manifest["bundles"]:
            assert bundle in providers, bundle
            assert set(providers[bundle]["requires"]) <= set(manifest["bundles"])
        for skill in manifest["required_skills"]:
            bundle, name = skill.split(":")
            assert bundle in manifest["bundles"] and name in providers[bundle]["skills"], skill
        fixture = (path.parent / manifest["fixture"]).resolve()
        with tempfile.TemporaryDirectory(prefix="sdd-oracle-") as temporary:
            workspace = Path(temporary) / "workspace"
            shutil.copytree(fixture, workspace)
            baseline_sources = {p.name: p.read_text() for p in workspace.glob("*.py")}
            assert run_check(manifest, workspace)["status"] == "fail", manifest["id"]
            for name in baseline_sources:
                (workspace / name).write_text(REFERENCE[name])
            assert run_check(manifest, workspace)["status"] == "pass", manifest["id"]
            for name, original in baseline_sources.items():
                (workspace / name).write_text(original)
                rejected = run_check(manifest, workspace)
                assert rejected["status"] == "fail", (manifest["id"], name, rejected)
                (workspace / name).write_text(REFERENCE[name])
                (workspace / name).write_text("invalid Python syntax !!!")
                invalid = run_check(manifest, workspace)
                assert invalid["status"] == "fail" and not any(invalid["checks"].values()), (name, invalid)
                (workspace / name).write_text(REFERENCE[name])
            print(f'{manifest["id"]}: baseline/syntax/per-module regressions rejected; reference passes {len(manifest["expected_checks"])} checks')
    print("Two SDD oracles validated; no model calls; process quality remains independently reviewed.")


if __name__ == "__main__":
    main()
