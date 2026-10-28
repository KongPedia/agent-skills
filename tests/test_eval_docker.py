"""Opt-in real-image integration checks: no authentication or model requests."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
from types import SimpleNamespace
import uuid

import pytest

from test_eval_graders import GOOD

IMAGE = os.environ.get("KONGLABS_EVAL_IMAGE")
AGENT_IMAGE = os.environ.get("KONGLABS_EVAL_AGENT_IMAGE")
if not (IMAGE or AGENT_IMAGE):
    pytest.skip("Set KONGLABS_EVAL_IMAGE or KONGLABS_EVAL_AGENT_IMAGE for Docker integration", allow_module_level=True)

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("eval_docker_runner", ROOT / "scripts/run_evals.py")
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)
TASKS = runner.load_tasks(ROOT / "evals/tasks")


def docker_check(workspace, command, mounts=(), *, image):
    name = "konglabs-eval-integration-" + uuid.uuid4().hex
    options = runner.container_options(image, name, workspace, network="none")
    for source, target in mounts:
        options += ["--mount", f"type=bind,src={source},dst={target},readonly"]
    try:
        result = runner.run_process([*options, "--entrypoint", command[0], image, *command[1:]], 60)
        assert result["status"] == "completed", result
        return result
    finally:
        cleanup = runner.run_process(["docker", "rm", "--force", name], 15)
        assert cleanup["status"] == "completed" and cleanup["returncode"] == 0, cleanup


@pytest.mark.skipif(not AGENT_IMAGE, reason="Set KONGLABS_EVAL_AGENT_IMAGE for agent CLI checks")
def test_real_cli_versions_and_help_without_authentication(tmp_path):
    for command, expected in [
        (["codex", "--version"], "codex-cli"),
        (["claude", "--version"], "Claude Code"),
        (["codex", "exec", "--help"], "--json"),
        (["claude", "--help"], "--output-format"),
    ]:
        result = docker_check(tmp_path, command, image=AGENT_IMAGE)
        assert result["returncode"] == 0, result
        assert expected in result["stdout"], result


@pytest.mark.skipif(not IMAGE, reason="Set KONGLABS_EVAL_IMAGE for grader checks")
@pytest.mark.parametrize("task", [task for task in TASKS if task["check"]], ids=lambda task: task["id"])
def test_real_image_external_grading_rejects_baseline_and_accepts_candidate(task, tmp_path):
    workspace = tmp_path / "workspace"
    runner.prepare_fixture(task, workspace)
    checks = tmp_path / "checks"
    checks.mkdir()
    shutil.copy(task["check"], checks / "check.py")
    shutil.copy(ROOT / "evals/drive_check.py", checks / "drive_check.py")
    command = ["python3", "/checks/drive_check.py", "/checks/check.py", "/workspace",
               json.dumps(task["expected_checks"])]
    baseline = docker_check(workspace, command, [(checks, "/checks")], image=IMAGE)
    assert runner.parse_check(baseline)["status"] == "fail", baseline
    path, content = GOOD[task["id"]]
    (workspace / path).write_text(content)
    candidate = docker_check(workspace, command, [(checks, "/checks")], image=IMAGE)
    assert runner.parse_check(candidate)["status"] == "pass", candidate


@pytest.mark.skipif(not AGENT_IMAGE, reason="Set KONGLABS_EVAL_AGENT_IMAGE for agent CLI checks")
def test_real_production_trial_bootstraps_home_and_installs_native_payload(tmp_path, monkeypatch):
    task = runner.load_tasks(ROOT / "evals/tasks", ["python-tdd"])[0]
    initial = tmp_path / "initial"
    runner.prepare_fixture(task, initial)
    provider = tmp_path / "provider"
    metadata = runner.prepare_provider(ROOT, provider, task["bundles"])
    output = tmp_path / "artifacts"
    output.mkdir()
    args = SimpleNamespace(output=output, engine="codex", model="not-used", image=AGENT_IMAGE, timeout=180)
    # Version-only replacement is explicit: this integration test cannot issue a model request.
    monkeypatch.setattr(runner, "agent_command", lambda *args: ["codex", "--version"])
    monkeypatch.setenv(runner.CREDENTIALS["codex"], "integration-placeholder-not-a-credential")
    process = runner.run_process
    observed = []

    def observe(argv, timeout, env=None):
        result = process(argv, timeout, env)
        if argv[:2] == ["docker", "exec"] and "--env" in argv and argv[-2:] == ["codex", "--version"]:
            name = argv[4]
            probe = process(["docker", "exec", name, "python3", "-c",
                             "from pathlib import Path; import hashlib,json; "
                             "home=Path('/home/eval/.codex'); "
                             "print(json.dumps({'home':home.is_dir(), 'skills':"
                             "{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in home.rglob('SKILL.md')}}))"], 20)
            assert probe["returncode"] == 0, probe
            observed.append(json.loads(probe["stdout"]))
        return result

    monkeypatch.setattr(runner, "run_process", observe)
    row = runner.run_trial(task, initial, provider, metadata, args, "candidate", 1)
    assert row["status"] == "agent_error", row  # --version intentionally has no completed JSONL turn.
    assert row["outcome"]["status"] == "unknown"
    directory = output / "python-tdd-1-candidate"
    for step in ("home", "version", "marketplace", "install-common", "install-python", "installed-skills", "cleanup"):
        assert (directory / f"{step}.stdout").exists()
        assert (directory / f"{step}.stderr").read_text() == "", (step, (directory / f"{step}.stderr").read_text())
    assert observed and observed[0]["home"]
    installed = set(observed[0]["skills"].values())
    assert set(row["installed_skill_paths"]) == set(observed[0]["skills"])
    assert json.loads((directory / "installed-skills.stdout").read_text()) == observed[0]["skills"]
    import hashlib
    for bundle, skill in [("common", "test-driven-development"), ("python", "python-testing-patterns")]:
        expected = hashlib.sha256((provider / "plugins" / bundle / "skills" / skill / "SKILL.md").read_bytes()).hexdigest()
        assert expected in installed, (bundle, observed)


@pytest.mark.skipif(not IMAGE, reason="Set KONGLABS_EVAL_IMAGE for grader checks")
def test_grader_image_only_contains_nonroot_python_runtime(tmp_path):
    result = docker_check(tmp_path, ["python3", "-c",
        "import os, shutil; import fastapi, httpx; "
        "assert os.getuid() != 0; "
        "assert fastapi.__version__ == '0.162.0'; "
        "assert httpx.__version__ == '0.28.1'; "
        "assert not any(shutil.which(name) for name in ('node', 'npm', 'git', 'codex', 'claude'))"
    ], image=IMAGE)
    assert result["returncode"] == 0, result
