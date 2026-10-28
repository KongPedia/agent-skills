"""Validate check completion outside the interpreter importing generated code.

This blocks premature-exit/result-printing accidents, not hostile Python sharing
an interpreter with the checker. The nonce is a protocol guard, not a security boundary.
"""
import json
import os
from pathlib import Path
import secrets
import signal
import subprocess
import sys


WRAPPER = r'''
import json, runpy, sys
check, workspace, nonce = sys.argv[1:]
sys.argv = [check, workspace]
code = 0
try:
    runpy.run_path(check, run_name="__main__")
except SystemExit as exc:
    code = exc.code if isinstance(exc.code, int) else 0 if exc.code is None else 1
print("EVAL_COMPLETE: " + json.dumps({"nonce": nonce, "exit_code": code}), flush=True)
raise SystemExit(code)
'''


def emit_diagnostics(stdout, stderr):
    for name, output in (("stdout", stdout), ("stderr", stderr)):
        if output:
            excerpt = output[:8192]
            suffix = "\n[truncated]" if len(output) > len(excerpt) else ""
            print(f"Checker {name}:\n{excerpt}{suffix}", file=sys.stderr)


def run_check(check_path, workspace, expected_checks, timeout=20):
    def verdict(status, reason, checks=None):
        return {"status": status, "checks": checks or {"driver_integrity": False}, "reason": reason}

    if (not isinstance(expected_checks, list) or not expected_checks
            or any(not isinstance(name, str) or not name for name in expected_checks)
            or len(set(expected_checks)) != len(expected_checks)):
        return verdict("unknown", "Expected check names must be a nonempty unique string list.")
    check_path = Path(check_path).resolve()
    workspace = Path(workspace).resolve()
    if not check_path.is_file() or not workspace.is_dir():
        return verdict("unknown", "Missing trusted checker or workspace.")
    nonce = secrets.token_hex(24)
    try:
        process = subprocess.Popen(
            [sys.executable, "-I", "-B", "-c", WRAPPER, str(check_path), str(workspace), nonce],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="replace", start_new_session=True,
        )
    except OSError as exc:
        return verdict("unknown", f"Unable to start checker: {exc}")
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        stdout, stderr = process.communicate()
        emit_diagnostics(stdout, stderr)
        return verdict("fail", "Checker timeout; process group killed.")
    emit_diagnostics(stdout, stderr)
    markers = [line.removeprefix("EVAL_COMPLETE: ") for line in stdout.splitlines()
               if line.startswith("EVAL_COMPLETE: ")]
    if not markers:
        return verdict("fail", "Checker exited before trusted completion.")
    results = [line.removeprefix("EVAL_RESULT: ") for line in stdout.splitlines()
               if line.startswith("EVAL_RESULT: ")]
    if len(markers) != 1 or len(results) != 1:
        return verdict("unknown", "Expected exactly one result and one completion marker.")
    try:
        completion = json.loads(markers[0])
        result = json.loads(results[0])
    except (ValueError, TypeError):
        return verdict("unknown", "Malformed checker JSON.")
    if (not isinstance(completion, dict) or completion.get("nonce") != nonce
            or type(completion.get("exit_code")) is not int
            or completion["exit_code"] != process.returncode):
        return verdict("unknown", "Invalid checker completion marker.")
    if (not isinstance(result, dict) or result.get("status") not in ("pass", "fail")
            or not isinstance(result.get("checks"), dict)):
        return verdict("unknown", "Malformed checker result schema.")
    checks = result["checks"]
    if result["status"] == "pass":
        if (set(checks) != set(expected_checks) or not all(value is True for value in checks.values())
                or process.returncode != 0):
            return verdict("unknown", "Incomplete or inconsistent passing result.")
        return verdict("pass", "Trusted check completed with all expected criteria true.", checks)
    if process.returncode != 1 or not any(value is not True for value in checks.values()):
        return verdict("unknown", "Inconsistent failing result.")
    return verdict("fail", "Trusted check reported a failed criterion.", checks)


def main():
    try:
        if len(sys.argv) != 4:
            raise ValueError("usage: drive_check.py CHECK_PATH WORKSPACE EXPECTED_CHECKS_JSON")
        result = run_check(sys.argv[1], sys.argv[2], json.loads(sys.argv[3]))
    except (ValueError, TypeError) as exc:
        result = {"status": "unknown", "checks": {"driver_protocol": False}, "reason": str(exc)}
    print("EVAL_RESULT: " + json.dumps(result))
    return {"pass": 0, "fail": 1, "unknown": 2}[result["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
