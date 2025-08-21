"""Week 3 - Activity 6: Develop the python code for Week 3 - Activity 4
Use the sample code to develop a command-line application for Week 3 - Activity 4, incorporating a database sqlite3 
and have at least three functionality such as add records, delete records and view records for different tables.
Share the completed project on GitHub here, with including a README.txt file in your repository to describe the technical aspects of this project (Yoobee Colleges).

YSpay_manager.py - Week 3 Activity 6 - W3A6 - EJI
Eduardo JR Ilagan
"""

from YSDatabase import create_connection
from YSstu_manager import view_student,check_stu_pay,view_sturec_vid
from YSvalidations import chk_int,date_valid
import sqlite3

"""Function for the Payemnts Menu"""
def menu_05_pay():
    while True:
        print("\n==== Yoobee Payments Menu ====")
        print("1. Add Student Payment Record")
        print("2. Delete Student Payment Record")
        print("3. Go Back to Last Menu")
        m02_choice = input("Select an option (1-3):")
        if m02_choice == "1":
                pay_check = input("Do you know the student's ID? (Y/N)").upper()
                if pay_check == "Y":
                    pay_add()
                else:
                    stu_name = input("Enter Name: ")
                    search=view_student(stu_name)
                    for search in search:
                        print(search)
                    print("Please take note of Student's ID")
                    pay_add()
        elif m02_choice == "2":
            rec_info_check = input("Do you know the details of the record you wish to delete? (Y/N): ").upper()
            if rec_info_check == "Y":
                pay_check = input("Do you know the student's ID? (Y/N)").upper()
                if pay_check == "Y":
                    pay_del()
                else:
                    stu_name = input("Enter Name: ")
                    search=view_student(stu_name)
                    for search in search:
                        print(search)
                        print("Please take note of Student's ID")
                        pay_del()
            else:
                stu_name=input("Get the details of the student by searching by the student's name:" )
                search=view_student(stu_name)
                for search in search:
                    print(search)
                print("Please take note of Student's ID")
                stu_id = input("Enter student's ID: ")
                paydet=check_stu_pay(stu_id)
                if paydet:
                    record=paydet[0]
                    print("Here are the details: ",record )
                    pay_del()
                else:
                    stu_name=view_sturec_vid(stu_id)
                    print(f"There are no payment records for {stu_name[0]} to delete.")
        elif m02_choice == "3":
            print("Going back to Main Menu.")
            break
        else:
            print("Invalid Input. Going back to Main Menu.")
            break
            
"""Function for adding payment records to the payments table"""
def add_pay_record(stu_id, amount, pd_date):
    conn = create_connection()
    cursor = conn.cursor()
    # try catch exception errors for SQL execution
    try:
        cursor.execute("INSERT INTO payments (stu_id, amount, pd_date ) VALUES (?, ?, ?)", (stu_id, amount, pd_date))
        ins_row_count = cursor.rowcount
        if ins_row_count > 0:
            print(" Payment recorded successfully.")
        else:
            print(" There were no records added.")
        conn.commit()
    # try catch exception errors for SQL execution
    except sqlite3.Error as e:
         print(f"An error occurred during deletion: {e}")
         conn.rollback() # Rollback if an error occurred
    conn.close()


"""Function for deleting payment records from the payments table based on student id"""
def delete_pay_record(stu_id,pd_date):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT stu_name FROM students WHERE stu_id = {stu_id}")
    stu_name = cursor.fetchall()[0]
    # try catch exception errors for SQL execution
    try:
        cursor.execute("DELETE FROM payments WHERE stu_id = ? AND pd_date = ?",(stu_id,pd_date))
        del_rows_count = cursor.rowcount
        if del_rows_count > 0:
            print("Successfully deleted", stu_name[0].strip(),"'s payment records.")
        else:
            print(f"There were no records deleted for {stu_name[0].strip()} with transaction date of {pd_date}.")
        conn.commit() 
    # try catch exception errors for SQL execution
    except sqlite3.Error as e: 
        print(f"An error occurred during deletion: {e}")
        conn.rollback() # Rollback if an error occurred
    conn.close()

def pay_add():
    stu_id = input("Enter student's ID: ")
    stu_id=chk_int(stu_id)
    amount = input("Enter amount paid in NZD: ")
    amount=chk_int(amount)
    pd_date = input("Enter date amount was paid (YYYY-MM-DD): ")
    pd_date=date_valid(pd_date)
    add_pay_record(stu_id,amount,pd_date)

def pay_del():
    stu_id = input("Enter student's ID: ")
    stu_id=chk_int(stu_id)
    pd_date = input("Enter date amount was paid (YYYY-MM-DD): ")
    pd_date=date_valid(pd_date)
    delete_pay_record(stu_id,pd_date)