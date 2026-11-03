"""Safety regressions for the plugin-owned design-system CLI."""
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest


SKILL = Path(__file__).resolve().parents[1] / "plugins/react-ui/skills/ui-ux-pro-max"


@pytest.fixture
def workspace(tmp_path):
    skill = shutil.copytree(SKILL, tmp_path / "skill")
    project = tmp_path / "project"
    project.mkdir()
    return skill, project


def invoke(workspace, *args, query="SaaS"):
    skill, project = workspace
    return subprocess.run(
        [sys.executable, "-B", str(skill / "scripts/search.py"), query,
         "--design-system", "--json", "-p", "Example", "--output-dir", str(project), *args],
        cwd=project, capture_output=True, text=True, timeout=15,
    )


def snapshot(root):
    return {
        str(path.relative_to(root)): ("link", str(path.readlink())) if path.is_symlink()
        else ("dir",) if path.is_dir() else ("file", path.read_bytes())
        for path in root.rglob("*")
    }


@pytest.mark.parametrize("filename,extra", [
    ("products.csv", ()), ("colors.csv", ()), ("typography.csv", ()),
    ("styles.csv", ()), ("landing.csv", ()), ("ui-reasoning.csv", ()),
    ("motion.csv", ("--motion", "5")),
    ("ux-guidelines.csv", ("--page", "dashboard")),
])
@pytest.mark.parametrize("damage", ["missing", "invalid-utf8", "unreadable-directory"])
def test_needed_data_failure_is_not_a_recommendation_or_partial_write(workspace, filename, extra, damage):
    skill, project = workspace
    resource = skill / "data" / filename
    resource.unlink()
    if damage == "invalid-utf8":
        resource.write_bytes(b"\xff\xfeinvalid")
    elif damage == "unreadable-directory":
        resource.mkdir()
    before = snapshot(project)
    result = invoke(workspace, "--persist", *extra)
    assert result.returncode != 0, result.stdout
    assert not result.stdout, "Failed data must not produce recommendations"
    assert filename in result.stderr
    assert "error:" in result.stderr.lower()
    assert "Traceback" not in result.stderr
    assert snapshot(project) == before, "Failed generation must not persist even a MASTER or directories"


@pytest.mark.parametrize("component", ["design-system", "example", "pages", "MASTER.md", "dashboard.md"])
@pytest.mark.parametrize("force", [False, True])
def test_persistence_rejects_child_symlinks_before_writes(workspace, component, force):
    skill, project = workspace
    outside = project.parent / "outside"
    outside.mkdir()
    design_dir = project / "design-system" / "example"
    paths = {
        "design-system": project / "design-system",
        "example": design_dir,
        "pages": design_dir / "pages",
        "MASTER.md": design_dir / "MASTER.md",
        "dashboard.md": design_dir / "pages/dashboard.md",
    }
    link = paths[component]
    link.parent.mkdir(parents=True, exist_ok=True)
    if component.endswith(".md"):
        target = outside / "existing.md"
        target.write_text("Keep outside content", encoding="utf-8")
    else:
        target = outside
    link.symlink_to(target, target_is_directory=not component.endswith(".md"))
    before_project, before_outside = snapshot(project), snapshot(outside)
    result = invoke(workspace, "--persist", "--page", "dashboard", *(["--force"] if force else []))
    assert result.returncode != 0, result.stdout
    assert not result.stdout
    assert "symlink" in result.stderr.lower()
    assert snapshot(project) == before_project
    assert snapshot(outside) == before_outside


def test_successful_recommendation_is_readonly_and_optional_motion_is_not_required(workspace):
    skill, project = workspace
    (skill / "data/motion.csv").unlink()
    before_skill, before_project = snapshot(skill), snapshot(project)
    result = invoke(workspace)
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["design_system"]["reasoning_default"] is False
    assert report["design_system"]["colors"]
    assert report["persistence"] is None
    assert snapshot(skill) == before_skill
    assert snapshot(project) == before_project


def test_persistence_preserves_existing_master_and_page_unless_forced(workspace):
    _, project = workspace
    result = invoke(workspace, "--persist", "--page", "dashboard")
    assert result.returncode == 0, result.stderr
    master = project / "design-system/example/MASTER.md"
    page = master.parent / "pages/dashboard.md"
    master.write_text("Existing decisions", encoding="utf-8")
    page.write_text("Existing page", encoding="utf-8")
    result = invoke(workspace, "--persist", "--page", "dashboard")
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["persistence"]["status"] == "skipped_exists"
    assert master.read_text() == "Existing decisions"
    assert page.read_text() == "Existing page"
    result = invoke(workspace, "--persist", "--page", "dashboard", "--force")
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["persistence"]["status"] == "success"
    assert master.read_text() != "Existing decisions"
    assert page.read_text() != "Existing page"


def test_explicit_output_root_may_be_a_symlink(workspace):
    skill, project = workspace
    selected_root = project.parent / "selected-root"
    selected_root.symlink_to(project, target_is_directory=True)
    result = invoke((skill, selected_root), "--persist")
    assert result.returncode == 0, result.stderr
    assert (project / "design-system/example/MASTER.md").is_file()


def test_legitimate_no_match_remains_disclosed_and_readonly(workspace):
    skill, project = workspace
    before_skill, before_project = snapshot(skill), snapshot(project)
    result = invoke(workspace, query="zzzznotacatalogentryqvx")
    assert result.returncode == 0, result.stderr
    design = json.loads(result.stdout)["design_system"]
    assert design["reasoning_default"] is True
    assert design["source_identities"]["product"] is None
    assert design["source_identities"]["reasoning"] is None
    assert snapshot(skill) == before_skill
    assert snapshot(project) == before_project
