
"""Develop a program using Object-Oriented Programming (OOP)  
and Unit-testing to create a simple Personal Expense Tracker.
The system should include at least two main functionalities:
Add Expense : Allow the user to add a new expense with a description and an amount.
Calculate Total Expense :  Compute and display the total amount of all recorded expenses.
Share your GitHub Link at the end here."""

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

    def test_totexp(self):
        """test case for adding record"""
        for rec in self.tr:
            print(rec)
        self.assertEqual(self.tr.total_expense(),290)


if __name__  == '__main__':
    r = Records()
    r.add_record("Lunch",15,"Food","10-Oct-25")
    r.add_record("Gas",40,"Transpo","09-Oct-25")
    r.add_record("Rent",180,"Rent","07-Oct-25")
    r.add_record("Electricity",30,"Utilities","10-Oct-25")

    for rec in r:
        print(rec)

    print("Expense for the Month:", r.total_expense())
    unittest.main(verbosity=2)
