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
    from fastapi.testclient import TestClient
    from app import app, resource
    check("no_import_acquisition", (resource.opened, resource.closed, resource.active) == (0, 0, 0))
    with TestClient(app) as client:
        check("no_startup_acquisition", (resource.opened, resource.closed, resource.active) == (0, 0, 0))
        for index, fail in enumerate([False, True, False, True], start=1):
            response = client.get("/work", params={"fail": str(fail).lower()})
            check(f"response_{index}", response.status_code == (409 if fail else 200)
                  and response.json() == ({"detail": "requested failure"} if fail else {"active": 1}))
            check(f"cleanup_{index}", (resource.opened, resource.closed, resource.active) == (index, index, 0))
    check("no_shutdown_double_release", (resource.opened, resource.closed, resource.active) == (4, 4, 0))
except Exception as exc:
    checks["execution_error"] = f"{type(exc).__name__}: {exc}"
    checks["completed"] = False

passed = bool(checks) and all(value is True for value in checks.values())
print("EVAL_RESULT: " + json.dumps({"status": "pass" if passed else "fail", "checks": checks}))
raise SystemExit(0 if passed else 1)
