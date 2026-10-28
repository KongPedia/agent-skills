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

def raises(kind, fn):
    try:
        fn()
    except kind:
        return True
    return False

checks = dict.fromkeys(['constructor_validation', 'replay_no_extension_exact_expiry', 'conflict_preserves_live_entry', 'deep_snapshot', 'capacity_expiry_and_no_eviction'], False)
try:
    from ledger import Ledger
    check("constructor_validation", lambda: all(raises(ValueError, lambda t=t,c=c: Ledger(t,c)) for t,c in [(0,2),(-1,2),(True,2),(1.5,2),("1",2),(1,0),(1,-1),(1,True),(1,1.5),(1,"2")]))
    def replay():
        ledger=Ledger(10,2)
        return ledger.claim("a", {"v":1},0) is True and ledger.claim("a", {"v":1},9) is False and ledger.claim("a", {"v":1},10) is True
    check("replay_no_extension_exact_expiry", replay)
    def conflict():
        ledger=Ledger(10,2); ledger.claim("a", {"v":1},0)
        return raises(ValueError,lambda:ledger.claim("a",{"v":2},5)) and ledger.claim("a",{"v":1},6) is False and ledger.claim("a",{"v":2},10) is True
    check("conflict_preserves_live_entry",conflict)
    def snapshot():
        ledger=Ledger(10,2); payload={"nested":{"items":[1]}}; ledger.claim("a",payload,0); payload["nested"]["items"].append(2)
        return ledger.claim("a",{"nested":{"items":[1]}},1) is False and raises(ValueError,lambda:ledger.claim("a",payload,2))
    check("deep_snapshot",snapshot)
    def capacity():
        ledger=Ledger(10,2); ledger.claim("a",{},0); ledger.claim("b",{},1)
        return raises(OverflowError,lambda:ledger.claim("c",{},2)) and ledger.claim("a",{},3) is False and ledger.claim("b",{},4) is False and ledger.claim("c",{},10) is True and raises(OverflowError,lambda:ledger.claim("d",{},10)) and ledger.claim("d",{},11) is True
    check("capacity_expiry_and_no_eviction",capacity)
except Exception:
    pass

passed = bool(checks) and all(value is True for value in checks.values())
print("EVAL_RESULT: " + json.dumps({"status": "pass" if passed else "fail", "checks": checks}))
raise SystemExit(0 if passed else 1)
