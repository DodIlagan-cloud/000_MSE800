"""Week 3 - Activity 6: Develop the python code for Week 3 - Activity 4
Use the sample code to develop a command-line application for Week 3 - Activity 4, incorporating a database sqlite3 
and have at least three functionality such as add records, delete records and view records for different tables.
Share the completed project on GitHub here, with including a README.txt file in your repository to describe the technical aspects of this project (Yoobee Colleges).

YSCourse.py - Week 3 Activity 6 - W3A6 - EJI
Eduardo JR Ilagan
"""

from YSDatabase import create_connection
import sqlite3

def menu_03_crse():
    while True:
        print("\n==== Yoobee Course Menu ====")
        print("1. Add Course")
        print("2. View Course")
        print("3. Delete Course Record")
        print("4. Go Back to Last Menu")
        m03_choice = input("Select an option (1-4): ")
        if m03_choice == "1":
            crse_name = input("Course Name: ")
            crse_tframe = input("Pleae enter the year (YYYY) and intake month (MM) (e.g. 202304 for 2023 April): ")
            add_crse(crse_name,crse_tframe)
        elif m03_choice == "2":
            crse_name = input("Enter Course Name: ")
            search=view_crse(crse_name)
            for search in search:
                print(search)
        elif m03_choice == "3":
            rec_info_check = input("Do you know the details of the record you wish to delete? (Y/N): ").upper()
            if rec_info_check == "Y":
                crsid_check = input("Do you know the Course's ID? (Y/N)").upper()
                if crsid_check == "Y":
                    crse_id = input("Enter Course's ID: ")
                    delete_crse(crse_id)
                else:
                    crse_name = input("Enter Name: ")
                    search=view_crse(crse_name)
                    for search in search:
                        print(search)
                    crse_id = input("Enter Course's ID: ")
                    delete_crse(crse_id)
            else:
                crse_name=input("Get the details of the course by searching by the course's name:" )
                search=view_crse(crse_name)
                for search in search:
                    print(search)
                print("Please take note of Course's ID")
                crse_id = input("Enter course's ID: ")
                delete_crse(crse_id)
        elif m03_choice == "4":
            print("Going back to Main Menu.")
            break
        else:
            print("Invalid Input. Going back to Main Menu.")
            break

"""Function for adding Course records"""
def add_crse(crse_name,crse_tframe):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO courses (crse_name, crse_timeframe) VALUES (?,?)", (crse_name, crse_tframe ))
        conn.commit()
        print(" Course added successfully.")
    except sqlite3.Error as e: 
        print(f"An error occurred during adding of the record: {e}")
        conn.rollback() # Rollback if an error occurred
    conn.close()

    """Function for viewing course records based on course Name wild card search"""
def view_crse(crse_name):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM courses WHERE crse_name LIKE ?", ('%' + crse_name + '%',))
    rows = cursor.fetchall()
    if rows :
        print("Record found from course table.")
    else:
        print(f"No record for '{crse_name}' exists.")
    if cursor.description:
        column_aliases = [description[0] for description in cursor.description]
    else:
        print("No cursor description available.")
    # Fetch and print data using aliases as headers
    print(column_aliases)
    conn.close()
    return rows

"""Function for deleting course's records based on course ID """
def delete_crse(crse_id):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM courses WHERE crse_id = ?", (crse_id))
        ins_row_count = cursor.rowcount
        if ins_row_count > 0:
            print("Successfully deleted course id ", crse_id,"from the record.")
        else:
            print(" There were no records deleted. Course ID ",crse_id," is not in the records.")
        conn.commit()
    except sqlite3.Error as e: 
        print(f"An error occurred during deletion: {e}")
        conn.rollback() # Rollback if an error occurred
    conn.close()