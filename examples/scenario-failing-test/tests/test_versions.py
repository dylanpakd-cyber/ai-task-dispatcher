import unittest

from versions import latest


class TestLatest(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(latest(["1.2.0", "1.3.0"]), "1.3.0")

    def test_double_digit_components(self):
        # the bug this scenario ships with: lexicographic max says 1.9 > 1.10
        self.assertEqual(latest(["1.9.0", "1.10.0"]), "1.10.0")

    def test_single(self):
        self.assertEqual(latest(["0.1.0"]), "0.1.0")


if __name__ == "__main__":
    unittest.main()
