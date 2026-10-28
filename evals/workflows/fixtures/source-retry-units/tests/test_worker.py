import unittest
from worker import nightly_retry
class WorkerContract(unittest.TestCase):
    def test_thirty_seconds(self):
        self.assertEqual(nightly_retry(), {"delay_seconds": 30.0})
