"""Offline oracle validation; reference repairs are never mounted for agents.

uv run --locked --with fastapi==0.162.0 --with httpx==0.28.1 python evals/followup/selfcheck.py
"""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
REFERENCES = {
"inventory-reservation": '''def reserve(stock, lines):
    demand = {}
    for sku, quantity in lines:
        if type(quantity) is not int or quantity <= 0:
            raise ValueError("positive integer required")
        demand[sku] = demand.get(sku, 0) + quantity
    result = stock.copy()
    for sku, quantity in demand.items():
        if sku not in stock:
            raise KeyError(sku)
        if quantity > stock[sku]:
            raise ValueError("insufficient stock")
        result[sku] -= quantity
    return result
''',
"idempotency-ledger": '''from copy import deepcopy
class Ledger:
    def __init__(self, ttl, capacity):
        if any(type(value) is not int or value <= 0 for value in (ttl, capacity)):
            raise ValueError("positive integers required")
        self.ttl, self.capacity = ttl, capacity
        self.entries = {}
    def claim(self, key, payload, now):
        self.entries = {k: entry for k, entry in self.entries.items() if entry[0] > now}
        if key in self.entries:
            if self.entries[key][1] != payload:
                raise ValueError("conflicting replay")
            return False
        if len(self.entries) >= self.capacity:
            raise OverflowError("full")
        self.entries[key] = (now + self.ttl, deepcopy(payload))
        return True
''',
"request-resource-errors": '''from fastapi import Depends, HTTPException
async def managed_resource():
    handle = await resource.acquire()
    try:
        yield handle
    finally:
        await handle.release()
app = FastAPI()
@app.get("/jobs/{job_id}")
async def get_job(job_id: str, handle=Depends(managed_resource)):
    try:
        return await service.lookup(job_id)
    except LookupError:
        raise HTTPException(status_code=404, detail="job not found")
''',
"nested-public-boundary": '''from fastapi import HTTPException, Query
from pydantic import BaseModel
class Contact(BaseModel):
    city: str
class Customer(BaseModel):
    id: int
    name: str
    contact: Contact
class CustomerPage(BaseModel):
    items: list[Customer]
    total: int
app = FastAPI()
@app.get("/customers", response_model=CustomerPage)
def list_customers(offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=50)):
    records = [CUSTOMERS[key] for key in sorted(CUSTOMERS)]
    return {"items": records[offset:offset+limit], "total": len(records)}
@app.get("/customers/{customer_id}", response_model=Customer)
def get_customer(customer_id: int):
    if customer_id not in CUSTOMERS:
        raise HTTPException(status_code=404, detail="customer not found")
    return CUSTOMERS[customer_id]
''',
}


def run_check(manifest, workspace):
    checker = ROOT / manifest["check"].removeprefix("../")
    result = subprocess.run([sys.executable, "-B", str(checker), str(workspace)], text=True, capture_output=True, timeout=20)
    markers = [line.removeprefix("EVAL_RESULT: ") for line in result.stdout.splitlines() if line.startswith("EVAL_RESULT: ")]
    assert len(markers) == 1, result.stderr or result.stdout
    report = json.loads(markers[0])
    assert set(report["checks"]) == set(manifest["expected_checks"]), report
    assert result.returncode == (0 if report["status"] == "pass" else 1), report
    return report


def main():
    for path in sorted((ROOT / "tasks").glob("*.json")):
        manifest = json.loads(path.read_text())
        fixture = ROOT / manifest["fixture"].removeprefix("../")
        module = next(fixture.glob("*.py")).name
        with tempfile.TemporaryDirectory(prefix="followup-oracle-") as temporary:
            workspace = Path(temporary) / "workspace"
            shutil.copytree(fixture, workspace)
            broken = run_check(manifest, workspace)
            assert broken["status"] == "fail", (manifest["id"], broken)
            source = (workspace / module).read_text()
            reference = REFERENCES[manifest["id"]]
            source = source.split('@app.get')[0] + reference if module == "app.py" else reference
            (workspace / module).write_text(source)
            repaired = run_check(manifest, workspace)
            assert repaired["status"] == "pass", (manifest["id"], repaired)
            if manifest["id"] == "request-resource-errors":
                for name, old, new in [
                    ("resource", "handle = await resource.acquire()", "handle = await captured_resource.acquire()"),
                    ("service", "return await service.lookup(job_id)", "return await captured_service.lookup(job_id)"),
                ]:
                    mutant = source.replace("from fastapi import Depends, HTTPException", "captured_resource = resource\ncaptured_service = service\nfrom fastapi import Depends, HTTPException")
                    mutant = mutant.replace(old, new)
                    (workspace / module).write_text(mutant)
                    rejected = run_check(manifest, workspace)
                    assert rejected["status"] == "fail", (name, rejected)
                    assert all(rejected["checks"][key] for key in ["response_1", "cleanup_1", "no_shutdown_release"]), rejected
                    assert not rejected["checks"]["replacement_cleanup_1" if name == "resource" else "replacement_service_called"], rejected
            (workspace / module).write_text("invalid Python syntax !!!")
            invalid = run_check(manifest, workspace)
            assert invalid["status"] == "fail" and not any(invalid["checks"].values()), invalid
            print(f'{manifest["id"]}: broken/syntax rejected; reference passed {len(repaired["checks"])} checks')
    print("Four external oracles validated; no agent calls performed.")


if __name__ == "__main__":
    main()
