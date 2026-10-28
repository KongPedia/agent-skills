"""Offline contracts only; no test invokes an authenticated model."""
import importlib.util
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("host_evals", ROOT / "scripts/run_host_evals.py")
host = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(host)


def test_inventory_disables_exact_files_including_hidden_and_symlink_aliases(tmp_path, monkeypatch):
    home, codex = tmp_path / "home", tmp_path / "codex"
    original = tmp_path / "external" / "skill"
    original.mkdir(parents=True)
    (original / "SKILL.md").write_text("skill")
    local = home / ".agents/skills"
    local.mkdir(parents=True)
    (local / "alias").symlink_to(original, target_is_directory=True)
    (original / "cycle").symlink_to(local, target_is_directory=True)
    builtin = codex / "skills/.system/example/SKILL.md"
    builtin.parent.mkdir(parents=True)
    builtin.write_text("builtin")
    disabled = host.inventory_skills(home, codex)
    assert str(local / "alias/SKILL.md") in disabled
    assert str(original / "SKILL.md") in disabled
    assert str(builtin) in disabled
    assert all(path.endswith("/SKILL.md") for path in disabled)
    assert len(disabled) == len(set(disabled))


def test_child_and_parent_environment_exclude_auth_and_session_variables(monkeypatch):
    monkeypatch.setenv("HOME", "/example/home")
    monkeypatch.setenv("CODEX_HOME", "/example/codex")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "not-in-child")
    monkeypatch.setenv("CODEX_API_KEY", "not-in-child")
    monkeypatch.setenv("CODEX_THREAD_ID", "not-in-child")
    env = host.host_environment()
    assert set(env) == {"PATH", "HOME", "CODEX_HOME", "TMPDIR"}
    assert env["PATH"].split(os.pathsep)[0] == str(Path(host.sys.executable).parent)
    assert "not-in-child" not in str(env)


def test_command_keeps_prompt_identical_and_uses_exact_skill_file_overrides(tmp_path):
    args = SimpleNamespace(codex_bin="codex", model="test-model")
    env = {"PATH": "/isolated/python:/usr/bin"}
    prompt = "Exact frozen task prompt"
    command = host.host_command(args, tmp_path, ["/ambient/skill/SKILL.md"], env) + [prompt]
    assert command[-1] == prompt
    assert "--ignore-user-config" in command and "--strict-config" in command
    assert "skip_host_skill_discovery" not in " ".join(command)
    assert "skills.include_instructions=true" in command
    assert 'skills.config=[{path="/ambient/skill/SKILL.md",enabled=false}]' in command
    assert 'shell_environment_policy.inherit="none"' in command
    assert "sandbox_workspace_write.network_access=false" in command
    assert "sandbox_workspace_write.exclude_slash_tmp=true" in command
    assert "sandbox_workspace_write.exclude_tmpdir_env_var=true" in command
    assert "project_doc_max_bytes=0" in command


def test_project_skills_are_native_copies_with_exact_read_aliases(tmp_path):
    provider = tmp_path / "provider"
    skill = provider / "plugins/common/skills/test-driven-development"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("procedure")
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    metadata = {"skill_ids": {"test-driven-development": "common:test-driven-development"}}
    mapping = host.stage_skills(provider, {"bundles": ["common"]}, workspace, metadata)
    relative = ".agents/skills/common/skills/test-driven-development/SKILL.md"
    assert (workspace / relative).read_text() == "procedure"
    assert mapping[relative] == "common:test-driven-development"
    assert mapping["./" + relative] == "common:test-driven-development"
    assert mapping[str(workspace / relative)] == "common:test-driven-development"
    assert host.stage_skills(None, {"bundles": []}, workspace, {}) == {}


def test_paired_trials_keep_prompts_equal_capture_guidance_and_grade_external_results(tmp_path, monkeypatch):
    task = host.shared.load_tasks(ROOT / "evals/tasks", ["python-tdd"])[0]
    initial = tmp_path / "initial"
    host.shared.prepare_fixture(task, initial)
    provider = tmp_path / "provider"
    metadata = host.shared.prepare_provider(ROOT, provider, task["bundles"])
    output = tmp_path / "out"
    output.mkdir()
    args = SimpleNamespace(output=output, codex_bin="fake-codex", model="fake", timeout=10, grader_image="sha256:" + "a" * 64)
    prompts = []
    real_process = host.shared.run_process

    def fake_model_only(argv, timeout, env=None):
        if argv[0] == "docker":
            return {"status": "completed", "returncode": 0, "stdout": 'EVAL_RESULT: {"status":"pass","checks":{"synthetic":true}}', "stderr": "", "seconds": 0}
        if argv[0] != "fake-codex":
            assert argv[0] == "git"
            return real_process(argv, timeout, env)
        prompts.append(argv[-1])
        workspace = Path(argv[argv.index("-C") + 1])
        (workspace / "points.py").write_text('def deduct(balance, amount):\n    if balance < 0 or amount < 0 or amount > balance:\n        raise ValueError()\n    return balance - amount\n')
        events = []
        path = workspace / ".agents/skills/common/skills/test-driven-development/SKILL.md"
        if path.exists():
            events.append({"type": "item.completed", "item": {"type": "command_execution",
                           "command": "cat .agents/skills/common/skills/test-driven-development/SKILL.md",
                           "exit_code": 0, "aggregated_output": "procedure"}})
        events.append({"type": "turn.completed", "usage": {"input_tokens": 10}})
        return {"status": "completed", "returncode": 0, "stdout": "\n".join(map(json.dumps, events)),
                "stderr": "", "seconds": 0}

    monkeypatch.setattr(host.shared, "run_process", fake_model_only)
    env = host.host_environment()
    prepared = (task, initial, {"baseline": (None, {"kind": "host-no-project-skills", "skill_ids": {}}),
                                "candidate": (provider, metadata)})
    rows = host.run_pair(prepared, args, 1, [], env)
    assert [row["condition"] for row in rows] == ["baseline", "candidate"]
    assert prompts == [task["prompt"], task["prompt"]]
    assert all(row["outcome"]["status"] == "pass" for row in rows)
    assert all(row["behavior"]["scope"]["status"] == "pass" for row in rows)
    assert all(row["behavior"]["tdd"]["status"] == "unknown" for row in rows)
    candidate = output / "python-tdd-1-candidate"
    before = json.loads((candidate / "before.json").read_text())
    after = json.loads((candidate / "after.json").read_text())
    guidance = ".agents/skills/common/skills/test-driven-development/SKILL.md"
    assert before[guidance] == after[guidance]
    assert rows[1]["behavior"]["required_skills"]["status"] == "pass"
    assert "points.py" in (candidate / "changes.diff").read_text()
    assert not any(path.startswith(".git/") for path in before)


@pytest.mark.parametrize("invalid", ["fixture", "skill", "dependencies", "cli"])
def test_preflight_rejects_bad_inputs_before_output_or_paid_calls(tmp_path, monkeypatch, invalid):
    tasks = host.shared.load_tasks(ROOT / "evals/tasks", ["docs-only", "python-tdd"])
    if invalid == "fixture":
        tasks[1]["fixture"] = tmp_path / "missing"
    elif invalid == "skill":
        tasks[1]["required_skills"] = ["common:missing"]
    elif invalid == "dependencies":
        tasks[1]["runtime_modules"] = ["missing_eval_dependency"]
    monkeypatch.setattr(host.shared, "load_tasks", lambda *args: tasks)
    monkeypatch.setattr(host.shutil, "which", lambda *args, **kwargs: "docker" if args[0] == "docker" else "/fake/codex")
    monkeypatch.setattr(host, "inventory_skills", lambda *args: [])
    calls = []

    def safe_preflight_only(argv, timeout, env=None):
        calls.append(argv)
        assert argv[0] in ("git", "/fake/codex", host.sys.executable, "docker")
        if argv[0] == "/fake/codex" and "--model" in argv:
            assert "--help" in argv
        failed = (invalid == "dependencies" and any("missing_eval_dependency" in word for word in argv)
                  or invalid == "cli" and argv[0] == "/fake/codex")
        return {"status": "completed", "returncode": int(failed), "stdout": "sha256:" + "a" * 64 if argv[:3] == ["docker", "image", "inspect"] else "version", "stderr": "bad input" if failed else "", "seconds": 0}

    monkeypatch.setattr(host.shared, "run_process", safe_preflight_only)
    monkeypatch.setattr(host, "run_pair", lambda *args: pytest.fail("Paid calls must not start"))
    output = tmp_path / "output"
    with pytest.raises(SystemExit) as error:
        host.main(["--model", "fake", "--candidate", str(ROOT), "--output", str(output), "--trials", "1", "--grader-image", "test-image"])
    assert error.value.code == 2
    assert not output.exists()


def test_pair_order_alternates_without_retries(monkeypatch):
    seen = []
    monkeypatch.setattr(host, "run_trial", lambda task, initial, provider, metadata, args, condition, number, disabled, env:
                        seen.append(condition) or {"condition": condition})
    prepared = ({}, None, {"baseline": (None, {}), "candidate": (None, {})})
    host.run_pair(prepared, None, 2, [], {})
    assert seen == ["candidate", "baseline"]


def test_main_records_scheduled_denominators_without_silently_dropping_unknowns(tmp_path, monkeypatch):
    tasks = host.shared.load_tasks(ROOT / "evals/tasks", ["docs-only", "readonly-analysis"])
    monkeypatch.setattr(host.shared, "load_tasks", lambda *args: tasks)
    monkeypatch.setattr(host.shutil, "which", lambda *args, **kwargs: "docker" if args[0] == "docker" else "/fake/codex")
    monkeypatch.setattr(host, "inventory_skills", lambda *args: [])
    monkeypatch.setattr(host.shared, "run_process", lambda *args, **kwargs:
                        {"status": "completed", "returncode": 0, "stdout": "sha256:" + "a" * 64, "stderr": "", "seconds": 0})

    def no_model_pair(prepared, args, number, disabled, env):
        task = prepared[0]
        return [{"engine": "codex", "task": task["id"], "trial": number, "condition": condition,
                 "status": "completed", "outcome": {"status": "pass" if task["check"] else "unknown"},
                 "behavior": {}} for condition in ("baseline", "candidate")]

    monkeypatch.setattr(host, "run_pair", no_model_pair)
    output = tmp_path / "output"
    assert host.main(["--model", "fake", "--output", str(output), "--trials", "2", "--grader-image", "test-image"]) == 0
    report = json.loads((output / "eval_report.json").read_text())
    assert report["scheduled_per_condition"] == {"trials": 4, "externally_checkable": 2, "semantic_review": 2}
    assert len(report["trials"]) == 8
    assert report["summary"]["paired_outcomes"]["unknown"] == 2
    assert report["provenance"]["mode"] == "host-conditional project-skill comparison"
    assert report["provenance"]["driver_hash"]


def test_native_bundle_copy_preserves_relative_reference_closure(tmp_path):
    provider = tmp_path / "provider"
    bundle = provider / "plugins/common"
    source = bundle / "skills/example/SKILL.md"
    source.parent.mkdir(parents=True)
    source.write_text("Read [reference](../../references/engineering.md).\n")
    reference = bundle / "references/engineering.md"
    reference.parent.mkdir()
    reference.write_text("boundary guidance\n")
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    paths = host.stage_skills(provider, {"bundles": ["common"]}, workspace,
                              {"skill_ids": {"example": "common:example"}})
    installed = workspace / ".agents/skills/common/skills/example/SKILL.md"
    assert installed.read_bytes() == source.read_bytes()
    assert (installed.parent / "../../references/engineering.md").read_bytes() == reference.read_bytes()
    assert paths[str(installed)] == "common:example"


@pytest.mark.parametrize("cleanup_ok", [True, False])
def test_generated_code_grading_never_runs_on_host_and_cleanup_is_confirmed(tmp_path, monkeypatch, cleanup_ok):
    task = host.shared.load_tasks(ROOT / "evals/tasks", ["docs-only"])[0]
    initial = tmp_path / "initial"
    host.shared.prepare_fixture(task, initial)
    output = tmp_path / "output"
    output.mkdir()
    args = SimpleNamespace(output=output, codex_bin="fake-codex", model="fake", timeout=10,
                           grader_image="sha256:" + "a" * 64)
    calls = []

    def fake_process(argv, timeout, env=None):
        calls.append(argv)
        grading = any(str(word).endswith("drive_check.py") for word in argv)
        failed = argv[:3] == ["docker", "rm", "--force"] and not cleanup_ok
        return {"status": "completed", "returncode": int(failed),
                "stdout": 'EVAL_RESULT: {"status":"pass","checks":{"readme_exact":true}}\n' if grading else '{"type":"turn.completed"}\n',
                "stderr": "", "seconds": 0}

    monkeypatch.setattr(host.shared, "run_process", fake_process)
    row = host.run_trial(task, initial, None, {"skill_ids": {}}, args, "baseline", 1, [], host.host_environment())
    grading = next(call for call in calls if any(str(word).endswith("drive_check.py") for word in call))
    assert grading[:2] == ["docker", "run"]
    assert grading[grading.index("--network") + 1] == "none"
    assert any("dst=/workspace,readonly" in word for word in grading)
    assert any("dst=/checks,readonly" in word for word in grading)
    assert not any("/eval-auth" in word or "API_KEY" in word or "dst=/provider" in word for word in grading)
    assert any(call[:3] == ["docker", "rm", "--force"] for call in calls)
    assert row["status"] == ("completed" if cleanup_ok else "environment_error")
    assert row["outcome"]["status"] == ("pass" if cleanup_ok else "unknown")


def test_missing_grader_image_rejects_before_any_trial_or_output(tmp_path, monkeypatch):
    monkeypatch.setattr(host.shutil, "which", lambda *args, **kwargs: "docker" if args[0] == "docker" else "/fake/codex")
    monkeypatch.setattr(host.shared, "run_process", lambda *args, **kwargs: pytest.fail("No process before required grader selection"))
    output = tmp_path / "output"
    with pytest.raises(SystemExit) as error:
        host.main(["--model", "fake", "--output", str(output)])
    assert error.value.code == 2
    assert not output.exists()


def test_followup_dataset_and_protocol_are_selected_and_recorded(tmp_path, monkeypatch):
    # Reusing the original dataset/protocol would silently mislabel a follow-up experiment.
    dataset = tmp_path / "followup/tasks"
    dataset.mkdir(parents=True)
    protocol = dataset.parent / "protocol.json"
    protocol.write_text('{"id":"followup"}')
    task = host.shared.load_tasks(ROOT / "evals/tasks", ["readonly-analysis"])[0]
    selected = []
    monkeypatch.setattr(host.shared, "load_tasks", lambda directory, ids:
                        selected.append((directory, ids)) or [task])
    monkeypatch.setattr(host.shutil, "which", lambda *args, **kwargs: "/fake/codex")
    monkeypatch.setattr(host, "inventory_skills", lambda *args: [])
    monkeypatch.setattr(host.shared, "run_process", lambda *args, **kwargs:
                        {"status": "completed", "returncode": 0, "stdout": "version", "stderr": "", "seconds": 0})
    monkeypatch.setattr(host, "run_pair", lambda *args:
                        [{"engine": "codex", "task": task["id"], "trial": 1, "condition": condition,
                          "status": "completed", "outcome": {"status": "unknown"}, "behavior": {}}
                         for condition in ("baseline", "candidate")])
    output = tmp_path / "output"
    assert host.main(["--model", "fake", "--output", str(output), "--trials", "1",
                      "--tasks-dir", str(dataset), "--protocol", str(protocol)]) == 0
    import hashlib
    report = json.loads((output / "eval_report.json").read_text())
    assert selected == [(dataset.resolve(), [])]
    assert report["provenance"]["protocol_hash"] == hashlib.sha256(protocol.read_bytes()).hexdigest()
    assert report["provenance"]["protocol_path"] == str(protocol.resolve())


def test_missing_followup_protocol_rejects_before_process_or_output(tmp_path, monkeypatch):
    monkeypatch.setattr(host.shutil, "which", lambda *args, **kwargs: "/fake/codex")
    monkeypatch.setattr(host.shared, "run_process", lambda *args, **kwargs:
                        pytest.fail("No processes before protocol validation"))
    output = tmp_path / "output"
    with pytest.raises(SystemExit) as error:
        host.main(["--model", "fake", "--output", str(output),
                   "--protocol", str(tmp_path / "missing.json")])
    assert error.value.code == 2
    assert not output.exists()
