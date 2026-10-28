# Task board library

The maintained producer contract is docs/specs/task-page.md. provider.py owns
listing; web.py displays the first page and export.py exports the entire list.
All consumers ship together as a local Python library. There are no external
consumers, persistence or HTTP deployment in this exercise.
Run the current examples with `python -m unittest discover -s tests`.
