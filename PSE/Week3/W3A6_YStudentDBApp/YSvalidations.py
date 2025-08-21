"""Week 3 - Activity 6: Develop the python code for Week 3 - Activity 4
Use the sample code to develop a command-line application for Week 3 - Activity 4, incorporating a database sqlite3 
and have at least three functionality such as add records, delete records and view records for different tables.
Share the completed project on GitHub here, with including a README.txt file in your repository to describe the technical aspects of this project (Yoobee Colleges).

YSvalidations.py - Week 3 Activity 6 - W3A6 - EJI
Eduardo JR Ilagan
"""
from datetime import datetime

"""Validation functions for user inputs"""
# integer validation input - validates if the user input for the integer is indeed a positive number
def chk_int(int_val):
    while True:
        try:
            int_val = int(int_val)
            return int_val
        except ValueError:
            print("Invalid input. Please enter a whole number.")

# date validation input - validates if the user input for the date is in the correct format
def date_valid(pd_date):
    pd_date_chk = date_check(pd_date)
    while pd_date_chk == False: 
        pd_date = input("Incorrect Date format Entered: Please enter date with this format YYYY-MM-DD: ")
        pd_date_chk = date_check(pd_date)
        if pd_date_chk == True:
            break
    return pd_date

def date_check(pd_date):
    try:
        is_date = datetime.strptime(pd_date, "%Y-%m-%d")
        return True
        #print(is_date)
    except ValueError:
        return False
