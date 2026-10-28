"""Offline regressions for observable behavior and independent outcome checks."""
import importlib.util
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("eval_graders", Path(__file__).resolve().parents[1] / "evals/graders.py")
graders = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(graders)


def task(**changes):
    return {"allowed_paths": ["src/*.py"], "forbid_commands": False,
            "required_skills": ["test-driven-development"],
            "forbidden_skills": ["robotics-software"], "tdd": True, **changes}


def test_missing_trace_never_proves_invocation_absence_or_tdd():
    checks = graders.grade_behavior(task(), {}, {}, [])
    for name in ("required_skills", "forbidden_skills", "tdd"):
        assert checks[name]["status"] == "unknown"


def test_observed_reads_and_scope_changes():
    checks = graders.grade_behavior(task(), {"README.md": "old"}, {"README.md": "new"}, [
        {"type": "skill_read", "skill": "robotics-software"},
        {"type": "skill_read", "skill": "test-driven-development"}])
    assert checks["required_skills"]["status"] == "pass"
    assert checks["forbidden_skills"]["status"] == "fail"
    assert checks["scope"]["status"] == "fail"


def test_command_violation_and_tdd_hints_are_not_chronology():
    checks = graders.grade_behavior(task(forbid_commands=True), {}, {}, [
        {"type": "command", "command": "python -m unittest", "exit_code": 1,
         "output": "AssertionError"},
        {"type": "command", "command": "python -m unittest", "exit_code": 0}])
    assert checks["commands"]["status"] == "fail"
    assert checks["tdd"]["status"] == "unknown"
    assert "2" in checks["tdd"]["reason"]


def test_scope_detects_deletions_and_accepts_allowed_changes():
    assert graders.grade_behavior(task(), {"src/a.py": "a"}, {}, [])["scope"]["status"] == "pass"
    assert graders.grade_behavior(task(), {"secret": "a"}, {}, [])["scope"]["status"] == "fail"

import json
import shutil
import subprocess
import sys
import pytest

BASE = Path(__file__).resolve().parents[1] / "evals"
TASKS = [json.loads(path.read_text()) for path in sorted((BASE / "tasks").glob("*.json"))]

GOOD = {
    "python-tdd": ("points.py", '''def deduct(balance, amount):
    if balance < 0 or amount < 0 or amount > balance:
        raise ValueError("invalid balance or amount")
    return balance - amount
'''),
    "simple-script": ("summary.py", '''def summarize(values):
    count = 0
    total = 0
    for value in values:
        count += 1
        total += value
    return {"count": count, "total": total, "mean": total / count if count else None}
'''),
    "docs-only": ("README.md", "# Local utility\n\nRun with Python 3.11 or newer.\n"),
    "fastapi-lifecycle": ("app.py", '''from fastapi import FastAPI, Depends, HTTPException

class Resource:
    def __init__(self):
        self.opened = self.closed = self.active = 0
    async def acquire(self):
        self.opened += 1
        self.active += 1
        return self
    async def release(self):
        self.closed += 1
        self.active -= 1
resource = Resource()
app = FastAPI()
async def scoped():
    item = await resource.acquire()
    try:
        yield item
    finally:
        await resource.release()
@app.get("/work")
async def work(fail: bool = False, item = Depends(scoped)):
    if fail:
        raise HTTPException(409, "requested failure")
    return {"active": item.active}
'''),
    "api-boundary": ("app.py", '''from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
app = FastAPI()
USERS = {1: {"id": 1, "name": "Ada", "password_hash": "secret", "token": "private"}}
class PublicUser(BaseModel):
    id: int
    name: str
@app.get("/users/{user_id}", response_model=PublicUser)
def get_user(user_id: int):
    if user_id not in USERS:
        raise HTTPException(404, "user not found")
    return USERS[user_id]
'''),
}


def run_check(task, workspace):
    check = (BASE / "tasks" / task["check"]).resolve()
    result = subprocess.run([sys.executable, "-B", str(check), str(workspace)],
                            capture_output=True, text=True, timeout=20)
    lines = [line for line in result.stdout.splitlines() if line.startswith("EVAL_RESULT: ")]
    assert len(lines) == 1, (result.stdout, result.stderr)
    payload = json.loads(lines[0].removeprefix("EVAL_RESULT: "))
    assert result.returncode == (0 if payload["status"] == "pass" else 1)
    assert payload["checks"]
    return payload


@pytest.mark.parametrize("task", [task for task in TASKS if task["check"]], ids=lambda task: task["id"])
def test_independent_checks_reject_baseline_and_accept_good_implementation(task, tmp_path):
    if task["id"] in ("api-boundary", "fastapi-lifecycle"):
        pytest.importorskip("fastapi")
        pytest.importorskip("httpx")
    shutil.copytree(BASE / "tasks" / task["fixture"], tmp_path, dirs_exist_ok=True)
    assert run_check(task, tmp_path)["status"] == "fail"
    # The trusted grader must still work after agent-controlled tests are deleted.
    shutil.rmtree(tmp_path / "tests", ignore_errors=True)
    path, source = GOOD[task["id"]]
    (tmp_path / path).write_text(source)
    assert run_check(task, tmp_path)["status"] == "pass"


def test_six_tasks_reference_existing_trusted_inputs():
    assert len(TASKS) == 6
    for task in TASKS:
        assert (BASE / "tasks" / task["fixture"]).is_dir()
        assert task["schema_version"] == 1
        assert task["prompt"]
        if task["check"]:
            assert (BASE / "tasks" / task["check"]).is_file()


def test_deleting_agent_tests_cannot_make_bad_baseline_pass(tmp_path):
    task = next(task for task in TASKS if task["id"] == "python-tdd")
    shutil.copytree(BASE / "tasks" / task["fixture"], tmp_path, dirs_exist_ok=True)
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_fake.py").write_text("def test_fake(): assert True\n")
    shutil.rmtree(tmp_path / "tests")
    assert run_check(task, tmp_path)["status"] == "fail"


def test_scope_no_command_and_no_applicable_checks():
    checks = graders.grade_behavior(task(allowed_paths=[], forbid_commands=True,
                                         required_skills=[], forbidden_skills=[], tdd=False),
                                    {}, {"new.py": "digest"}, [])
    assert checks["scope"]["status"] == "fail"
    assert checks["commands"]["status"] == "unknown"
    for name in ("required_skills", "forbidden_skills", "tdd"):
        assert checks[name]["status"] == "not_applicable"


@pytest.mark.parametrize("task_id, replacement", [
    ("fastapi-lifecycle", '    finally:\n        if not fail:\n            await resource.release()\n'),
    ("api-boundary", '@app.get("/users/{user_id}")'),
])
def test_api_checks_reject_lifecycle_failure_and_missing_response_model(task_id, replacement, tmp_path):
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    task = next(task for task in TASKS if task["id"] == task_id)
    path, source = GOOD[task_id]
    if task_id == "fastapi-lifecycle":
        # Correct on success, deliberately leaks on the requested error path.
        source = source.replace("async def scoped():", "async def scoped(fail: bool = False):")
        source = source.replace("    finally:\n        await resource.release()\n", replacement)
    else:
        source = source.replace('@app.get("/users/{user_id}", response_model=PublicUser)', replacement)
        source = source.replace('return USERS[user_id]', 'return {"id": USERS[user_id]["id"], "name": USERS[user_id]["name"]}')
    (tmp_path / path).write_text(source)
    payload = run_check(task, tmp_path)
    assert payload["status"] == "fail"
    key = "cleanup_2" if task_id == "fastapi-lifecycle" else "public_response_model"
    assert payload["checks"][key] is False


def test_runtime_modules_cover_trusted_check_dependencies():
    import ast

    for item in TASKS:
        expected = set()
        if item["check"]:
            tree = ast.parse((BASE / "tasks" / item["check"]).read_text())
            if any(isinstance(node, ast.ImportFrom) and node.module == "fastapi.testclient"
                   for node in ast.walk(tree)):
                # Starlette TestClient imports httpx even though our check imports FastAPI.
                expected.update(("fastapi", "httpx"))
        assert set(item.get("runtime_modules", [])) == expected


def test_raw_command_mentions_do_not_establish_skill_read_or_tdd():
    checks = graders.grade_behavior(task(), {}, {}, [{
        "type": "command", "command": "echo test-driven-development RED GREEN",
        "exit_code": 0, "output": "test-driven-development RED GREEN"}])
    assert checks["required_skills"]["status"] == "unknown"
    assert checks["tdd"]["status"] == "unknown"
