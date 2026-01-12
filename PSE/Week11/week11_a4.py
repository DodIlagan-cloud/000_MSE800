""" Update the testing section in Week 11 – Activities 1 & 2 
by implementing doctesting or a combination of unittest and doctest (hybrid testing). 
After completing the updates, share your GitHub repository link with the revised code.
"""

import doctest
import unittest

class Records:
    """Created the class that records the expense"""
    def __init__(self):
        self.r = []

    def add_record(self,exp_name, exp_amt, exp_type, exp_date):
        """function that adds the expenses to the record"""
        record = {
            "Expense Name":exp_name, 
            "Amount":exp_amt, 
            "Type":exp_type,
            "Date": exp_date
        }
        self.r.append(record)

    def total_expense(self):
        """function that sums the expenses"""
        return sum(item["Amount"] for item in self.r)

    def __getitem__(self, i):
        """enables the class to act as a list"""
        return self.r[i]

    def __iter__(self):
        """enables the rcords to be able to iterate"""
        return iter(self.r)

    def __len__(self):
        """enables len to be used on the class"""
        return len(self.r)

    def total_exp_type(self,exp_type):
        """function that sums the expenses"""
        return sum(item["Amount"] for item in self.r if item["Type"] == exp_type)

class TestExpTracker(unittest.TestCase):
    """class for unit testing"""
    def setUp(self):
        """test data"""
        self.tr = Records()
        self.tr.add_record("TestLunch",30,"Food","10-Oct-25")
        self.tr.add_record("TestGas",40,"Transpo","09-Oct-25")
        self.tr.add_record("TestRent",190,"Rent","07-Oct-25")
        self.tr.add_record("TestElectricity",30,"Utilities","10-Oct-25")

    def test_add_rec(self):
        """test case for adding record"""
        len_before_insert = len(self.tr.r)
        self.tr.add_record("TestWater",20,"Utilities","10-Oct-25")
        self.assertEqual(len(self.tr.r),len_before_insert +1)

    def test_tot_exp(self):
        """test case for summing up total expenses"""
        for rec in self.tr:
            print(rec)
        self.assertEqual(self.tr.total_expense(),290)

    def test_tot_exptype(self):
        """test case for summing up expenses based on type"""
        self.tr.add_record("TestWater",20,"Utilities","10-Oct-25")
        self.assertEqual(self.tr.total_exp_type("Utilities"),50)

def add(x, y):
    """function for addiition
    >>> add(2, -1)
    1
    >>> add(2, 2)
    4
    """
    return x + y


def diff(x, y):
    """function for subtraction
    >>> diff(1, -1)
    2
    >>> diff(2, 2)
    0
    >>> diff(-1, -1)
    0
    """
    return x - y

def div(x, y):
    """function for division
    >>> div(4, 2)
    2.0
    >>> div(3, 2)
    1.5
    >>> div(7, 0) # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    ZeroDivisionError:...
    """
    return x / y

def tims(x, y):
    """function for multiplication
    >>> tims(3, 3)
    9
    >>> tims(-1, -2)
    2
    >>> tims(6, 0)
    0
    >>> tims(1, -1)
    -1
    """
    return x * y


if __name__  == '__main__':
    doctest.testmod(verbose=True)
    unittest.main(verbosity=2)
    r = Records()
    r.add_record("Lunch",15,"Food","10-Oct-25")
    r.add_record("Gas",40,"Transpo","09-Oct-25")
    r.add_record("Rent",180,"Rent","07-Oct-25")
    r.add_record("Electricity",30,"Utilities","10-Oct-25")

    for rcrd in r:
        print(rcrd)

    tot_exp = r.total_expense()

    print("Expense for the Month:", tot_exp)

    tot_util = r.total_exp_type("Utilities")

    util_part = tims(div(tot_util, tot_exp), 100)

    print("Expense for the Month:", util_part)
