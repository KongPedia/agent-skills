"""Behavioral oracle only; SDD chronology and contract quality need trace review."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(sys.argv[1]).resolve()))
checks = dict.fromkeys([
    "page_shape_and_sort", "cursor_and_end", "validation", "input_ownership",
    "web_first_page", "export_all_pages",
], False)


def check(name, operation):
    try:
        checks[name] = bool(operation())
    except Exception:
        checks[name] = False


def raises_value_error(operation):
    try:
        operation()
    except ValueError:
        return True
    return False


try:
    from provider import list_tasks
    from web import render_tasks
    from export import export_ids

    records = [{"id": n, "title": f"task {n}"} for n in [4, 1, 3, 2, 5]]
    check("page_shape_and_sort", lambda: list_tasks(records) == {
        "items": [{"id": 1, "title": "task 1"}, {"id": 2, "title": "task 2"}],
        "next_cursor": 2,
    })
    check("cursor_and_end", lambda: (
        list_tasks(records, cursor=2, limit=2) == {"items": [records[2], records[0]], "next_cursor": 4}
        and list_tasks(records, cursor=4, limit=2) == {"items": [records[4]], "next_cursor": None}
        and list_tasks(records, cursor=5) == {"items": [], "next_cursor": None}
        and list_tasks(records, cursor=100) == {"items": [], "next_cursor": None}
        and list_tasks([], cursor=0) == {"items": [], "next_cursor": None}
    ))
    check("validation", lambda: all(
        raises_value_error(lambda value=value: list_tasks([], **{field: value}))
        for field, values in [("cursor", [-1, True, False, 1.5, "1", None]),
                              ("limit", [0, -1, 51, True, False, 1.5, "1", None])]
        for value in values
    ) and list_tasks(records, limit=1)["next_cursor"] == 1
      and list_tasks(records, limit=50)["next_cursor"] is None)

    def ownership():
        original = [dict(record) for record in records]
        result = list_tasks(records)
        result["items"][0]["title"] = "changed"
        return records == original and result["items"] is not records

    check("input_ownership", ownership)
    check("web_first_page", lambda: render_tasks(records) == ["task 1", "task 2"]
          and render_tasks(records, limit=3) == ["task 1", "task 2", "task 3"]
          and render_tasks([]) == [])

    def all_pages():
        many = [{"id": n, "title": f"task {n}"} for n in range(122, 0, -1)]
        original = [dict(record) for record in many]
        return (export_ids(many) == list(range(1, 123)) and many == original
                and export_ids(records) == [1, 2, 3, 4, 5] and export_ids([]) == [])

    check("export_all_pages", all_pages)
except Exception:
    pass

passed = all(value is True for value in checks.values())
print("EVAL_RESULT: " + json.dumps({"status": "pass" if passed else "fail", "checks": checks}))
raise SystemExit(0 if passed else 1)
