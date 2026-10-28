"""Offline runner contracts; fake process responses are not model evidence."""
import importlib.util
import json
from pathlib import Path
import os
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("run_evals", ROOT / "scripts/run_evals.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def test_codex_jsonl_records_actual_command_and_not_message_claim():
    trace = "\n".join(json.dumps(event) for event in [
        {"type": "item.completed", "item": {"type": "agent_message", "text": "I read SKILL.md"}},
        {"type": "item.completed", "item": {"type": "command_execution", "command": "cat /provider/plugins/common/skills/test-driven-development/SKILL.md", "exit_code": 0, "aggregated_output": "procedure"}},
        {"type": "turn.completed", "usage": {"input_tokens": 123}},
    ])
    result = runner.parse_trace(trace, {"test-driven-development": "common:test-driven-development"})
    assert [event["type"] for event in result["events"]] == ["message", "command", "skill_read"]
    assert result["events"][-1]["skill"] == "common:test-driven-development"
    assert result["usage"]["input_tokens"] == 123


def test_comparison_keeps_unknowns_out_of_success_denominator_and_pairs_hosts():
    trials = [
        {"engine": "codex", "task": "one", "trial": 1, "condition": "baseline", "status": "completed", "outcome": {"status": "fail"}},
        {"engine": "codex", "task": "one", "trial": 1, "condition": "candidate", "status": "completed", "outcome": {"status": "pass"}},
        {"engine": "codex", "task": "two", "trial": 1, "condition": "baseline", "status": "environment_error", "outcome": {"status": "unknown"}},
        {"engine": "codex", "task": "two", "trial": 1, "condition": "candidate", "status": "completed", "outcome": {"status": "pass"}},
    ]
    result = runner.compare_trials(trials)
    assert result["paired_outcomes"] == {"comparable": 1, "improved": 1, "regressed": 0, "unchanged": 0, "unknown": 1}
    assert result["conditions"]["baseline"]["outcome_pass"] == 0
    assert result["conditions"]["baseline"]["outcome_known"] == 1


@pytest.mark.parametrize("command", [
    "echo cat /provider/plugins/common/skills/test-driven-development/SKILL.md",
    "cat /tmp/test-driven-development/SKILL.md",
    "printf '%s' '/provider/plugins/common/skills/test-driven-development/SKILL.md'",
    "cat --help /provider/plugins/common/skills/test-driven-development/SKILL.md",
    "cat /etc/hosts # /provider/plugins/common/skills/test-driven-development/SKILL.md",
    "cat /etc/hosts; echo /provider/plugins/common/skills/test-driven-development/SKILL.md",
])
def test_path_mentions_are_not_skill_reads(command):
    event = {"type": "item.completed", "item": {"type": "command_execution", "command": command,
             "exit_code": 0, "aggregated_output": "something"}}
    parsed = runner.parse_trace(json.dumps(event), {"test-driven-development": "common:test-driven-development"})
    assert not any(event["type"] == "skill_read" for event in parsed["events"])


def test_empty_trace_is_not_completed_model_work():
    assert runner.parse_trace("", {})["completed"] is False
    assert runner.parse_trace('{"type":"turn.completed"}', {})["completed"] is True
    assert runner.parse_trace('{"type":"result","is_error":true}', {})["completed"] is False


def test_claude_successful_native_skill_tool_is_observed_not_claimed():
    events = [
        {"type": "assistant", "message": {"content": [{"type": "tool_use", "id": "read1", "name": "Skill", "input": {"skill": "common:test-driven-development"}}]}},
        {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "read1", "content": "procedure"}]}},
        {"type": "result", "is_error": False, "usage": {"input_tokens": 9}},
    ]
    result = runner.parse_trace("\n".join(map(json.dumps, events)), {"test-driven-development": "common:test-driven-development"})
    assert result["completed"]
    assert result["events"][0]["skill"] == "common:test-driven-development"


def test_all_current_tasks_validate_against_catalog(tmp_path):
    tasks = runner.load_tasks(ROOT / "evals/tasks")
    assert len(tasks) == 6
    metadata = runner.prepare_provider(ROOT, tmp_path / "provider", sorted({bundle for task in tasks for bundle in task["bundles"]}))
    for task in tasks:
        runner.validate_skills(task, metadata)
    with pytest.raises(ValueError, match="skill"):
        runner.validate_skills({**tasks[0], "required_skills": ["made-up"]}, metadata)


def test_run_process_preserves_timeout_and_bounds_fast_output():
    timeout = runner.run_process([sys.executable, "-c", "import time; print('started',flush=True); time.sleep(5)"], 0.1)
    assert timeout["status"] == "timeout"
    assert "started" in timeout["stdout"]
    output = runner.run_process([sys.executable, "-c", "print('x'*(9*1024*1024))"], 3)
    assert output["status"] == "output_limit"
    assert len(output["stdout"]) <= 8*1024*1024


def test_docker_options_never_mount_host_home_socket_or_credentials(tmp_path):
    argv = runner.container_options("image", "trial", tmp_path, network="none")
    assert "--user" in argv and argv[argv.index("--user") + 1].split(":")[0] != "0"
    assert "--cap-drop=ALL" in argv and "--read-only" in argv and "--pull=never" in argv
    assert "--network" in argv and "none" in argv
    assert not any("docker.sock" in word or "API_KEY=" in word for word in argv)


def test_failed_agent_cleanup_blocks_grading_and_is_reported(tmp_path, monkeypatch):
    from types import SimpleNamespace
    initial = tmp_path / "initial"
    initial.mkdir()
    (initial / "points.py").write_text("x=1\n")
    output = tmp_path / "out"
    output.mkdir()
    calls = []
    def fake_process(argv, timeout, env=None):
        calls.append(argv)
        return {"status": "completed", "returncode": 1 if argv[1:3] == ["rm", "--force"] else 0,
                "stdout": '{"type":"turn.completed"}\n', "stderr": "", "seconds": 0}
    monkeypatch.setattr(runner, "run_process", fake_process)
    monkeypatch.setenv(runner.CREDENTIALS["codex"], "test-only")
    task = runner.load_tasks(ROOT / "evals/tasks", ["python-tdd"])[0]
    args = SimpleNamespace(output=output, engine="codex", model="fake", image="fake", timeout=10)
    row = runner.run_trial(task, initial, None, {"skill_ids": {}}, args, "baseline", 1)
    assert row["status"] == "environment_error"
    assert row["outcome"]["status"] == "unknown"
    assert not any("/checks/check.py" in word for argv in calls for word in argv)
    assert (output / "python-tdd-1-baseline/cleanup.stdout").exists()


def test_scope_snapshot_records_symlinks_without_reading_target(tmp_path):
    (tmp_path / "link").symlink_to("/etc/passwd")
    assert runner.snapshot(tmp_path) == {"link": "symlink:/etc/passwd"}
    with pytest.raises(ValueError, match="Symlinks"):
        runner.clean_copy(tmp_path, tmp_path.parent / "copy")


def test_missing_image_runtime_is_environment_failure_before_model(tmp_path, monkeypatch):
    from types import SimpleNamespace
    initial = tmp_path / "initial"
    initial.mkdir()
    (initial / "app.py").write_text("# baseline\n")
    output = tmp_path / "out"
    output.mkdir()
    calls = []
    def fake_process(argv, timeout, env=None):
        calls.append(argv)
        return {"status": "completed", "returncode": int(any("importlib.import_module('fastapi')" in word for word in argv)),
                "stdout": "fake-version", "stderr": "", "seconds": 0}
    monkeypatch.setattr(runner, "run_process", fake_process)
    monkeypatch.setenv(runner.CREDENTIALS["codex"], "test-only")
    task = runner.load_tasks(ROOT / "evals/tasks", ["api-boundary"])[0]
    args = SimpleNamespace(output=output, engine="codex", model="fake", image="fake", timeout=10)
    row = runner.run_trial(task, initial, None, {"skill_ids": {}}, args, "baseline", 1)
    assert row["status"] == "environment_error"
    assert row["outcome"]["status"] == "unknown"
    assert not any("--model" in argv for argv in calls)


def test_archive_redacts_key_in_both_logs_and_in_memory(tmp_path):
    result = {"stdout": "sensitive-key", "stderr": "error sensitive-key"}
    runner.archive(tmp_path / "trace", result, ["sensitive-key"])
    assert result == {"stdout": "[REDACTED]", "stderr": "error [REDACTED]"}
    assert "sensitive-key" not in (tmp_path / "trace.stdout").read_text()


@pytest.mark.parametrize("task", runner.load_tasks(ROOT / "evals/tasks"), ids=lambda task: task["id"])
def test_each_task_prepares_its_own_complete_provider_selection(task, tmp_path):
    metadata = runner.prepare_provider(ROOT, tmp_path / "provider", task["bundles"])
    runner.validate_skills(task, metadata)


@pytest.mark.parametrize("invalid_input", ["dependencies", "skills", "fixture", "candidate_source", "baseline_source"])
def test_all_inputs_validate_before_trials_or_output_creation(tmp_path, monkeypatch, invalid_input):
    tasks = runner.load_tasks(ROOT / "evals/tasks", ["docs-only", "python-tdd"])
    invalid = tasks[1]
    if invalid_input == "dependencies":
        invalid["bundles"] = ["common", "python", "fastapi"]
    elif invalid_input == "skills":
        invalid["required_skills"] = ["common:missing-skill"]
    elif invalid_input == "fixture":
        invalid["fixture"] = tmp_path / "missing-fixture"
    monkeypatch.setattr(runner, "load_tasks", lambda *args: tasks)
    monkeypatch.setenv(runner.CREDENTIALS["codex"], "test-only")
    trial_calls = []

    def fake_process(argv, timeout, env=None):
        return {"status": "completed", "returncode": 0, "stdout": "sha256:" + "a" * 64,
                "stderr": "", "seconds": 0}

    def fake_trial(task, initial, provider, metadata, args, condition, number):
        trial_calls.append((task["id"], condition))
        return {"engine": "codex", "task": task["id"], "trial": number, "condition": condition,
                "status": "completed", "outcome": {"status": "pass"}, "behavior": {}}

    monkeypatch.setattr(runner, "run_process", fake_process)
    monkeypatch.setattr(runner, "run_trial", fake_trial)
    output = tmp_path / "artifacts"
    candidate = tmp_path / "missing-candidate" if invalid_input == "candidate_source" else ROOT
    baseline = str(tmp_path / "missing-baseline") if invalid_input == "baseline_source" else "vanilla"
    with pytest.raises(SystemExit) as error:
        runner.main(["--engine", "codex", "--model", "test-model", "--image", "test-image",
                     "--candidate", str(candidate), "--baseline", baseline, "--output", str(output)])
    assert error.value.code == 2
    assert trial_calls == []
    assert not output.exists()


def test_removed_device_login_option_is_rejected_before_runtime(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(runner, "run_process", lambda *args, **kwargs: pytest.fail("Removed login option reached runtime"))
    with pytest.raises(SystemExit) as error:
        runner.main(["--engine", "codex", "--model", "test-model", "--image", "test-image",
                     "--output", str(tmp_path / "output"), "--codex-auth-volume", "retired-volume"])
    assert error.value.code == 2
    assert "unrecognized arguments: --codex-auth-volume" in capsys.readouterr().err
    assert not (tmp_path / "output").exists()


@pytest.mark.parametrize("engine,key", [("codex", "CODEX_API_KEY"), ("claude", "ANTHROPIC_API_KEY")])
def test_only_dedicated_key_is_forwarded_to_agent_and_never_grader(tmp_path, monkeypatch, engine, key):
    from types import SimpleNamespace
    initial = tmp_path / "initial"
    initial.mkdir()
    (initial / "price.py").write_text("# fixture\n")
    output = tmp_path / "out"
    output.mkdir()
    calls = []
    def fake_process(argv, timeout, env=None):
        calls.append(argv)
        return {"status": "completed", "returncode": 0,
                "stdout": 'EVAL_RESULT: {"status":"pass","checks":{"synthetic":true}}\n' if "/checks/drive_check.py" in argv else '{"type":"turn.completed"}\n', "stderr": "", "seconds": 0}
    monkeypatch.setattr(runner, "run_process", fake_process)
    monkeypatch.setenv(runner.CREDENTIALS[engine], "eval-key-for-test-only")
    task = runner.load_tasks(ROOT / "evals/tasks", ["python-tdd"])[0]
    args = SimpleNamespace(output=output, engine=engine, model="fake", image="fake", timeout=10)
    row = runner.run_trial(task, initial, None, {"skill_ids": {}}, args, "baseline", 1)
    assert row["status"] == "completed"
    assert row["auth_mode"] == "dedicated-api-key"
    assert not any("/eval-auth" in word or "auth.json" in word for call in calls for word in call)
    invocation = next(call for call in calls if "--model" in call)
    assert invocation[invocation.index("--env") + 1] == key
    assert "eval-key-for-test-only" not in " ".join(invocation)
    grading = next(call for call in calls if "/checks/drive_check.py" in call)
    assert not any("/eval-auth" in word or "API_KEY" in word for word in grading)


def test_nested_auth_fields_and_jwt_are_redacted_without_reading_credentials(tmp_path):
    jwt = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJmb28ifQ.signature"
    data = {"item": {"aggregated_output": json.dumps({"access_token": jwt, "refresh_token": "refresh-secret", "id_token": jwt})}}
    result = {"stdout": json.dumps(data), "stderr": "Bearer " + jwt}
    runner.archive(tmp_path / "trace", result)
    assert jwt not in result["stdout"] + result["stderr"]
    assert "refresh-secret" not in result["stdout"]
    assert "[REDACTED]" in result["stdout"]


def test_fresh_home_is_initialized_before_any_real_cli_contract(tmp_path, monkeypatch):
    from types import SimpleNamespace
    initial = tmp_path / "initial"
    initial.mkdir()
    output = tmp_path / "output"
    output.mkdir()
    initialized = False
    def fake_process(argv, timeout, env=None):
        nonlocal initialized
        if "python3" in argv and any("mkdir" in word and "/home/eval/.codex" in word and "/home/eval/.claude" in word for word in argv):
            initialized = True
        failed = "--version" in argv and not initialized
        return {"status": "completed", "returncode": int(failed), "stdout": '{"type":"turn.completed"}',
                "stderr": "CODEX_HOME does not exist" if failed else "", "seconds": 0}
    monkeypatch.setattr(runner, "run_process", fake_process)
    monkeypatch.setenv(runner.CREDENTIALS["codex"], "test-only")
    task = runner.load_tasks(ROOT / "evals/tasks", ["readonly-analysis"])[0]
    args = SimpleNamespace(output=output, engine="codex", model="fake", image="fake", timeout=10)
    row = runner.run_trial(task, initial, None, {"skill_ids": {}}, args, "baseline", 1)
    assert row["status"] == "completed"
    assert initialized


def test_native_cache_reads_require_exact_attested_paths():
    identity = "common:test-driven-development"
    path = "/home/eval/.codex/plugins/cache/konglabs-agent-skills/common/0.1.1/skills/test-driven-development/SKILL.md"
    ids = {"test-driven-development": identity}
    event = {"type": "item.completed", "item": {"type": "command_execution", "command": "cat " + path,
             "exit_code": 0, "aggregated_output": "procedure"}}
    assert not any(item["type"] == "skill_read" for item in runner.parse_trace(json.dumps(event), ids)["events"])
    observed = runner.parse_trace(json.dumps(event), ids, {path: identity})
    assert observed["events"][-1]["type"] == "skill_read"
    assert observed["events"][-1]["skill"] == identity
    event["item"]["command"] = "cat " + path.replace("/0.1.1/", "/unregistered/")
    assert not any(item["type"] == "skill_read" for item in runner.parse_trace(json.dumps(event), ids, {path: identity})["events"])


@pytest.mark.parametrize("mismatch", [False, True])
def test_native_install_attestation_precedes_model_and_rejects_wrong_bytes(tmp_path, monkeypatch, mismatch):
    from types import SimpleNamespace
    import hashlib

    task = runner.load_tasks(ROOT / "evals/tasks", ["python-tdd"])[0]
    initial = tmp_path / "initial"
    runner.prepare_fixture(task, initial)
    provider = tmp_path / "provider"
    metadata = runner.prepare_provider(ROOT, provider, task["bundles"])
    hashes = {}
    for skill, identity in metadata["skill_ids"].items():
        bundle = identity.split(":")[0]
        if bundle in task["bundles"]:
            path = f'/home/eval/.codex/plugins/cache/konglabs-agent-skills/{bundle}/{metadata["version"]}/skills/{skill}/SKILL.md'
            hashes[path] = hashlib.sha256((provider / "plugins" / bundle / "skills" / skill / "SKILL.md").read_bytes()).hexdigest()
    if mismatch:
        hashes[next(iter(hashes))] = "0" * 64
    calls = []

    def fake_process(argv, timeout, env=None):
        calls.append(argv)
        stdout = json.dumps(hashes) if any("hashlib.sha256" in word for word in argv) else '{"type":"turn.completed"}\n'
        if "/checks/drive_check.py" in argv:
            stdout = 'EVAL_RESULT: {"status":"pass","checks":{"synthetic":true}}\n'
        return {"status": "completed", "returncode": 0, "stdout": stdout, "stderr": "", "seconds": 0}

    monkeypatch.setattr(runner, "run_process", fake_process)
    monkeypatch.setenv(runner.CREDENTIALS["codex"], "test-only")
    output = tmp_path / "output"
    output.mkdir()
    args = SimpleNamespace(output=output, engine="codex", model="fake", image="fake", timeout=30)
    row = runner.run_trial(task, initial, provider, metadata, args, "candidate", 1)
    if mismatch:
        assert row["status"] == "environment_error"
        assert "attestation" in row["error"].lower()
        assert not any("--model" in call for call in calls)
    else:
        assert row["status"] == "completed", row
        assert set(row["installed_skill_paths"]) == set(hashes)
        assert (output / "python-tdd-1-candidate/installed-skills.stdout").exists()
        probe = next(index for index, call in enumerate(calls) if any("hashlib.sha256" in word for word in call))
        model = next(index for index, call in enumerate(calls) if "--model" in call)
        assert probe < model


def test_native_0164_multifile_cat_records_each_exact_registered_skill():
    # Observed command shape from the real API-boundary candidate trace.
    paths = {
        ".agents/skills/fastapi/skills/fastapi-backend/SKILL.md": "fastapi:fastapi-backend",
        ".agents/skills/common/skills/test-driven-development/SKILL.md": "common:test-driven-development",
        ".agents/skills/common/skills/verification-before-completion/SKILL.md": "common:verification-before-completion",
    }
    command = "/bin/zsh -c 'cat " + " ".join(paths) + "'"
    event = {"type": "item.completed", "item": {"type": "command_execution", "command": command,
             "exit_code": 0, "aggregated_output": "---\nname: fastapi-backend\n...\n---\nname: test-driven-development\n..."}}
    ids = {identity.split(":")[1]: identity for identity in paths.values()}
    parsed = runner.parse_trace(json.dumps(event), ids, paths)
    assert [item["skill"] for item in parsed["events"] if item["type"] == "skill_read"] == list(paths.values())
    assert all("not adherence proof" in item["evidence"] for item in parsed["events"] if item["type"] == "skill_read")


@pytest.mark.parametrize("suffix", [
    " /unregistered/same-name/SKILL.md", " --help", " ; echo hi", " # comment", " | cat", " && true",
])
def test_multifile_cat_rejects_unknown_arguments_options_and_shell_syntax(suffix):
    path = ".agents/skills/common/skills/test-driven-development/SKILL.md"
    identity = "common:test-driven-development"
    event = {"type": "item.completed", "item": {"type": "command_execution", "command": "cat " + path + suffix,
             "exit_code": 0, "aggregated_output": "procedure"}}
    parsed = runner.parse_trace(json.dumps(event), {"test-driven-development": identity}, {path: identity})
    assert not any(item["type"] == "skill_read" for item in parsed["events"])
