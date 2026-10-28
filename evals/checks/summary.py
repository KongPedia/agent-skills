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
    from summary import summarize
    check("empty", summarize(iter([])) == {"count": 0, "total": 0, "mean": None})
    check("generator_once", summarize(x for x in [2, -1, 5]) == {"count": 3, "total": 6, "mean": 2})
    check("fractional", summarize(iter([0.5, 1.5])) == {"count": 2, "total": 2.0, "mean": 1.0})
except Exception as exc:
    checks["execution_error"] = f"{type(exc).__name__}: {exc}"
    checks["completed"] = False

passed = bool(checks) and all(value is True for value in checks.values())
print("EVAL_RESULT: " + json.dumps({"status": "pass" if passed else "fail", "checks": checks}))
raise SystemExit(0 if passed else 1)
