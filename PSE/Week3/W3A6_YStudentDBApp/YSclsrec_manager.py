"""Week 3 - Activity 6: Develop the python code for Week 3 - Activity 4
Use the sample code to develop a command-line application for Week 3 - Activity 4, incorporating a database sqlite3 
and have at least three functionality such as add records, delete records and view records for different tables.
Share the completed project on GitHub here, with including a README.txt file in your repository to describe the technical aspects of this project (Yoobee Colleges).

YSclsrec_manager.py - Week 3 Activity 6 - W3A6 - EJI
Eduardo JR Ilagan
"""


from YSDatabase import create_connection
import sqlite3
from YSclsrec_view import clsrec_view,clsrec_stuid_chk,clsrec_instid_chk,clsrec_sbjtid_chk



def menu_06_clsrec():
    while True:
        print("\n==== Yoobee Class Record Menu ====")
        print("1. Add Records")
        print("2. View Record")
        print("3. Go Back to Last Menu")
        m06_choice = input("Select an option (1-3): ")
        if m06_choice == "1":
            clsrec_stu_id = clsrec_stuid_chk() 
            clsrec_sbjt_id = clsrec_sbjtid_chk()
            clsrec_inst_id = clsrec_instid_chk()
            add_clsrec(clsrec_stu_id,clsrec_sbjt_id,clsrec_inst_id)
        elif m06_choice == "2":
            clsrec_view()
        elif m06_choice == "3":
            print("Going back to Main Menu.")
            break
        else:
            print("Invalid Input. Going back to Main Menu.")
            break



"""Function for adding class records"""
def add_clsrec(clsrec_stu_id,clsrec_sbjt_id,clsrec_inst_id):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO class_records (stu_id,sbjt_id, inst_id ) VALUES (?,?,?)", (clsrec_stu_id,clsrec_sbjt_id,clsrec_inst_id))
        conn.commit()
        print(" Course added successfully.")
    except sqlite3.Error as e: 
        print(f"An error occurred during adding of the record: {e}")
        conn.rollback() # Rollback if an error occurred
    conn.close()




"""Function for deleting course's records based on course ID """
def delete_sbjt(sbjt_id):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM subject WHERE sbjt_id = ?", (sbjt_id))
        ins_row_count = cursor.rowcount
        if ins_row_count > 0:
            print("Successfully deleted subject id ", sbjt_id,"from the record.")
        else:
            print(" There were no records deleted. Course ID ",sbjt_id," is no longer in the records.")
        conn.commit()
    except sqlite3.Error as e: 
        print(f"An error occurred during deletion: {e}")
        conn.rollback() # Rollback if an error occurred
    conn.close()


