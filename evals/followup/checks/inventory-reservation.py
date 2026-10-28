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

checks = dict.fromkeys(['normal', 'duplicate_aggregation', 'aggregate_insufficient', 'unknown_sku', 'invalid_quantities', 'input_ownership', 'failure_atomic', 'empty_independent'], False)
try:
    from inventory import reserve
    check("normal", lambda: reserve({"a": 5, "b": 2}, [("a", 2)]) == {"a": 3, "b": 2})
    check("duplicate_aggregation", lambda: reserve({"a": 7}, [("a", 2), ("a", 3)]) == {"a": 2})
    check("aggregate_insufficient", lambda: raises(ValueError, lambda: reserve({"a": 4}, [("a", 3), ("a", 2)])))
    check("unknown_sku", lambda: raises(KeyError, lambda: reserve({"a": 4}, [("missing", 1)])))
    check("invalid_quantities", lambda: all(raises(ValueError, lambda q=q: reserve({"a": 4}, [("a", q)])) for q in [0, -1, True, 1.5, "1"]))
    def independent():
        stock = {"a": 5}; lines = [("a", 2)]
        result = reserve(stock, lines)
        return result == {"a": 3} and stock == {"a": 5} and lines == [("a", 2)] and result is not stock
    check("input_ownership", independent)
    def failure_atomic():
        stock = {"a": 5, "b": 1}; lines = [("a", 2), ("b", 2)]
        return raises(ValueError, lambda: reserve(stock, lines)) and stock == {"a": 5, "b": 1} and lines == [("a", 2), ("b", 2)]
    check("failure_atomic", failure_atomic)
    def empty():
        stock = {"a": 5}; result = reserve(stock, [])
        return result == stock and result is not stock
    check("empty_independent", empty)
except Exception:
    pass

passed = bool(checks) and all(value is True for value in checks.values())
print("EVAL_RESULT: " + json.dumps({"status": "pass" if passed else "fail", "checks": checks}))
raise SystemExit(0 if passed else 1)
