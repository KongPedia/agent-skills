"""External behavior oracle; never mounted into model workspace."""
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(sys.argv[1]).resolve()))
checks = dict.fromkeys(['millisecond_conversion','default_seconds','invalid_headers','worker_unchanged','sdk_contract'], False)
def check(name, fn):
    try:
        checks[name] = bool(fn())
    except Exception:
        pass

def rejects(value):
    try:
        schedule_retry({'Retry-After-Ms': value})
    except ValueError:
        return True
    return False

try:
    from http_retry import schedule_retry
    from worker import nightly_retry
    import retry_sdk
    check('millisecond_conversion', lambda: all(schedule_retry({'Retry-After-Ms': str(value)}) == {'delay_seconds': value / 1000} for value in [0,1,999,2500,30000]))
    check('default_seconds', lambda: schedule_retry({}) == {'delay_seconds': 1.0})
    check('invalid_headers', lambda: all(rejects(value) for value in ['-1','bad','2.5','']))
    check('worker_unchanged', lambda: nightly_retry() == {'delay_seconds': 30.0})
    check('sdk_contract', lambda: retry_sdk.__version__ == '2.4.0' and retry_sdk.delay(2.5) == {'delay_seconds': 2.5} and retry_sdk.delay() == {'delay_seconds': 1.0})
except Exception:
    pass
passed = all(checks.values())
print('EVAL_RESULT: ' + json.dumps({'status': 'pass' if passed else 'fail','checks': checks}))
raise SystemExit(0 if passed else 1)
