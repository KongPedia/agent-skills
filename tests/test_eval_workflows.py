"""Workflow dataset regressions; no authenticated agents or model calls."""
import importlib.util
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("workflow_runner", ROOT / "scripts/run_evals.py")
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


def test_workflow_tasks_have_complete_provider_dependencies(tmp_path):
    for task in runner.load_tasks(ROOT / "evals/workflows/tasks"):
        provider = runner.prepare_provider(ROOT, tmp_path / task["id"], task["bundles"])
        runner.validate_skills(task, provider)


@pytest.mark.parametrize("axis", ["sdd", "source", "ddd"])
def test_workflow_oracles_reject_broken_answers_and_accept_supported_repairs(axis):
    result = subprocess.run([sys.executable, str(ROOT / f"evals/workflows/selfcheck_{axis}.py")],
                            capture_output=True, text=True, timeout=45)
    assert result.returncode == 0, result.stdout + result.stderr
