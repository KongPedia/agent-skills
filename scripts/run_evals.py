"""Opt-in, Docker-isolated CLI evals; ordinary pytest never invokes a model."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import shlex
import signal
import subprocess
import tempfile
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
RUNNER_HASH = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
CREDENTIALS = {"codex": "KONGLABS_EVAL_CODEX_API_KEY", "claude": "KONGLABS_EVAL_CLAUDE_API_KEY"}
spec = importlib.util.spec_from_file_location("eval_graders", ROOT / "evals/graders.py")
graders = importlib.util.module_from_spec(spec)
spec.loader.exec_module(graders)


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def snapshot(root):
    """Never follow agent-created links outside the workspace."""
    result = {}
    total = 0
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if any(part in {"__pycache__", ".pytest_cache"} for part in path.relative_to(root).parts):
            continue
        if path.is_symlink():
            result[relative] = "symlink:" + os.readlink(path)
        elif path.is_file():
            size = path.stat().st_size
            total += size
            if size > 8 * 1024 * 1024 or total > 64 * 1024 * 1024 or len(result) >= 4096:
                raise ValueError(f"Artifact too large: {relative}")
            result[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
        elif not path.is_dir():
            raise ValueError(f"Unsupported workspace file: {relative}")
    return result


def tree_hash(files):
    return hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()


def load_tasks(directory, selected=()):
    tasks = []
    for path in sorted(directory.glob("*.json")):
        task = json.loads(path.read_text())
        required = {"schema_version", "id", "prompt", "bundles", "required_skills", "forbidden_skills",
                    "fixture", "check", "allowed_paths", "forbid_commands", "tdd"}
        if not isinstance(task, dict) or not required <= task.keys() or task["schema_version"] != 1:
            raise ValueError(f"Invalid task schema: {path}")
        if not isinstance(task["id"], str) or not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,79}", task["id"]):
            raise ValueError(f"Unsafe task ID: {path}")
        if not isinstance(task["prompt"], str) or not task["prompt"].strip():
            raise ValueError(f"Empty prompt: {path}")
        for field in ("bundles", "required_skills", "forbidden_skills", "allowed_paths"):
            if not isinstance(task[field], list) or not all(isinstance(item, str) for item in task[field]):
                raise ValueError(f"Invalid {field}: {path}")
        if not all(re.fullmatch(r"[a-z][a-z0-9-]*", bundle) for bundle in task["bundles"]):
            raise ValueError(f"Unsafe bundle: {path}")
        if "session-guidance" in task["bundles"]:
            raise ValueError("Hook execution is outside this initial eval suite")
        if any(pattern.startswith("/") or ".." in Path(pattern).parts for pattern in task["allowed_paths"]):
            raise ValueError(f"Unsafe allowed path: {path}")
        for field in ("forbid_commands", "tdd"):
            if type(task[field]) is not bool:
                raise ValueError(f"Invalid {field}: {path}")
        if not isinstance(task.get("runtime_modules", []), list) or not all(isinstance(name, str) and re.fullmatch(r"[a-zA-Z_][a-zA-Z0-9_]*", name) for name in task.get("runtime_modules", [])):
            raise ValueError(f"Invalid runtime modules: {path}")
        if not isinstance(task.get("expected_checks"), list) or not all(isinstance(name, str) for name in task["expected_checks"]):
            raise ValueError(f"Invalid expected checks: {path}")
        if len(task["expected_checks"]) != len(set(task["expected_checks"])) or bool(task["check"]) != bool(task["expected_checks"]):
            raise ValueError(f"Checker and expected criteria disagree: {path}")
        # Dataset authors are trusted, but fixture/check closure prevents accidental private-file mounts.
        for field in ("fixture", "check"):
            if field == "check" and task[field] is None:
                continue
            target = (path.parent / task[field]).resolve()
            if not target.is_relative_to(directory.parent.resolve()):
                raise ValueError(f"{field} escapes dataset: {path}")
            if (field == "fixture" and not target.is_dir()) or (field == "check" and not target.is_file()):
                raise ValueError(f"Missing {field}: {path}")
            task[field] = target
        task["manifest_hash"] = hashlib.sha256(path.read_bytes()).hexdigest()
        tasks.append(task)
    ids = [task["id"] for task in tasks]
    if len(ids) != len(set(ids)) or set(selected) - set(ids):
        raise ValueError("Duplicate or unknown selected task IDs")
    tasks = [task for task in tasks if not selected or task["id"] in selected]
    if not tasks:
        raise ValueError("No tasks selected")
    return tasks


def parse_trace(text, skill_ids, installed_skill_paths=None):
    events, errors, usage, pending = [], [], {}, {}
    read_paths = {f'/provider/plugins/{identity.split(":")[0]}/skills/{name}/SKILL.md': identity
                  for name, identity in skill_ids.items()}
    read_paths.update({path: identity for path, identity in (installed_skill_paths or {}).items()
                       if identity in skill_ids.values()})
    completed = False

    def observed_read(command, output, exit_code):
        # shortcut: conservative literal file reads only; indirect/dynamic reads need transcript review.
        if exit_code != 0 or not output:
            return
        try:
            words = shlex.split(command)
            if len(words) == 3 and Path(words[0]).name in {"bash", "zsh", "sh"} and words[1] in {"-c", "-lc"}:
                words = shlex.split(words[2])
        except ValueError:
            return
        if not words:
            return
        program = Path(words[0]).name
        if program == "cat" and len(words) > 1:
            if all(path in read_paths for path in words[1:]):
                for path in words[1:]:
                    events.append({"type": "skill_read", "skill": read_paths[path], "evidence": "literal read command; not adherence proof"})
            return
        simple_read = len(words) == 2 and program in {"cat", "head", "tail", "Read"}
        ranged_read = (len(words) == 4 and words[1] == "-n"
                       and ((program == "sed" and re.fullmatch(r"\d+(,\d+)?p", words[2]))
                            or (program in {"head", "tail"} and words[2].isdigit())))
        if not (simple_read or ranged_read):
            return
        if words[-1] in read_paths:
            events.append({"type": "skill_read", "skill": read_paths[words[-1]], "evidence": "literal read command; not adherence proof"})

    for number, line in enumerate(text.split("\n"), 1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
            if not isinstance(event, dict):
                raise ValueError("event must be an object")
        except (ValueError, TypeError) as exc:
            errors.append(f"Line {number}: {exc}")
            continue
        kind = event.get("type")
        if kind in {"error", "turn.failed"} or (kind == "result" and event.get("is_error")):
            errors.append(f"CLI event failure: {kind}")
        if kind == "turn.completed":
            completed = True
            usage.update(event.get("usage") or {})
        if kind == "item.completed":
            item = event.get("item", {})
            if not isinstance(item, dict):
                errors.append("Invalid item schema")
                continue
            if item.get("type") == "command_execution":
                command, output, code = item.get("command", ""), item.get("aggregated_output", ""), item.get("exit_code")
                events.append({"type": "command", "command": command, "exit_code": code, "output": output})
                observed_read(command, output, code)
            elif item.get("type") == "agent_message":
                events.append({"type": "message", "text": item.get("text", "")})
        message = event.get("message", {})
        if kind in {"assistant", "user"} and isinstance(message, dict):
            for block in message.get("content", []) if isinstance(message.get("content"), list) else []:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "text":
                    events.append({"type": "message", "text": block.get("text", "")})
                elif block.get("type") == "tool_use":
                    name, data = block.get("name", ""), block.get("input", {})
                    if not isinstance(data, dict):
                        errors.append("Invalid tool input schema")
                        continue
                    pending[block.get("id")] = (name, data)
                    if name == "Bash":
                        events.append({"type": "command", "command": data.get("command", ""), "exit_code": None, "output": ""})
                elif block.get("type") == "tool_result":
                    name, data = pending.get(block.get("tool_use_id"), ("", {}))
                    output = str(block.get("content", ""))
                    if name == "Read":
                        observed_read("Read " + data.get("file_path", ""), output, 1 if block.get("is_error") else 0)
                    elif name == "Bash":
                        observed_read(data.get("command", ""), output, 1 if block.get("is_error") else 0)
                    elif name == "Skill" and output and not block.get("is_error"):
                        identity = data.get("skill")
                        identity = skill_ids.get(identity, identity)
                        if identity in skill_ids.values():
                            events.append({"type": "skill_read", "skill": identity, "evidence": "successful native Skill tool result; not adherence proof"})
        if kind == "result":
            completed = not event.get("is_error", False)
            usage.update(event.get("usage") or {})
            for key in ("total_cost_usd", "duration_ms", "num_turns"):
                if key in event:
                    usage[key] = event[key]
    return {"events": events, "errors": errors, "usage": usage, "completed": completed and not errors}


def compare_trials(trials):
    conditions = {}
    for condition in ("baseline", "candidate"):
        rows = [row for row in trials if row["condition"] == condition]
        known = [row for row in rows if row["status"] == "completed" and row["outcome"]["status"] in {"pass", "fail"}]
        passes = sum(row["outcome"]["status"] == "pass" for row in known)
        conditions[condition] = {"trials": len(rows), "trial_statuses": dict(Counter(row["status"] for row in rows)),
                                 "outcome_known": len(known), "outcome_pass": passes,
                                 "outcome_unknown": len(rows) - len(known),
                                 "outcome_rate": passes / len(known) if known else None}
        names = {name for row in rows for name in row.get("behavior", {})}
        conditions[condition]["behavior"] = {name: dict(Counter(row.get("behavior", {}).get(name, {}).get("status", "unknown") for row in rows)) for name in sorted(names)}
    pairs = {}
    for row in trials:
        pairs.setdefault((row["engine"], row["task"], row["trial"]), {})[row["condition"]] = row
    paired = dict.fromkeys(("comparable", "improved", "regressed", "unchanged", "unknown"), 0)
    behavior = {}
    for pair in pairs.values():
        if set(pair) != {"baseline", "candidate"} or any(row["status"] != "completed" or row["outcome"]["status"] not in {"pass", "fail"} for row in pair.values()):
            paired["unknown"] += 1
            continue
        before, after = (pair[key]["outcome"]["status"] == "pass" for key in ("baseline", "candidate"))
        paired["comparable"] += 1
        paired["improved" if after > before else "regressed" if after < before else "unchanged"] += 1
    names = {name for row in trials for name in row.get("behavior", {})}
    for name in sorted(names):
        counts = dict.fromkeys(("comparable", "improved", "regressed", "unchanged", "unknown"), 0)
        for pair in pairs.values():
            checks = [pair.get(condition, {}).get("behavior", {}).get(name, {}).get("status", "unknown") for condition in ("baseline", "candidate")]
            if set(pair) != {"baseline", "candidate"} or any(row["status"] != "completed" for row in pair.values()) or any(status not in {"pass", "fail"} for status in checks):
                counts["unknown"] += 1
            else:
                before, after = (status == "pass" for status in checks)
                counts["comparable"] += 1
                counts["improved" if after > before else "regressed" if after < before else "unchanged"] += 1
        behavior[name] = counts
    return {"conditions": conditions, "paired_outcomes": paired, "paired_behavior": behavior}


def run_process(argv, timeout, env=None):
    """Bound wall time and retained output; kill the client process group on limit."""
    started = time.monotonic()
    with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        process = subprocess.Popen(argv, stdout=out, stderr=err, env=env, start_new_session=True)
        status = "completed"
        while process.poll() is None:
            if time.monotonic() - started > timeout:
                status = "timeout"
            elif any(os.fstat(stream.fileno()).st_size > 8 * 1024 * 1024 for stream in (out, err)):
                status = "output_limit"
            if status != "completed":
                os.killpg(process.pid, signal.SIGKILL)
                break
            try:
                process.wait(timeout=0.1)
            except subprocess.TimeoutExpired:
                pass
        process.wait()
        if status == "completed" and any(os.fstat(stream.fileno()).st_size > 8 * 1024 * 1024 for stream in (out, err)):
            status = "output_limit"
        out.seek(0)
        err.seek(0)
        return {"status": status, "returncode": process.returncode,
                "stdout": out.read(8 * 1024 * 1024).decode(errors="replace"),
                "stderr": err.read(8 * 1024 * 1024).decode(errors="replace"),
                "seconds": round(time.monotonic() - started, 3)}


def archive(path, result, secrets=()):
    sensitive = {"access_token", "refresh_token", "id_token", "api_key", "openai_api_key", "codex_api_key", "anthropic_api_key"}

    def redact(value):
        if isinstance(value, dict):
            return {key: "[REDACTED]" if key.lower() in sensitive else redact(item) for key, item in value.items()}
        if isinstance(value, list):
            return [redact(item) for item in value]
        if isinstance(value, str):
            value = re.sub(r'(?i)("(?:access_token|refresh_token|id_token|api_key|openai_api_key|codex_api_key|anthropic_api_key)"\s*:\s*")[^"]*(")', r'\1[REDACTED]\2', value)
            return re.sub(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+", "[REDACTED]", value)
        return value

    for field in ("stdout", "stderr"):
        content = result[field]
        for secret in secrets:
            if secret:
                content = content.replace(secret, "[REDACTED]")
        lines = []
        for line in content.split("\n"):
            try:
                lines.append(json.dumps(redact(json.loads(line)), ensure_ascii=False))
            except ValueError:
                lines.append(redact(line))
        content = "\n".join(lines)
        path.with_suffix("." + field).write_text(content)
        result[field] = content


def clean_copy(source, destination):
    files = snapshot(source)
    if any(value.startswith("symlink:") for value in files.values()):
        raise ValueError(f"Symlinks are not permitted in eval inputs: {source}")
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))


def prepare_fixture(task, destination):
    clean_copy(task["fixture"], destination)


def prepare_provider(source, destination, bundles):
    catalog = json.loads((source / "catalog.json").read_text())
    identities = {entry["id"]: entry for entry in catalog["plugins"]}
    if set(bundles) - identities.keys():
        raise ValueError("Task selects unknown bundles")
    for bundle in bundles:
        if set(identities[bundle]["requires"]) - set(bundles):
            raise ValueError(f"Task missing dependencies of {bundle}")
    destination.mkdir()
    shutil.copy(source / "catalog.json", destination / "catalog.json")
    for directory in ("plugins", ".agents/plugins", ".claude-plugin"):
        clean_copy(source / directory, destination / directory)
    actual = snapshot(destination)
    revision = run_process(["git", "-C", str(source), "rev-parse", "HEAD"], 10)
    dirty = run_process(["git", "-C", str(source), "status", "--porcelain"], 10)
    return {"revision": revision["stdout"].strip() if revision["returncode"] == 0 else None,
            "dirty": bool(dirty["stdout"].strip()) if dirty["returncode"] == 0 else None,
            "payload_hash": tree_hash(actual), "version": catalog["version"],
            "skill_ids": {name: f'{entry["id"]}:{name}' for entry in catalog["plugins"] for name in entry["skills"]}}


def validate_skills(task, metadata):
    available = {identity for identity in metadata["skill_ids"].values() if identity.split(":")[0] in task["bundles"]}
    if (set(task["required_skills"]) | set(task["forbidden_skills"])) - available:
        raise ValueError(f'Unknown or unavailable skill IDs in {task["id"]}')


def agent_command(engine, model, prompt, bundles, with_skills):
    if engine == "codex":
        return ["codex", "exec", "--json", "--ephemeral", "--skip-git-repo-check", "--dangerously-bypass-approvals-and-sandbox", "-C", "/workspace", "--model", model, prompt]
    command = ["claude", "-p", prompt, "--model", model, "--output-format", "stream-json", "--verbose", "--dangerously-skip-permissions"]
    if with_skills:
        for bundle in bundles:
            command += ["--plugin-dir", "/provider/plugins/" + bundle]
    return command


def container_options(image, name, workspace, *, network):
    uid, gid = os.getuid() or 1000, os.getgid() or 1000
    return ["docker", "run", "--pull=never", "--name", name, "--init", "--read-only", "--user", f"{uid}:{gid}",
            "--cap-drop=ALL", "--security-opt=no-new-privileges", "--pids-limit=128", "--memory=2g", "--cpus=2",
            "--network", network, "--tmpfs", "/tmp:rw,nosuid,nodev,size=256m,mode=1777",
            "--tmpfs", f"/home/eval:rw,nosuid,nodev,size=256m,uid={uid},gid={gid},mode=0700",
            "--env", "HOME=/home/eval", "--env", "CODEX_HOME=/home/eval/.codex",
            "--env", "CLAUDE_CONFIG_DIR=/home/eval/.claude", "--env", "PYTHONDONTWRITEBYTECODE=1",
            "--workdir", "/workspace", "--mount", f"type=bind,src={workspace},dst=/workspace" + (",readonly" if network == "none" else "")]


def parse_check(result):
    if result["status"] != "completed":
        return {"status": "unknown", "reason": "Grading " + result["status"]}
    markers = [line.removeprefix("EVAL_RESULT: ") for line in result["stdout"].splitlines() if line.startswith("EVAL_RESULT: ")]
    if len(markers) != 1:
        return {"status": "unknown", "reason": "Missing or ambiguous grader result"}
    try:
        check = json.loads(markers[0])
        if check["status"] not in {"pass", "fail", "unknown"} or result["returncode"] != {"pass": 0, "fail": 1, "unknown": 2}[check["status"]]:
            raise ValueError("exit/result mismatch")
        return check
    except (ValueError, KeyError, TypeError):
        return {"status": "unknown", "reason": "Invalid grader result"}


def run_trial(task, initial, provider, metadata, args, condition, number):
    directory = args.output / f'{task["id"]}-{number}-{condition}'
    directory.mkdir()
    workspace = directory / "workspace"
    clean_copy(initial, workspace)
    before = snapshot(workspace)
    if os.getuid() == 0:
        for path in [workspace, *workspace.rglob("*")]:
            os.chown(path, 1000, 1000)
    write_json(directory / "before.json", before)
    row = {"engine": args.engine, "model": args.model, "task": task["id"], "trial": number,
           "condition": condition, "manifest_hash": task["manifest_hash"], "fixture_hash": tree_hash(before),
           "provider": metadata, "checker_hash": hashlib.sha256(task["check"].read_bytes()).hexdigest() if task["check"] else None,
           "runner_hash": RUNNER_HASH,
           "grader_hash": hashlib.sha256((ROOT / "evals/graders.py").read_bytes()).hexdigest(),
           "driver_hash": hashlib.sha256((ROOT / "evals/drive_check.py").read_bytes()).hexdigest(),
           "status": "environment_error", "outcome": {"status": "unknown"}, "behavior": {}}
    name = "konglabs-eval-" + uuid.uuid4().hex
    grade_name = name + "-grade"
    started = time.monotonic()
    parsed = {"events": [], "usage": {}, "errors": []}
    stopped = False
    row["auth_mode"] = "dedicated-api-key"
    secret = os.environ[CREDENTIALS[args.engine]]
    env = {**os.environ, ("CODEX_API_KEY" if args.engine == "codex" else "ANTHROPIC_API_KEY"): secret}
    key = "CODEX_API_KEY" if args.engine == "codex" else "ANTHROPIC_API_KEY"

    def step(label, argv, timeout=30, process_env=None):
        remaining = args.timeout - (time.monotonic() - started)
        result = run_process(argv, max(0.01, min(remaining, timeout)), env=process_env)
        archive(directory / label, result, (secret,))
        if result["status"] != "completed" or result["returncode"]:
            row["status"] = result["status"] if result["status"] != "completed" else "environment_error"
            raise RuntimeError(f'{label}: {row["status"]}, exit={result["returncode"]}')
        return result

    try:
        create = container_options(args.image, name, workspace, network="bridge")
        if provider:
            create += ["--mount", f"type=bind,src={provider},dst=/provider,readonly"]
        step("container", [*create, "--detach", "--entrypoint", "sleep", args.image, str(args.timeout + 60)])
        step("home", ["docker", "exec", name, "python3", "-c", "from pathlib import Path; [Path(p).mkdir(parents=True,exist_ok=True) for p in ('/home/eval/.codex','/home/eval/.claude')]"])
        version = step("version", ["docker", "exec", name, args.engine, "--version"])
        row["cli_version"] = version["stdout"].strip()
        step("dependencies", ["docker", "exec", name, "python3", "-c", "import importlib; " + "; ".join(f"importlib.import_module({module!r})" for module in task.get("runtime_modules", []))])
        installed_skill_paths = {}
        selected_ids = {skill: identity for skill, identity in metadata.get("skill_ids", {}).items()
                        if identity.split(":")[0] in task["bundles"]}
        if provider and args.engine == "codex":
            step("marketplace", ["docker", "exec", name, "codex", "plugin", "marketplace", "add", "/provider", "--json"])
            for bundle in task["bundles"]:
                step("install-" + bundle, ["docker", "exec", name, "codex", "plugin", "add", bundle + "@konglabs-agent-skills", "--json"])
            expected_hashes = {}
            for skill, identity in selected_ids.items():
                bundle = identity.split(":")[0]
                path = f'/home/eval/.codex/plugins/cache/konglabs-agent-skills/{bundle}/{metadata["version"]}/skills/{skill}/SKILL.md'
                source = provider / "plugins" / bundle / "skills" / skill / "SKILL.md"
                expected_hashes[path] = hashlib.sha256(source.read_bytes()).hexdigest()
                installed_skill_paths[path] = identity
            probe = step("installed-skills", ["docker", "exec", name, "python3", "-c",
                         "import hashlib,json,sys; from pathlib import Path; "
                         "print(json.dumps({p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in json.loads(sys.argv[1])}))",
                         json.dumps(list(expected_hashes))])
            if json.loads(probe["stdout"]) != expected_hashes:
                raise ValueError("Installed skill attestation does not match selected provider bytes")
            row["installed_skill_paths"] = installed_skill_paths
        command = ["docker", "exec", "--env", key, name,
                   *agent_command(args.engine, args.model, task["prompt"], task["bundles"], bool(provider))]
        write_json(directory / "command.json", command)
        result = run_process(command, max(0.01, args.timeout - (time.monotonic() - started)), env)
        archive(directory / "trace", result, (secret,))
        parsed = parse_trace(result["stdout"], selected_ids, installed_skill_paths)
        row["status"] = result["status"] if result["status"] != "completed" else "agent_error" if result["returncode"] or not parsed["completed"] else "completed"
    except (RuntimeError, OSError, ValueError) as exc:
        row["error"] = str(exc).replace(secret, "[REDACTED]") if secret else str(exc)
    finally:
        # Stop all agent processes before inspecting or grading their final files.
        cleanup = run_process(["docker", "rm", "--force", name], 15)
        archive(directory / "cleanup", cleanup, (secret,))
        stopped = cleanup["status"] == "completed" and cleanup["returncode"] == 0
        if not stopped:
            row["status"] = "environment_error"
            row["error"] = "Agent container cleanup could not be confirmed; grading blocked. Inspect " + name
    try:
        if not stopped:
            row["seconds"] = round(time.monotonic() - started, 3)
            write_json(directory / "result.json", row)
            return row
        after = snapshot(workspace)
        write_json(directory / "after.json", after)
        row["behavior"] = graders.grade_behavior(task, before, after, parsed["events"])
        links = [path for path, value in after.items() if value.startswith("symlink:")]
        if links:
            row["outcome"] = {"status": "fail", "reason": f"Unsafe symlinks: {links}"}
        elif task["check"] and row["status"] == "completed":
            check_root = directory / "checks"
            check_root.mkdir()
            shutil.copy(task["check"], check_root / "check.py")
            shutil.copy(ROOT / "evals/drive_check.py", check_root / "drive_check.py")
            command = container_options(args.image, grade_name, workspace, network="none")
            try:
                result = run_process([*command, "--mount", f"type=bind,src={check_root},dst=/checks,readonly", "--entrypoint", "python3", args.image, "/checks/drive_check.py", "/checks/check.py", "/workspace", json.dumps(task["expected_checks"])], 30)
                archive(directory / "grading", result, (secret,))
                row["outcome"] = parse_check(result)
                if row["outcome"]["status"] == "unknown":
                    row["status"] = "grading_error"
            finally:
                cleanup = run_process(["docker", "rm", "--force", grade_name], 15)
                archive(directory / "grading-cleanup", cleanup, (secret,))
                if cleanup["status"] != "completed" or cleanup["returncode"]:
                    row["status"] = "environment_error"
                    row["error"] = "Grading container cleanup could not be confirmed: " + grade_name
        elif not task["check"]:
            row["outcome"] = {"status": "unknown", "reason": "Semantic answer correctness requires transcript review"}
        write_json(directory / "events.json", parsed)
        row["usage"] = parsed["usage"]
    except (OSError, ValueError) as exc:
        row["status"] = "grading_error"
        row["error"] = str(exc).replace(secret, "[REDACTED]") if secret else str(exc)
    row["seconds"] = round(time.monotonic() - started, 3)
    row["artifacts"] = directory.name
    write_json(directory / "result.json", row)
    return row


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks", type=Path, default=ROOT / "evals/tasks")
    parser.add_argument("--task", action="append", default=[])
    parser.add_argument("--engine", choices=CREDENTIALS, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--image", required=True, help="Existing reviewed Docker image containing CLIs and evaluation dependencies")
    parser.add_argument("--candidate", type=Path, default=ROOT)
    parser.add_argument("--baseline", default="vanilla", help="vanilla or reviewed prior provider checkout")
    parser.add_argument("--output", type=Path, required=True, help="New artifact directory; never overwritten")
    parser.add_argument("--trials", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=300)
    args = parser.parse_args(argv)
    if args.trials < 1 or args.timeout < 1 or args.image.startswith("-"):
        parser.error("Positive trials/timeout and a valid image are required")
    args.output = args.output.resolve()
    if args.output.exists():
        parser.error("Output directory already exists; choose a fresh directory")
    if not os.environ.get(CREDENTIALS[args.engine]):
        parser.error(f"Set {CREDENTIALS[args.engine]} to a dedicated, budget-limited eval key; personal auth is never copied")
    try:
        tasks = load_tasks(args.tasks.resolve(), args.task)
        image = run_process(["docker", "image", "inspect", "--format", "{{.Id}}", args.image], 15)
        if image["status"] != "completed" or image["returncode"] or not re.fullmatch(r"sha256:[a-f0-9]{64}", image["stdout"].strip()):
            raise ValueError("Reviewed image must already exist in the current Docker daemon; no automatic pull/build")
        args.image = image["stdout"].strip()
        rows = []
        with tempfile.TemporaryDirectory(prefix="konglabs-eval-") as temp:
            base = Path(temp)
            prepared = []
            for task in tasks:
                initial = base / (task["id"] + "-fixture")
                prepare_fixture(task, initial)
                providers = {}
                for condition, source in (("baseline", args.baseline), ("candidate", args.candidate)):
                    if condition == "baseline" and source == "vanilla":
                        providers[condition] = (None, {"kind": "vanilla", "skill_ids": {}})
                    else:
                        destination = base / (task["id"] + "-" + condition)
                        metadata = prepare_provider(Path(source).resolve(), destination, task["bundles"])
                        validate_skills(task, metadata)
                        metadata["kind"] = "native-plugin-payload"
                        providers[condition] = destination, metadata
                prepared.append((task, initial, providers))
            # Reject the entire suite before the first paid call, not midway through earlier tasks.
            args.output.mkdir(parents=True, mode=0o700)
            for task, initial, providers in prepared:
                for number in range(1, args.trials + 1):
                    # Alternate order so a consistently second candidate is not a time/order advantage.
                    order = ("baseline", "candidate") if number % 2 else ("candidate", "baseline")
                    for condition in order:
                        provider, metadata = providers[condition]
                        row = run_trial(task, initial, provider, metadata, args, condition, number)
                        rows.append(row)
                        report = {"schema_version": 1, "engine": args.engine, "model": args.model, "image_id": args.image,
                                  "timeout": args.timeout, "trials": rows, "summary": compare_trials(rows),
                                  "limits": ["Exploratory fixed-task results, not population reliability or App evidence", "TDD chronology and unobserved invocation remain unknown", "Model container has network; grading container has none; review image and use only disposable eval credentials"]}
                        write_json(args.output / "eval_report.json", report)
                        print(f'{task["id"]} {condition} trial={number}: {row["status"]}, outcome={row["outcome"]["status"]}', flush=True)
        return 1 if any(row["status"] != "completed" or row["outcome"]["status"] == "fail" or any(check["status"] == "fail" for check in row["behavior"].values()) for row in rows) else 0
    except (OSError, ValueError) as exc:
        if args.output.is_dir():
            write_json(args.output / "setup_error.json", {"status": "environment_error", "reason": str(exc)})
        parser.exit(2, f"Eval setup error: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
