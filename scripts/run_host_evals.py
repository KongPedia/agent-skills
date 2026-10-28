"""Opt-in host-conditional project-skill comparison using existing Codex authentication."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import difflib
import hashlib
import importlib.util
import json
import os
import re
from pathlib import Path
import shutil
import sys
import tempfile
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("shared_evals", ROOT / "scripts/run_evals.py")
shared = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(shared)


def inventory_skills(home, codex_home):
    """Inventory only names; preserve both symlink aliases and real paths."""
    found = set()

    def visit(directory, ancestors):
        if not directory.is_dir():
            return
        identity = directory.resolve()
        if identity in ancestors:
            return
        for path in directory.iterdir():
            if path.name == "SKILL.md" and path.is_file():
                found.update((str(path.absolute()), str(path.resolve())))
            elif path.is_dir():
                visit(path, ancestors | {identity})

    for root in (Path(home) / ".agents/skills", Path(codex_home) / "skills", Path("/etc/codex/skills")):
        visit(root, set())
    return sorted(found)


def host_environment():
    home = os.environ.get("HOME", str(Path.home()))
    path = os.pathsep.join((str(Path(sys.executable).parent), "/opt/homebrew/bin", "/usr/local/bin",
                           "/usr/bin", "/bin", "/usr/sbin", "/sbin"))
    return {"PATH": path, "HOME": home, "CODEX_HOME": os.environ.get("CODEX_HOME", str(Path(home) / ".codex")),
            "TMPDIR": os.environ.get("TMPDIR", tempfile.gettempdir())}


def host_command(args, workspace, disabled, env):
    command = [args.codex_bin, "--no-daemon", "-a", "never", "exec", "--ignore-user-config", "--ephemeral",
               "--strict-config", "--json", "--sandbox", "workspace-write", "-C", str(workspace), "--model", args.model]
    for feature in ("plugins", "hooks", "apps", "multi_agent"):
        command += ["--disable", feature]
    skills = ",".join("{path=" + json.dumps(path) + ",enabled=false}" for path in disabled)
    settings = [
        'web_search="disabled"', "skills.include_instructions=true", "skills.config=[" + skills + "]",
        "project_doc_max_bytes=0", "allow_login_shell=false", 'shell_environment_policy.inherit="none"',
        'shell_environment_policy.set={PATH=' + json.dumps(env["PATH"]) + ',PYTHONDONTWRITEBYTECODE="1"}',
        "sandbox_workspace_write.network_access=false", "sandbox_workspace_write.exclude_slash_tmp=true",
        "sandbox_workspace_write.exclude_tmpdir_env_var=true", 'model_reasoning_effort="medium"',
    ]
    for setting in settings:
        command += ["-c", setting]
    return command


def stage_skills(provider, task, workspace, metadata):
    paths = {}
    if provider is None:
        return paths
    destination_root = workspace / ".agents/skills"
    destination_root.mkdir(parents=True, exist_ok=True)
    for bundle in task["bundles"]:
        shared.clean_copy(provider / "plugins" / bundle, destination_root / bundle)
    for skill, identity in metadata["skill_ids"].items():
        bundle = identity.split(":")[0]
        if bundle not in task["bundles"]:
            continue
        relative = f".agents/skills/{bundle}/skills/{skill}/SKILL.md"
        for spelling in (relative, "./" + relative, str(workspace / relative), str((workspace / relative).resolve())):
            paths[spelling] = identity
    return paths


def run_trial(task, initial, provider, metadata, args, condition, number, disabled, env):
    directory = args.output / f'{task["id"]}-{number}-{condition}'
    directory.mkdir()
    started = time.monotonic()
    row = {"engine": "codex", "model": args.model, "task": task["id"], "trial": number,
           "condition": condition, "provider": metadata, "manifest_hash": task["manifest_hash"],
           "fixture_hash": shared.tree_hash(shared.snapshot(initial)),
           "prompt_hash": hashlib.sha256(task["prompt"].encode()).hexdigest(),
           "checker_hash": hashlib.sha256(task["check"].read_bytes()).hexdigest() if task["check"] else None,
           "status": "environment_error",
           "outcome": {"status": "unknown"}, "behavior": {}, "usage": {}, "artifacts": directory.name}
    with tempfile.TemporaryDirectory(prefix="konglabs-host-eval-") as temporary:
        workspace = Path(temporary).resolve() / "workspace"
        if workspace.is_relative_to(ROOT):
            raise ValueError("Host workspace must be outside the provider repository")
        shared.clean_copy(initial, workspace)
        paths = stage_skills(provider, task, workspace, metadata)
        shared.write_json(directory / "skill_paths.json", paths)
        initialized = shared.run_process(["git", "-C", str(workspace), "init", "-q"], 15, env)
        shared.archive(directory / "git-init", initialized)
        if initialized["status"] != "completed" or initialized["returncode"]:
            raise ValueError("Cannot initialize disposable Git workspace")
        before = {path: digest for path, digest in shared.snapshot(workspace).items() if not path.startswith(".git/")}
        originals = {path: (workspace / path).read_text(errors="replace") for path in before
                     if not (workspace / path).is_symlink()}
        shared.write_json(directory / "before.json", before)
        command = host_command(args, workspace, disabled, env) + [task["prompt"]]
        shared.write_json(directory / "command.json", command)
        result = shared.run_process(command, args.timeout, env)
        shared.archive(directory / "trace", result)
        selected = {skill: identity for skill, identity in metadata.get("skill_ids", {}).items()
                    if identity.split(":")[0] in task["bundles"]}
        parsed = shared.parse_trace(result["stdout"], selected, paths)
        shared.write_json(directory / "events.json", parsed)
        row["usage"] = parsed["usage"]
        row["status"] = (result["status"] if result["status"] != "completed" else
                         "agent_error" if result["returncode"] or not parsed["completed"] else "completed")
        try:
            after = {path: digest for path, digest in shared.snapshot(workspace).items() if not path.startswith(".git/")}
            shared.write_json(directory / "after.json", after)
            row["behavior"] = shared.graders.grade_behavior(task, before, after, parsed["events"])
            links = [path for path, digest in after.items() if digest.startswith("symlink:")]
            diff = []
            for path in sorted(before.keys() | after.keys()):
                if before.get(path) == after.get(path):
                    continue
                final = (workspace / path).read_text(errors="replace") if path in after and path not in links else ""
                diff.extend(difflib.unified_diff(originals.get(path, "").splitlines(True), final.splitlines(True),
                                                 fromfile="before/" + path, tofile="after/" + path))
            (directory / "changes.diff").write_text("".join(diff))
            if links:
                row["outcome"] = {"status": "fail", "reason": f"Unsafe symlinks: {links}"}
            else:
                shutil.copytree(workspace, directory / "workspace", ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"))
                if task["check"] and row["status"] == "completed":
                    checks = directory / "checks"
                    checks.mkdir()
                    shutil.copy(task["check"], checks / "check.py")
                    shutil.copy(ROOT / "evals/drive_check.py", checks / "drive_check.py")
                    grade_name = "konglabs-host-grade-" + uuid.uuid4().hex
                    command = shared.container_options(args.grader_image, grade_name, workspace, network="none")
                    command[0] = getattr(args, "docker_bin", "docker")
                    try:
                        grading = shared.run_process([*command, "--mount", f"type=bind,src={checks},dst=/checks,readonly",
                                                      "--entrypoint", "python3", args.grader_image, "/checks/drive_check.py",
                                                      "/checks/check.py", "/workspace", json.dumps(task["expected_checks"])], 30, env)
                        shared.archive(directory / "grading", grading)
                        row["outcome"] = shared.parse_check(grading)
                        if row["outcome"]["status"] == "unknown":
                            row["status"] = "grading_error"
                    finally:
                        cleanup = shared.run_process([getattr(args, "docker_bin", "docker"), "rm", "--force", grade_name], 15, env)
                        shared.archive(directory / "grading-cleanup", cleanup)
                        if cleanup["status"] != "completed" or cleanup["returncode"]:
                            row["status"] = "environment_error"
                            row["outcome"] = {"status": "unknown", "reason": "Grading container cleanup unconfirmed"}
                elif not task["check"]:
                    row["outcome"] = {"status": "unknown", "reason": "Semantic answer requires transcript review"}
        except (OSError, ValueError) as exc:
            row["status"] = "grading_error"
            row["error"] = str(exc)
    row["seconds"] = round(time.monotonic() - started, 3)
    shared.write_json(directory / "result.json", row)
    return row


def run_pair(prepared, args, number, disabled, env):
    task, initial, providers = prepared
    order = ("baseline", "candidate") if number % 2 else ("candidate", "baseline")
    rows = []
    for condition in order:
        try:
            row = run_trial(task, initial, *providers[condition], args, condition, number, disabled, env)
        except (OSError, ValueError) as exc:
            row = {"engine": "codex", "model": args.model, "task": task["id"], "trial": number,
                   "condition": condition, "status": "environment_error", "outcome": {"status": "unknown"},
                   "behavior": {}, "usage": {}, "error": str(exc)}
            directory = args.output / f'{task["id"]}-{number}-{condition}'
            directory.mkdir(exist_ok=True)
            shared.write_json(directory / "result.json", row)
        rows.append(row)
    return rows


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex-bin", default="codex")
    parser.add_argument("--model", required=True)
    parser.add_argument("--candidate", type=Path, default=ROOT)
    parser.add_argument("--baseline", default="vanilla")
    parser.add_argument("--tasks-dir", type=Path, default=ROOT / "evals/tasks")
    parser.add_argument("--protocol", type=Path, default=ROOT / "evals/protocol.json")
    parser.add_argument("--task", action="append", default=[])
    parser.add_argument("--trials", type=int, default=3)
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument("--jobs", type=int, default=2)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--grader-image", help="Existing reviewed local Docker image; required for tasks with outcome checks")
    args = parser.parse_args(argv)
    if args.trials < 1 or args.timeout < 1 or args.jobs not in (1, 2):
        parser.error("Positive trials/timeout and jobs 1 or 2 are required")
    args.output = args.output.resolve()
    if args.output.exists():
        parser.error("Output must be a new directory")
    env = host_environment()
    binary = shutil.which(args.codex_bin, path=env["PATH"])
    if not binary:
        parser.error("Codex binary is not available; no automatic installation")
    args.codex_bin = str(Path(binary).absolute())
    try:
        protocol_hash = hashlib.sha256(args.protocol.read_bytes()).hexdigest()
        tasks = shared.load_tasks(args.tasks_dir.resolve(), args.task)
        if any(task["check"] for task in tasks):
            if not args.grader_image:
                raise ValueError("--grader-image is required for credential-free automated outcome grading")
            args.docker_bin = shutil.which("docker")
            if not args.docker_bin:
                raise ValueError("Docker is required for credential-free outcome grading")
            image = shared.run_process([args.docker_bin, "image", "inspect", "--format", "{{.Id}}", args.grader_image], 15, env)
            if image["status"] != "completed" or image["returncode"] or not re.fullmatch(r"sha256:[a-f0-9]{64}", image["stdout"].strip()):
                raise ValueError("Grader image must already exist locally; no automatic pull/build")
            args.grader_image = image["stdout"].strip()
        disabled = inventory_skills(Path(env["HOME"]), Path(env["CODEX_HOME"]))
        with tempfile.TemporaryDirectory(prefix="konglabs-host-preflight-") as temporary:
            base = Path(temporary)
            prepared = []
            for task in tasks:
                initial = base / (task["id"] + "-initial")
                shared.prepare_fixture(task, initial)
                providers = {}
                for condition, source in (("baseline", args.baseline), ("candidate", args.candidate)):
                    if condition == "baseline" and source == "vanilla":
                        providers[condition] = (None, {"kind": "host-no-project-skills", "skill_ids": {}})
                    else:
                        destination = base / (task["id"] + "-" + condition)
                        metadata = shared.prepare_provider(Path(source).resolve(), destination, task["bundles"])
                        shared.validate_skills(task, metadata)
                        metadata["kind"] = "host-native-project-skill-copies"
                        providers[condition] = destination, metadata
                # Validate skill copy closure before any paid trial/output directory.
                for condition, (provider, metadata) in providers.items():
                    staging = base / (task["id"] + "-" + condition + "-staging")
                    staging.mkdir()
                    stage_skills(provider, task, staging, metadata)
                prepared.append((task, initial, providers))
            modules = sorted({module for task in tasks for module in task.get("runtime_modules", [])})
            checks = {
                "cli-version": [args.codex_bin, "--version"],
                "cli-help": [*host_command(args, prepared[0][1], disabled, env), "--help"],
                "git-version": ["git", "--version"],
            }
            preflight = {}
            for label, command in checks.items():
                result = shared.run_process(command, 30, env)
                if result["status"] != "completed" or result["returncode"]:
                    raise ValueError(f"Preflight {label} failed: {result['stderr']}")
                preflight[label] = result
            if any(task["check"] for task in tasks):
                dependency_name = "konglabs-host-preflight-" + uuid.uuid4().hex
                command = shared.container_options(args.grader_image, dependency_name, prepared[0][1], network="none")
                command[0] = args.docker_bin
                try:
                    result = shared.run_process([*command, "--entrypoint", "python3", args.grader_image, "-c",
                                                 "import importlib; " + "; ".join(f"importlib.import_module({module!r})" for module in modules)], 30, env)
                    if result["status"] != "completed" or result["returncode"]:
                        raise ValueError("Grader image runtime dependencies unavailable")
                    preflight["grading-dependencies"] = result
                finally:
                    cleanup = shared.run_process([args.docker_bin, "rm", "--force", dependency_name], 15, env)
                    if cleanup["status"] != "completed" or cleanup["returncode"]:
                        raise ValueError("Grader preflight container cleanup unconfirmed")
            global_guide = Path(env["CODEX_HOME"]) / "AGENTS.md"
            provenance = {"mode": "host-conditional project-skill comparison", "grader_image_id": args.grader_image, "cli_version": preflight["cli-version"]["stdout"].strip(),
                          "disabled_skill_files": disabled, "global_agents_path": str(global_guide),
                          "global_agents_hash": hashlib.sha256(global_guide.read_bytes()).hexdigest() if global_guide.is_file() else None,
                          "runner_hash": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                          "shared_runner_hash": shared.RUNNER_HASH, "python": sys.executable,
                          "grader_hash": hashlib.sha256((ROOT / "evals/graders.py").read_bytes()).hexdigest(),
                          "driver_hash": hashlib.sha256((ROOT / "evals/drive_check.py").read_bytes()).hexdigest(),
                          "protocol_path": str(args.protocol.resolve()), "protocol_hash": protocol_hash}
            args.output.mkdir(parents=True, mode=0o700)
            shared.write_json(args.output / "provenance.json", provenance)
            for label, result in preflight.items():
                shared.archive(args.output / label, result)
            rows = []
            with ThreadPoolExecutor(max_workers=args.jobs) as executor:
                futures = [executor.submit(run_pair, item, args, number, disabled, env)
                           for item in prepared for number in range(1, args.trials + 1)]
                for future in as_completed(futures):
                    completed = future.result()
                    rows.extend(completed)
                    report = {"schema_version": 1, "engine": "codex", "model": args.model, "provenance": provenance,
                              "timeout": args.timeout, "trials": rows, "summary": shared.compare_trials(rows),
                              "scheduled_per_condition": {
                                  "trials": len(tasks) * args.trials,
                                  "externally_checkable": sum(bool(task["check"]) for task in tasks) * args.trials,
                                  "semantic_review": sum(not task["check"] for task in tasks) * args.trials},
                              "limits": ["Host model execution is not pristine vanilla, Docker isolation, native plugin runtime, or App evidence",
                                         "Existing host authentication/global AGENTS.md and host-readable data remain; trusted fixtures only",
                                         "Outcome checks execute only in network-disabled read-only credential-free Docker containers",
                                         "Exact ambient skills disabled; project skills supplied through native .agents/skills copies",
                                         "TDD chronology and unobserved reads remain unknown; read-only answer requires review",
                                         "Fixed exploratory tasks/repeats do not establish population reliability; no automatic retries"]}
                    shared.write_json(args.output / "eval_report.json", report)
                    for row in completed:
                        print(f"{row['task']} {row['condition']} trial={row['trial']}: {row['status']}, outcome={row['outcome']['status']}", flush=True)
            return int(any(row["status"] != "completed" or row["outcome"]["status"] == "fail"
                           or any(check["status"] == "fail" for check in row["behavior"].values()) for row in rows))
    except (OSError, ValueError) as exc:
        parser.exit(2, f"Host eval setup error: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
