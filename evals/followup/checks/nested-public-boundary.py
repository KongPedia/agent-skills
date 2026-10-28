"""External behavioral oracle; not available in the model workspace."""
import copy
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


checks = dict.fromkeys(['detail_allowlist', 'missing_404', 'sorted_default_list', 'pagination_total', 'invalid_pagination', 'future_private_fields', 'source_unchanged', 'openapi_public_shapes'], False)
try:
    from fastapi.testclient import TestClient
    import app as module
    before=copy.deepcopy(module.CUSTOMERS)
    public=lambda row:{"id":row["id"],"name":row["name"],"contact":{"city":row["contact"]["city"]}}
    with TestClient(module.app) as client:
        response=client.get("/customers/1")
        check("detail_allowlist",lambda:response.status_code==200 and response.json()==public(before[1]))
        response=client.get("/customers/999")
        check("missing_404",lambda:response.status_code==404 and response.json()=={"detail":"customer not found"})
        response=client.get("/customers")
        check("sorted_default_list",lambda:response.status_code==200 and response.json()=={"items":[public(before[k]) for k in sorted(before)],"total":2})
        response=client.get("/customers",params={"offset":1,"limit":1})
        check("pagination_total",lambda:response.status_code==200 and response.json()=={"items":[public(before[2])],"total":2})
        check("invalid_pagination",lambda:all(client.get("/customers",params=params).status_code==422 for params in [{"offset":-1},{"limit":0},{"limit":51},{"offset":"oops"}]))
        module.CUSTOMERS[1]["future_secret"]="private"
        module.CUSTOMERS[1]["contact"]["future_secret"]="nested-private"
        detail=client.get("/customers/1"); listing=client.get("/customers")
        check("future_private_fields",lambda:detail.json()==public(before[1]) and listing.json()=={"items":[public(before[k]) for k in sorted(before)],"total":2})
        module.CUSTOMERS[1].pop("future_secret"); module.CUSTOMERS[1]["contact"].pop("future_secret")
    check("source_unchanged",lambda:module.CUSTOMERS==before)
    def schema_boundary():
        schema=module.app.openapi()
        def resolve(node):
            while "$ref" in node:
                node=schema["components"]["schemas"][node["$ref"].split("/")[-1]]
            return node
        detail=resolve(schema["paths"]["/customers/{customer_id}"]["get"]["responses"]["200"]["content"]["application/json"]["schema"])
        listing=resolve(schema["paths"]["/customers"]["get"]["responses"]["200"]["content"]["application/json"]["schema"])
        item=resolve(resolve(listing["properties"]["items"])["items"])
        return all(set(row.get("properties",{}))=={"id","name","contact"} and set(resolve(row["properties"]["contact"]).get("properties",{}))=={"city"} for row in [detail,item]) and set(listing.get("properties",{}))=={"items","total"}
    check("openapi_public_shapes",schema_boundary)
except Exception:
    pass

passed = bool(checks) and all(value is True for value in checks.values())
print("EVAL_RESULT: " + json.dumps({"status": "pass" if passed else "fail", "checks": checks}))
raise SystemExit(0 if passed else 1)
