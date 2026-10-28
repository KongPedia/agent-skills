"""Frozen follow-up dataset checks; never invoke an agent or authenticated model."""
import importlib.util
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("followup_runner", ROOT / "scripts/run_evals.py")
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


def test_followup_tasks_have_complete_provider_dependencies(tmp_path):
    for task in runner.load_tasks(ROOT / "evals/followup/tasks"):
        provider = runner.prepare_provider(ROOT, tmp_path / task["id"], task["bundles"])
        runner.validate_skills(task, provider)


def test_followup_oracles_reject_broken_candidates_and_accept_reference_repairs():
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    result = subprocess.run([sys.executable, str(ROOT / "evals/followup/selfcheck.py")],
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
