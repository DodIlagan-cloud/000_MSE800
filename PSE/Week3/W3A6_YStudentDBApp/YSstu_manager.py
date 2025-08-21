"""Week 3 - Activity 6: Develop the python code for Week 3 - Activity 4
Use the sample code to develop a command-line application for Week 3 - Activity 4, incorporating a database sqlite3 
and have at least three functionality such as add records, delete records and view records for different tables.
Share the completed project on GitHub here, with including a README.txt file in your repository to describe the technical aspects of this project (Yoobee Colleges).

YSstu_manager.py - Week 3 Activity 6 - W3A6 - EJI
Eduardo JR Ilagan
"""

from YSDatabase import create_connection
import sqlite3

"""Function for the Student Menu"""
def menu_01_stu():
    while True:
        print("\n==== Yoobee Student Menu ====")
        print("1. Add Student")
        print("2. View Student")
        print("3. Delete Student Record")
        print("4. Check for Student Payment")
        print("5. Go Back to Last Menu")
        m01_choice = input("Select an option (1-4):")
        if m01_choice == "1":
            stu_name = input("Name: ")
            stu_addr = input("Addres: ")
            add_student(stu_name, stu_addr)
        elif m01_choice == "2":
            stu_name = input("Enter Name: ")
            search=view_student(stu_name)
            for search in search:
                print(search)
        elif m01_choice == "3":
            rec_info_check = input("Do you know the details of the record you wish to delete? (Y/N): ").upper()
            if rec_info_check == "Y":
                stuid_check = input("Do you know the student's ID? (Y/N)").upper()
                if stuid_check == "Y":
                    stu_id = input("Enter Student's ID: ")
                    delete_student(stu_id)
                else:
                    stu_name = input("Enter Name: ")
                    search=view_student(stu_name)
                    for search in search:
                        print(search)
                    print("Please take note of Student's ID")
                    delete_student(stu_id)
            else:
                stu_name=input("Get the details of the student by searching by the student's name:" )
                search=view_student(stu_name)
                for search in search:
                    print(search)
                print("Please take note of Student's ID")
                stu_id = input("Enter student's ID: ")
                delete_student(stu_id)
        elif m01_choice == "4":
            pay_check = input("Do you know the student's ID? (Y/N)").upper()
            if pay_check == "Y":
                stu_id = input("Enter student's ID: ")
                int(stu_id)
                search=view_sturec_vid(stu_id)
                for search in search:
                    print(search)
                if search == "":
                    print("There are no records for Student's name: '{stu_name}' ")
                pay_check_func(stu_id)
            else:
                stu_name = input("Enter student's name: ")
                search=view_student(stu_name)
                for search in search:
                    print(search)
                if search == "":
                    print("There are no records for Student's name: '{stu_name}' ")
                else:
                    print("Please take note of Student's ID")
                    stu_id = input("Enter student's ID: ")
                    int(stu_id)
                    pay_check_func(stu_id)
        elif m01_choice == "5":
            print("Going back to Main Menu.")
            break
        else:
            print("Invalid Input. Going back to Main Menu.")
            break


"""Function for adding student records"""
def add_student(stu_name, stu_addr):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO students (stu_name, stu_addr) VALUES (?, ?)", (stu_name, stu_addr))
        conn.commit()
        print(" Student Record added successfully.")
    except sqlite3.Error as e: 
        print(f"An error occurred during adding record: {e}")
        conn.rollback() # Rollback if an error occurred
    conn.close()


"""Function for checking payment records."""
def pay_check_func(stu_id):
    paydet=check_stu_pay(stu_id)
    if paydet:
        print("Here are the details: ",paydet[0] )
    else:
        stu_name=view_stuname_vid(stu_id)
        print(f"There are no payment records for {stu_name[0]} to delete.")

"""Function for viewing student records based on Student Name wild card search"""
def view_student(stu_name):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students WHERE stu_name LIKE ?", ('%' + stu_name + '%',))
    rows = cursor.fetchall()
    if rows :
        print("Record found from students table.")
    else:
        print(f"No record for '{stu_name}' exists.")
    conn.close()
    if cursor.description:
        column_aliases = [description[0] for description in cursor.description]
    else:
        print("No cursor description available.")
    # Fetch and print data using aliases as headers
    print(column_aliases)
    return rows

"""Function for viewing student Student Name based on Student Id search"""
def view_stuname_vid(stu_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT stu_name FROM students WHERE stu_id = {stu_id} ")
    rows = cursor.fetchall()
    if rows :
        stu_name = rows[0]
        print(f"Record found for student {stu_name[0]} in the students records.")
    else:
        print(f"No record for student id'{stu_id}' exists.")
    conn.close()
    return rows[0]


def view_sturec_vid(stu_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM students WHERE stu_id = {stu_id} ")
    rows = cursor.fetchall()
    if rows :
        stu_name = rows[0]
        print(f"Record found for student {stu_name[0]} in the students records.")
    else:
        print(f"No record for student id'{stu_id}' exists.")
    conn.close()
    return rows

"""Function for deleting student records based on Student ID """
def delete_student(stu_id):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM students WHERE stu_id = ?", (stu_id))
        ins_row_count = cursor.rowcount
        if ins_row_count > 0:
            print("Successfully deleted student id ", stu_id,"from the record.")
        else:
            print(" There were no records deleted. Student ID ",stu_id," is not in the records.")
        conn.commit()
    except sqlite3.Error as e: 
        print(f"An error occurred during deletion: {e}")
        conn.rollback() # Rollback if an error occurred
    conn.close()

"""Function for checking student payment records based on Student ID .
Query from payemnts and students table."""
def check_stu_pay(stu_id):
    conn = create_connection()
    cursor = conn.cursor()
    search_query = f"""SELECT s.stu_id,
                                s.stu_name,
                                p.tran_id,
                                p.amount,
                                pd_date
                           FROM students s, 
                                payments p 
                          WHERE s.stu_id = p.stu_id 
                            AND s.stu_id = {stu_id}
                            
                    """
    cursor.execute(search_query)
    rows = cursor.fetchall()
    if rows:
        print(f"Payment records found for student ID: {stu_id}")
    else:
        print(f"There are no payment records found for student ID: {stu_id}")
    conn.close()
    return rows


