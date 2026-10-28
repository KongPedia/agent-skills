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
    from points import deduct
    check("normal", deduct(10, 3) == 7)
    check("zero", deduct(0, 0) == 0 and deduct(5, 0) == 5)
    check("full_balance", deduct(7, 7) == 0)
    for balance, amount in [(3, 4), (5, -1), (-1, 0), (-2, -3)]:
        try:
            deduct(balance, amount)
        except ValueError:
            check(f"reject_{balance}_{amount}", True)
        else:
            check(f"reject_{balance}_{amount}", False)
except Exception as exc:
    checks["execution_error"] = f"{type(exc).__name__}: {exc}"
    checks["completed"] = False

passed = bool(checks) and all(value is True for value in checks.values())
print("EVAL_RESULT: " + json.dumps({"status": "pass" if passed else "fail", "checks": checks}))
raise SystemExit(0 if passed else 1)
