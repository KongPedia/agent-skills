"""External behavioral oracle; not available in the model workspace."""
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(sys.argv[1]).resolve()))
checks = {}
def check(name, fn):
    try:
        checks[name] = bool(fn())
    except Exception:
        checks[name] = False


checks = dict.fromkeys(['no_import_acquisition', 'no_startup_acquisition', 'response_1', 'cleanup_1', 'response_2', 'cleanup_2', 'response_3', 'cleanup_3', 'response_4', 'cleanup_4', 'no_shutdown_release', 'replacement_response_1', 'replacement_cleanup_1', 'replacement_response_2', 'replacement_cleanup_2', 'replacement_response_3', 'replacement_cleanup_3', 'replacement_service_called', 'original_resource_unchanged', 'replacement_no_shutdown_release'], False)
try:
    from fastapi.testclient import TestClient
    import app as module
    check("no_import_acquisition",lambda:(module.resource.opened,module.resource.closed,module.resource.active)==(0,0,0))
    with TestClient(module.app,raise_server_exceptions=False) as client:
        check("no_startup_acquisition",lambda:(module.resource.opened,module.resource.closed,module.resource.active)==(0,0,0))
        for index,job in enumerate(["one","missing","broken","two"],1):
            response=client.get("/jobs/"+job)
            expected_status=404 if job=="missing" else 500 if job=="broken" else 200
            check("response_"+str(index),lambda:response.status_code==expected_status and (job=="broken" or response.json()==({"detail":"job not found"} if job=="missing" else {"id":job,"active":1})))
            check("cleanup_"+str(index),lambda:(module.resource.opened,module.resource.closed,module.resource.active)==(index,index,0))
    check("no_shutdown_release",lambda:(module.resource.opened,module.resource.closed,module.resource.active)==(4,4,0))
    original_resource = module.resource
    class ReplacementResource:
        def __init__(self):
            self.opened = self.closed = self.active = 0
        async def acquire(self):
            self.opened += 1
            self.active += 1
            return self
        async def release(self):
            self.closed += 1
            self.active -= 1
    replacement = ReplacementResource()
    calls = []
    class ReplacementService:
        async def lookup(self, job_id):
            calls.append(job_id)
            if job_id == "external-missing":
                raise LookupError(job_id)
            if job_id == "external-broken":
                raise RuntimeError("replacement backend failure")
            return {"id": job_id, "active": replacement.active}
    module.resource = replacement
    module.service = ReplacementService()
    with TestClient(module.app, raise_server_exceptions=False) as client:
        for index, job in enumerate(["external-success", "external-missing", "external-broken"], 1):
            response = client.get("/jobs/" + job)
            expected_status = 404 if job == "external-missing" else 500 if job == "external-broken" else 200
            expected_body = {"detail": "job not found"} if job == "external-missing" else {"id": job, "active": 1}
            check("replacement_response_" + str(index), lambda: response.status_code == expected_status
                  and (job == "external-broken" or response.json() == expected_body))
            check("replacement_cleanup_" + str(index), lambda: (replacement.opened, replacement.closed, replacement.active) == (index, index, 0))
    check("replacement_service_called", lambda: calls == ["external-success", "external-missing", "external-broken"])
    check("original_resource_unchanged", lambda: (original_resource.opened, original_resource.closed, original_resource.active) == (4, 4, 0))
    check("replacement_no_shutdown_release", lambda: (replacement.opened, replacement.closed, replacement.active) == (3, 3, 0))

except Exception:
    pass

passed = bool(checks) and all(value is True for value in checks.values())
print("EVAL_RESULT: " + json.dumps({"status": "pass" if passed else "fail", "checks": checks}))
raise SystemExit(0 if passed else 1)
