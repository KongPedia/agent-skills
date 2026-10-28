"""Regression coverage for outer grading completion and result protocol."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

import pytest

BASE = Path(__file__).resolve().parents[1] / "evals"
SPEC = importlib.util.spec_from_file_location("drive_check", BASE / "drive_check.py")
driver = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(driver)


def checker(tmp_path, body):
    path = tmp_path / "check.py"
    path.write_text(body)
    return path


def payload(status="pass", checks=None):
    return 'print("EVAL_RESULT: " + ' + repr(json.dumps({
        "status": status, "checks": {"criterion": True} if checks is None else checks})) + ', flush=True)\n'


def test_normal_good_and_bad_results(tmp_path):
    check = checker(tmp_path, payload() + "raise SystemExit(0)\n")
    assert driver.run_check(check, tmp_path, ["criterion"])["status"] == "pass"
    check.write_text(payload("fail", {"criterion": False}) + "raise SystemExit(1)\n")
    assert driver.run_check(check, tmp_path, ["criterion"])["status"] == "fail"


def test_imported_module_cannot_pass_by_printing_then_exiting(tmp_path):
    (tmp_path / "generated.py").write_text("import os\n" + payload() + "os._exit(0)\n")
    check = checker(tmp_path, "import sys\nsys.path.insert(0, sys.argv[1])\nimport generated\n" + payload())
    assert driver.run_check(check, tmp_path, ["criterion"])["status"] == "fail"


@pytest.mark.parametrize("body", [
    payload(checks={}),
    payload() + payload(),
    'print("EVAL_RESULT: not-json")\n',
    payload() + 'print("EVAL_COMPLETE: forged")\n',
    payload() + 'raise SystemExit(1)\n',
])
def test_incomplete_duplicate_malformed_or_inconsistent_result_never_passes(tmp_path, body):
    result = driver.run_check(checker(tmp_path, body), tmp_path, ["criterion"])
    assert result["status"] == "unknown"


def test_missing_completion_fails_even_with_exit_zero(tmp_path):
    check = checker(tmp_path, "import os\nos._exit(0)\n")
    assert driver.run_check(check, tmp_path, ["criterion"])["status"] == "fail"


def test_timeout_cleans_up_process_group(tmp_path):
    sentinel = tmp_path / "survived"
    child = f"import time; from pathlib import Path; time.sleep(0.5); Path({str(sentinel)!r}).touch()"
    body = f"import subprocess,sys,time\nsubprocess.Popen([sys.executable, '-c', {child!r}])\ntime.sleep(30)\n"
    started = time.monotonic()
    assert driver.run_check(checker(tmp_path, body), tmp_path, ["criterion"], timeout=0.15)["status"] == "fail"
    assert time.monotonic() - started < 3
    time.sleep(0.6)
    assert not sentinel.exists()


def test_real_points_baseline_and_good_candidate(tmp_path):
    task = json.loads((BASE / "tasks/python-tdd.json").read_text())
    shutil.copytree(BASE / "tasks" / task["fixture"], tmp_path, dirs_exist_ok=True)
    check = (BASE / "tasks" / task["check"]).resolve()
    expected = ["normal", "zero", "full_balance", "reject_3_4", "reject_5_-1", "reject_-1_0", "reject_-2_-3"]
    assert driver.run_check(check, tmp_path, expected)["status"] == "fail"
    (tmp_path / "points.py").write_text('def deduct(balance, amount):\n    if balance < 0 or amount < 0 or amount > balance:\n        raise ValueError()\n    return balance - amount\n')
    assert driver.run_check(check, tmp_path, expected)["status"] == "pass"


def test_cli_emits_one_outer_result(tmp_path):
    check = checker(tmp_path, payload() + "raise SystemExit(0)\n")
    process = subprocess.run([sys.executable, str(BASE / "drive_check.py"), str(check), str(tmp_path),
                              '["criterion"]'], capture_output=True, text=True, timeout=5)
    assert process.returncode == 0
    assert process.stdout.count("EVAL_RESULT:") == 1
    assert json.loads(process.stdout.removeprefix("EVAL_RESULT: "))["status"] == "pass"


def test_manifest_expected_checks_match_good_candidates(tmp_path):
    from test_eval_graders import GOOD, TASKS

    for task in TASKS:
        if not task["check"]:
            assert task["expected_checks"] == []
            continue
        if task["runtime_modules"]:
            continue  # API candidates are covered in the dependency-enabled parameterized test below.
        workspace = tmp_path / task["id"]
        shutil.copytree(BASE / "tasks" / task["fixture"], workspace)
        path, source = GOOD[task["id"]]
        (workspace / path).write_text(source)
        result = driver.run_check((BASE / "tasks" / task["check"]).resolve(), workspace,
                                  task["expected_checks"])
        assert result["status"] == "pass", result


@pytest.mark.parametrize("task_id", ["api-boundary", "fastapi-lifecycle"])
def test_api_manifest_expected_checks_match_good_candidates(task_id, tmp_path):
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    from test_eval_graders import GOOD, TASKS

    task = next(item for item in TASKS if item["id"] == task_id)
    path, source = GOOD[task_id]
    (tmp_path / path).write_text(source)
    result = driver.run_check((BASE / "tasks" / task["check"]).resolve(), tmp_path,
                              task["expected_checks"])
    assert result["status"] == "pass", result


def test_cli_preserves_bounded_child_diagnostics_on_stderr(tmp_path):
    check = checker(tmp_path, 'import sys,os\nprint("STDOUT_SENTINEL", flush=True)\n'
                    'print("STDERR_SENTINEL", file=sys.stderr, flush=True)\nos._exit(0)\n')
    process = subprocess.run([sys.executable, str(BASE / "drive_check.py"), str(check), str(tmp_path),
                              '["criterion"]'], capture_output=True, text=True, timeout=5)
    assert process.returncode == 1
    assert process.stdout.count("EVAL_RESULT:") == 1
    assert json.loads(process.stdout.removeprefix("EVAL_RESULT: "))["status"] == "fail"
    assert "STDOUT_SENTINEL" in process.stderr
    assert "STDERR_SENTINEL" in process.stderr


def test_timeout_keeps_partial_diagnostics(tmp_path, capsys):
    check = checker(tmp_path, 'import time,sys\nprint("BEFORE_TIMEOUT", flush=True)\n'
                    'print("ERROR_BEFORE_TIMEOUT", file=sys.stderr, flush=True)\ntime.sleep(30)\n')
    assert driver.run_check(check, tmp_path, ["criterion"], timeout=0.15)["status"] == "fail"
    stderr = capsys.readouterr().err
    assert "BEFORE_TIMEOUT" in stderr
    assert "ERROR_BEFORE_TIMEOUT" in stderr


def test_forwarded_diagnostics_are_bounded(capsys):
    driver.emit_diagnostics("x" * 10000, "y" * 10000)
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err.count("[truncated]") == 2
    assert output.err.count("x") == 8192
    assert output.err.count("y") == 8192
