import unittest

from report import line_item, total_line


class TestReport(unittest.TestCase):
    def test_line_item(self):
        self.assertEqual(line_item("coffee", 450), "coffee: $4.50")

    def test_line_item_pads_cents(self):
        self.assertEqual(line_item("gum", 105), "gum: $1.05")

    def test_total(self):
        self.assertEqual(total_line([("a", 100), ("b", 205)]), "TOTAL: $3.05")


if __name__ == "__main__":
    unittest.main()
