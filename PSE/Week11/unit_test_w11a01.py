import unittest

"""function for addiition"""
def add(x, y):
    return x + y

"""function for subtraction"""
def diff(x, y):
    return x - y

"""function for division"""
def div(x, y):
    return x / y

"""function for multiplication"""
def tims(x, y):
    return x * y

class TestMathOperations(unittest.TestCase):
    """Testing Addition"""
    def test_add(self):
        self.assertEqual(add(2, 3), 5)
        self.assertEqual(add(-1, 1), 0)
    """Testing Subtraction"""
    def test_diff(self):
        self.assertEqual(diff(7, 4), 3)
        self.assertEqual(diff(-1, 1), -2)
        self.assertEqual(diff(-1, -1), 0)
    """Testing divisionm"""
    def test_div(self):
        self.assertEqual(div(10, 2), 5)
        self.assertEqual(div(10, -5),-2)
        with self.assertRaises(ZeroDivisionError):
            div(10, 0)
    """Testing multiplication"""
    def test_tims(self):
        self.assertEqual(tims(10, 2), 20)
        self.assertEqual(tims(10, 0), 0)
        self.assertEqual(tims(10,-3),-30)

if __name__  == '__main__':
    unittest.main()
