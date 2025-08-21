"""Week 3 - Activity 6: Develop the python code for Week 3 - Activity 4
Use the sample code to develop a command-line application for Week 3 - Activity 4, incorporating a database sqlite3 
and have at least three functionality such as add records, delete records and view records for different tables.
Share the completed project on GitHub here, with including a README.txt file in your repository to describe the technical aspects of this project (Yoobee Colleges).

YSclsrec_view.py - Week 3 Activity 6 - W3A6 - EJI
Eduardo JR Ilagan
"""

import sqlite3
from YSDatabase import create_connection
from YSinst_manager import view_inst
from YSstu_manager import view_student
from YSsbjt_manager import view_sbjt
from YScrse_manager import view_crse


def clsrec_view():
    while True:
        print("\n====== Yoobee Class Record View Menu ======")
        print("For which information are you looking for?")
        print("1. View by Student")
        print("2. View by Instructor")
        print("3. View by Subject")
        print("4. Go Back to Last Menu")
        m060_choice = input("Select an option (1-4): ")
        if m060_choice == "1":
            clsrec_stuid = clsrec_stuid_chk()
            search=clsrec_v_stuid(clsrec_stuid)
        elif m060_choice == "2":
            clsrec_instid = clsrec_instid_chk() 
            search=clsrec_v_instid(clsrec_instid)
        elif m060_choice == "3":
            clsrec_sbjtid = clsrec_sbjtid_chk()
            search=clsrec_v_sbjtid(clsrec_sbjtid)
        elif m060_choice == "5":
            print("Going back to Previuos Menu.")
            break
        else:
            print("Invalid Input. Going back to Previous Menu.")
            break
        for search in search:
            print(search)

"""Function for getting the relevant course id for the subject records"""
def clsrec_crseid_chk():
    instid_check = input("Do you know the Course's ID this record is for? (Y/N)").upper()
    if instid_check == "Y":
        inst_id = input("Please enter Course's ID: ")
    else:
        inst_name = input("Get the details of the course by searching using the course's name: " )
        search=view_crse(inst_name)
        for search in search:
            print(search)
        inst_id = input("Enter Course's ID: ")
    return inst_id

"""Function for viewing class records based on Course ID """
def clsrec_v_crseid(clsrec_crseid):
    conn = create_connection()
    cursor = conn.cursor()
    search_pattern = f"{clsrec_crseid}"
    search_query = f"""SELECT c.crse_id Course_ID
                                c.crse_name Course,
                                c.crse_timeframe Course_Intake,
                                s.sbjt_name Subject,
                                i.inst_name Instructor,
                                s.sbjt_sched Schedule,
                                st.stu_name Student
                           FROM subjects s, 
                                courses c,
                                instructors i,
                                class_records cl,
                                students st
                          WHERE cl.sbjt_id = s.sbjt_id
                            AND cl.inst_id = i.inst_id
                            AND cl.stu_id = st.stu_id
                            AND s.crse_id = c.crse_id 
                            AND s.inst_id = i.inst_id 
                            AND c.crse_id = ?
                    """
    cursor.execute(search_query,(search_pattern,))
    # Get Column Names (Aliases) from cursor.description
    rows = cursor.fetchall()
    if rows :
        print("Record found from record.")
    else:
        print(f"No record for Instructor ID'{clsrec_crseid}' exists.")
    if cursor.description:
        column_aliases = [description[0] for description in cursor.description]
    else:
        print("No cursor description available.")
    # Fetch and print data using aliases as headers
    print(column_aliases)
    conn.close()
    return rows

"""Function for viewing class records based on course Student ID """
def clsrec_v_stuid(clsrec_stuid):
    conn = create_connection()
    cursor = conn.cursor()
    search_pattern = f"{clsrec_stuid}"
    search_query = f"""SELECT st.stu_id Student_ID,
                                st.stu_name Student,
                                cl.marking Markings,
                                s.sbjt_name Subject,
                                s.sbjt_sched Schedule,
                                c.crse_name Course,
                                i.inst_name Instructor
                           FROM subjects s, 
                                courses c,
                                instructors i,
                                class_records cl,
                                students st
                          WHERE cl.sbjt_id = s.sbjt_id
                            AND cl.inst_id = i.inst_id
                            AND cl.stu_id = st.stu_id
                            AND s.crse_id = c.crse_id 
                            AND s.inst_id = i.inst_id 
                            AND cl.stu_id = ?
                    """
    cursor.execute(search_query,(search_pattern,))
    # Get Column Names (Aliases) from cursor.description
    rows = cursor.fetchall()
    if rows :
        print("Record found in system.")
    else:
        print(f"No record for Student ID'{clsrec_stuid}' exists.")
    if cursor.description:
        column_aliases = [description[0] for description in cursor.description]
    else:
        print("No cursor description available.")
    # Fetch and print data using aliases as headers
    print(column_aliases)
    conn.close()
    return rows

"""Function for viewing class records based on course Instructors ID """
def clsrec_v_instid(clsrec_instid):
    conn = create_connection()
    cursor = conn.cursor()
    search_pattern = f"{clsrec_instid}"
    search_query = f"""SELECT i.inst_id Instructor_ID,
                                i.inst_name Instructor,
                                s.sbjt_name Subject,
                                s.sbjt_sched Schedule,
                                c.crse_name Course,
                                st.stu_name Student
                           FROM subjects s, 
                                courses c,
                                instructors i,
                                class_records cl,
                                students st
                          WHERE cl.sbjt_id = s.sbjt_id
                            AND cl.inst_id = i.inst_id
                            AND cl.stu_id = st.stu_id
                            AND s.crse_id = c.crse_id 
                            AND s.inst_id = i.inst_id 
                            AND cl.inst_id = ?
                    """
    cursor.execute(search_query,(search_pattern,))
    # Get Column Names (Aliases) from cursor.description
    rows = cursor.fetchall()
    if rows :
        print("Record found from record.")
    else:
        print(f"No record for Instructor ID'{clsrec_instid}' exists.")
    if cursor.description:
        column_aliases = [description[0] for description in cursor.description]
    else:
        print("No cursor description available.")
    # Fetch and print data using aliases as headers
    print(column_aliases)
    conn.close()
    return rows

"""Function for viewing class records based on Subject ID """
def clsrec_v_sbjtid(clsrec_sbjtid):
    conn = create_connection()
    cursor = conn.cursor()
    search_pattern = f"{clsrec_sbjtid}"
    search_query = f"""SELECT s.sbjt_id Subject_ID,
                                s.sbjt_name Subject,
                                i.inst_name Instructor,
                                s.sbjt_sched Schedule,
                                c.crse_name Course,
                                st.stu_name Student
                           FROM subjects s, 
                                courses c,
                                instructors i,
                                class_records cl,
                                students st
                          WHERE cl.sbjt_id = s.sbjt_id
                            AND cl.inst_id = i.inst_id
                            AND cl.stu_id = st.stu_id
                            AND s.crse_id = c.crse_id 
                            AND s.inst_id = i.inst_id 
                            AND cl.sbjt_id = ?
                    """
    cursor.execute(search_query,(search_pattern,))
    # Get Column Names (Aliases) from cursor.description
    rows = cursor.fetchall()
    if rows :
        print("Record found from record.")
    else:
        print(f"No record for Instructor ID'{clsrec_sbjtid}' exists.")
    if cursor.description:
        column_aliases = [description[0] for description in cursor.description]
    else:
        print("No cursor description available.")
    # Fetch and print data using aliases as headers
    print(column_aliases)
    conn.close()
    return rows

"""Function for getting the relevant student id for the class record"""
def clsrec_stuid_chk():
    clsrec_info_chk = input("Do you know the Student ID this record is for? (Y/N): ").upper()
    if clsrec_info_chk == "Y":
        clsrec_stu_id = input("Please enter Student's ID: ")
    else:
        stu_name = input("Get the details of the student by searching by the student's name: ")
        search=view_student(stu_name)
        for search in search:
            print(search)
        if search == "":
            print("There are no records for Student's name: '{stu_name}' ")
        else:
            print("Please take note of Student's ID")
            clsrec_stu_id = input("Enter student's ID: ")            
    return clsrec_stu_id



"""Function for getting the relevant instructor id for the subject record"""
def clsrec_instid_chk():
    instid_check = input("Do you know the Instructor's ID this record is for? (Y/N)").upper()
    if instid_check == "Y":
        inst_id = input("Please enter Instructor's ID: ")
    else:
        inst_name = input("Get the details of the instructor by searching by the instructor's name: " )
        search=view_inst(inst_name)
        for search in search:
            print(search)
        inst_id = input("Enter Instructor's ID: ")
    return inst_id

"Function for getting the relevant subject id for the class record"""
def clsrec_sbjtid_chk():
    clsrec_info_check = input("Do you know the details of the subject this record is for? (Y/N): ").upper()
    if clsrec_info_check == "Y":
        clsrec_sbjt_id = input("Please enter the subject ID:")
    else:
        clsrec_sbjtid_check = input("Do you know the subject's ID? (Y/N)").upper()
        if clsrec_sbjtid_check == "Y":
            clsrec_sbjt_id = input("Please enter subject's ID: ")
        else:
            sbjt_name = input("Get the details of the subject by searching by the subject's name: " )
            search=view_sbjt(sbjt_name)
            for search in search:
                print(search)
            clsrec_sbjt_id = input("Please enter Subject's ID: ")
    return clsrec_sbjt_id