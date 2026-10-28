# Task listing
Status: current
Owner: task-board maintainers

`provider.list_tasks(records)` returns a list of task dictionaries in input
order. Records contain unique integer `id` and string `title` fields. Input is
not mutated. `web.render_tasks(records)` returns their titles.
`export.export_ids(records)` returns their IDs. Both consumers currently list
all tasks; no pagination is supported.

Acceptance: empty input produces an empty list; consumers preserve input order.
Evidence: tests/test_current.py exercises provider and both consumers.
