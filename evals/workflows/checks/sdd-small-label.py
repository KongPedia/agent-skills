"""Behavioral oracle; proportional specification effort is reviewed separately."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(sys.argv[1]).resolve()))
checks = dict.fromkeys(["underscores", "whitespace", "title_semantics", "empty"], False)


def check(name, cases):
    try:
        checks[name] = all(display_label(value) == expected for value, expected in cases)
    except Exception:
        checks[name] = False


try:
    from labels import display_label
    check("underscores", [("account_name", "Account Name"), ("__two___words__", "Two Words")])
    check("whitespace", [("  hello\t\nworld ", "Hello World"), ("a_ \t_b", "A B")])
    check("title_semantics", [("api_HTTP", "Api Http"), ("don't STOP", "Don'T Stop"), ("éclair_menu", "Éclair Menu")])
    check("empty", [("", ""), (" _\t__\n ", "")])
except Exception:
    pass

passed = all(value is True for value in checks.values())
print("EVAL_RESULT: " + json.dumps({"status": "pass" if passed else "fail", "checks": checks}))
raise SystemExit(0 if passed else 1)
