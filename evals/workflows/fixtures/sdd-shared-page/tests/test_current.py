import unittest
from provider import list_tasks
from web import render_tasks
from export import export_ids


class CurrentBehavior(unittest.TestCase):
    def test_empty_consumers(self):
        self.assertEqual(render_tasks([]), [])
        self.assertEqual(export_ids([]), [])

    def test_provider_does_not_mutate(self):
        records = [{"id": 1, "title": "one"}]
        list_tasks(records)
        self.assertEqual(records, [{"id": 1, "title": "one"}])
