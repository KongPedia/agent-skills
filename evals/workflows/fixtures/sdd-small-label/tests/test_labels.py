import unittest
from labels import display_label


class LabelTests(unittest.TestCase):
    def test_plain_word(self):
        self.assertEqual(display_label("hello"), "Hello")
