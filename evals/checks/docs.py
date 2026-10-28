"""Trusted external outcome check; never copied into the agent workspace."""
import json
from pathlib import Path
import sys

workspace = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(workspace))
checks = {}


def check(name, condition):
    checks[name] = bool(condition)


try:
    check("readme_exact", (workspace / "README.md").read_text() == "# Local utility\n\nRun with Python 3.11 or newer.\n")
except Exception as exc:
    checks["execution_error"] = f"{type(exc).__name__}: {exc}"
    checks["completed"] = False

passed = bool(checks) and all(value is True for value in checks.values())
print("EVAL_RESULT: " + json.dumps({"status": "pass" if passed else "fail", "checks": checks}))
raise SystemExit(0 if passed else 1)
