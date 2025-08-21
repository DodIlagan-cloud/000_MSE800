"""Week 3 - Activity 6: Develop the python code for Week 3 - Activity 4
Use the sample code to develop a command-line application for Week 3 - Activity 4, incorporating a database sqlite3 
and have at least three functionality such as add records, delete records and view records for different tables.
Share the completed project on GitHub here, with including a README.txt file in your repository to describe the technical aspects of this project (Yoobee Colleges).

YSsbjt_manager.py - Week 3 Activity 6 - W3A6 - EJI
Eduardo JR Ilagan
"""


from YSDatabase import create_connection
from YScrse_manager import view_crse
from YSinst_manager import view_inst
import sqlite3

def menu_04_sbjt():
    while True:
        print("\n==== Yoobee Subject Menu ====")
        print("1. Add Subject")
        print("2. View Subject")
        print("3. Delete Subject Record")
        print("4. Go Back to Last Menu")
        #print("4. Blank")
        m04_choice = input("Select an option (1-4): ")
        if m04_choice == "1":
            sbjt_name = input("Subject Name: ")
            sbjt_sched = input("Pleae enter the day (Day) and time (HH:mm) (e.g. Sat0800 for Saturday 8 AM): ")
            sbjt_crse_id = sbjt_crseid_chk()
            sbjt_inst_id = sbjt_instid_chk()  
            add_sbjt(sbjt_name,sbjt_sched,sbjt_crse_id,sbjt_inst_id)
        elif m04_choice == "2":
            sbjt_name = input("Enter Subject Name: ")
            search=view_sbjt(sbjt_name)
            for search in search:
                print(search)
        elif m04_choice == "3":
            rec_info_check = input("Do you know the details of the record you wish to delete? (Y/N): ").upper()
            if rec_info_check == "Y":
                sbjt_check = input("Do you know the Subject's ID? (Y/N)").upper()
                if sbjt_check == "Y":
                    sbjt_id = input("Enter Subject's ID: ")
                    delete_sbjt(sbjt_id)
                else:
                    sbjt_name = input("Enter Name: ")
                    search=view_sbjt(sbjt_name)
                    for search in search:
                        print(search)
                    sbjt_id = input("Enter Sbjects's ID: ")
                    delete_sbjt(sbjt_id)
            else:
                sbjt_name=input("Get the details of the sbuject by searching by the subject's name:" )
                search=view_sbjt(sbjt_name)
                for search in search:
                    print(search)
                print("Please take note of Course's ID")
                sbjt_id = input("Enter course's ID: ")
                delete_sbjt(sbjt_id)
        elif m04_choice == "4":
            print("Going back to Main Menu.")
            break
        else:
            print("Invalid Input. Going back to Main Menu.")
            break

"""Function for getting the relevant course id for the subject record"""
def sbjt_crseid_chk():
    sbjt_info_check = input("Do you know the details of the course this subject is under? (Y/N): ").upper()
    if sbjt_info_check == "Y":
        sbjt_crse_id = input("Please enter the course ID:")
    else:
        crsid_check = input("Do you know the Course's ID? (Y/N)").upper()
        if crsid_check == "Y":
            sbjt_crse_id = input("Enter Course's ID: ")
        else:
            crse_name = input("Get the details of the course by searching by the course's name: " )
            search=view_crse(crse_name)
            for search in search:
                print(search)
            sbjt_crse_id = input("Enter Course's ID: ")
    return sbjt_crse_id

"""Function for getting the relevant instructor id for the subject record"""
def sbjt_instid_chk():
    instid_check = input("Do you know the Instructor's ID? (Y/N)").upper()
    if instid_check == "Y":
        inst_id = input("Enter Instructor's ID: ")
    else:
        inst_name = input("Get the details of the instructor by searching by the instructor's name: " )
        search=view_inst(inst_name)
        for search in search:
            print(search)
        inst_id = input("Enter Instructor's ID: ")
    return inst_id

"""Function for adding subject records"""
def add_sbjt(sbjt_name,sbjt_sched,sbjt_crse_id,sbjt_inst_id):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO subjects (sbjt_name, sbjt_sched, crse_id, inst_id ) VALUES (?,?,?,?)", (sbjt_name,sbjt_sched,sbjt_crse_id,sbjt_inst_id))
        conn.commit()
        print(" Subject added successfully.")
    except sqlite3.Error as e: 
        print(f"An error occurred during adding of the record: {e}")
        conn.rollback() # Rollback if an error occurred
    conn.close()

    """Function for viewing course records based on course Name wild card search"""
def view_sbjt(sbjt_name):
    conn = create_connection()
    cursor = conn.cursor()
    search_pattern = f"%{sbjt_name}%"
    search_query = f"""SELECT s.sbjt_id Subject_ID,
                                s.sbjt_name Subject,
                                s.sbjt_sched Schedule,
                                c.crse_name Course,
                                i.inst_name Instructor,
                                i.inst_id Instructo_ID
                           FROM subjects s, 
                                courses c,
                                instructors i 
                          WHERE s.crse_id = c.crse_id 
                            AND s.inst_id = i.inst_id 
                            AND s.sbjt_name LIKE ?
                    """
    cursor.execute(search_query,(search_pattern,))
    # Get Column Names (Aliases) from cursor.description
    rows = cursor.fetchall()
    if rows :
        print("Record found from subject table.")
    else:
        print(f"No record for '{sbjt_name}' exists.")
    if cursor.description:
        column_aliases = [description[0] for description in cursor.description]
    else:
        print("No cursor description available.")
    # Fetch and print data using aliases as headers
    print(column_aliases)
    conn.close()
    return rows

"""Function for deleting course's records based on course ID """
def delete_sbjt(sbjt_id):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM subjects WHERE sbjt_id = ?", (sbjt_id))
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