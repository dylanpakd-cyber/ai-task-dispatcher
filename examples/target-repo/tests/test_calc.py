import unittest

from calc import add, fizzbuzz


class TestCalc(unittest.TestCase):
    def test_add(self):
        self.assertEqual(add(2, 3), 5)

    def test_fizzbuzz(self):
        self.assertEqual(fizzbuzz(15), "fizzbuzz")
        self.assertEqual(fizzbuzz(9), "fizz")
        self.assertEqual(fizzbuzz(10), "buzz")
        self.assertEqual(fizzbuzz(7), "7")


if __name__ == "__main__":
    unittest.main()
