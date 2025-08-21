"""Week 3 - Activity 6: Develop the python code for Week 3 - Activity 4
Use the sample code to develop a command-line application for Week 3 - Activity 4, incorporating a database sqlite3 
and have at least three functionality such as add records, delete records and view records for different tables.
Share the completed project on GitHub here, with including a README.txt file in your repository to describe the technical aspects of this project (Yoobee Colleges).

YSinst_manager.py - Week 3 Activity 6 - W3A6 - EJI
Eduardo JR Ilagan
"""

from YSDatabase import create_connection
import sqlite3

"""Function for Instructor Menu"""
def menu_02_inst():
    while True:
        print("\n==== Yoobee Instructor Menu ====")
        print("1. Add Instructor")
        print("2. View Insturctor")
        print("3. Delete Instructor Record")
        print("4. Go Back to Last Menu")
        #print("4. Blank")
        m02_choice = input("Select an option (1-4): ")
        if m02_choice == "1":
            inst_name = input("Name: ")
            add_inst(inst_name)
        elif m02_choice == "2":
            inst_name = input("Enter Name: ")
            search=view_inst(inst_name)
            for search in search:
                print(search)
        elif m02_choice == "3":
            rec_info_check = input("Do you know the details of the record you wish to delete? (Y/N): ").upper()
            if rec_info_check == "Y":
                instid_check = input("Do you know the Instructor's ID? (Y/N)").upper()
                if instid_check == "Y":
                    inst_id = input("Enter Instructor's ID: ")
                    delete_inst(inst_id)
                else:
                    inst_name = input("Get the details of the instructor by searching by the instructor's name:" )
                    search=view_inst(inst_name)
                    for search in search:
                        print(search)
                    inst_id = input("Enter Instructor's ID: ")
                    delete_inst(inst_id)
            else:
                inst_name=input("Get the details of the instructor by searching by the instructor's name:" )
                search=view_inst(inst_name)
                for search in search:
                    print(search)
                print("Please take note of Instructor's ID")
                inst_id = input("Enter instructor's ID: ")
                delete_inst(inst_id)
        elif m02_choice == "4":
            print("Going back to Main Menu.")
            break
        else:
            print("Invalid Input. Going back to Main Menu.")
            break


"""Function for adding Instructor records"""
def add_inst(inst_name):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO instructors (inst_name) VALUES (?)", (inst_name,))
        conn.commit()
        print(" Instructor added successfully.")
    except sqlite3.Error as e: 
        print(f"An error occurred during adding of the record: {e}")
        conn.rollback() # Rollback if an error occurred
    conn.close()

"""Function for viewing instructor records based on Student Name wild card search"""
def view_inst(inst_name):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM instructors WHERE inst_name LIKE ?", ('%' + inst_name + '%',))
    rows = cursor.fetchall()
    if rows :
        print("Record found from instructor table.")
    else:
        print(f"No record for '{inst_name}' exists.")
    if cursor.description:
        column_aliases = [description[0] for description in cursor.description]
    else:
        print("No cursor description available.")
    # Fetch and print data using aliases as headers
    print(column_aliases)
    conn.close()
    return rows

"""Function for viewing instructor inst_name based on Instructor Id search"""
def view_instname_vid(inst_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT inst_name FROM instructors WHERE inst_id = {inst_id} ")
    rows = cursor.fetchall()
    if rows :
        inst_name = rows[0]
        print(f"Record found for instructor {inst_name[0]} in the instructor records.")
    else:
        print(f"No record for instructor id'{inst_id}' exists.")
    conn.close()
    return rows[0]

"""Function for deleting instructor's records based on instructor ID """
def delete_inst(inst_id):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM instructors WHERE inst_id = ?", (inst_id))
        ins_row_count = cursor.rowcount
        if ins_row_count > 0:
            print("Successfully deleted instructor id ", inst_id,"from the record.")
        else:
            print(" There were no records deleted. Instructor ID ",inst_id," is not nger in the records.")
        conn.commit()
    except sqlite3.Error as e: 
        print(f"An error occurred during deletion: {e}")
        conn.rollback() # Rollback if an error occurred
    conn.close()

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

