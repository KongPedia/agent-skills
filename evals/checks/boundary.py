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
    from copy import deepcopy
    from fastapi.testclient import TestClient
    from app import app, USERS
    USERS[1]["future_private_field"] = "must-not-leak"
    original = deepcopy(USERS)
    with TestClient(app) as client:
        response = client.get("/users/1")
        check("public_response", response.status_code == 200 and response.json() == {"id": 1, "name": "Ada"})
        missing = client.get("/users/999")
        check("not_found", missing.status_code == 404 and missing.json() == {"detail": "user not found"})
        schema = client.get("/openapi.json").json()
        response_schema = schema["paths"]["/users/{user_id}"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]
        if "$ref" in response_schema:
            response_schema = schema["components"]["schemas"][response_schema["$ref"].rsplit("/", 1)[-1]]
        check("public_response_model", set(response_schema.get("properties", {})) == {"id", "name"})
    check("source_unchanged", USERS == original)
except Exception as exc:
    checks["execution_error"] = f"{type(exc).__name__}: {exc}"
    checks["completed"] = False

passed = bool(checks) and all(value is True for value in checks.values())
print("EVAL_RESULT: " + json.dumps({"status": "pass" if passed else "fail", "checks": checks}))
raise SystemExit(0 if passed else 1)
