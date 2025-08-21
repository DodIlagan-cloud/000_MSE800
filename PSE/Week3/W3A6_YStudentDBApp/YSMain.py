"""Week 3 - Activity 6: Develop the python code for Week 3 - Activity 4
Use the sample code to develop a command-line application for Week 3 - Activity 4, incorporating a database sqlite3 
and have at least three functionality such as add records, delete records and view records for different tables.
Share the completed project on GitHub here, with including a README.txt file in your repository to describe the technical aspects of this project (Yoobee Colleges).

YSMain.py - Week 3 Activity 6 - W3A6 - EJI
Eduardo JR Ilagan
"""

from YSDatabase import create_tables
from YSstu_manager import menu_01_stu
from YSinst_manager import menu_02_inst
from YScrse_manager import menu_03_crse
from YSsbjt_manager import menu_04_sbjt
from YSpay_manager import menu_05_pay
from YSclsrec_manager import menu_06_clsrec

"""Function for Main Menu"""
def menu_0():
    print("1. Students")
    print("2. Instructor")
    print("3. Course")
    print("4. Subject")
    print("5. Payment Records")
    print("6. Class Records")
    print("7. Exit")

def main():
    create_tables()
    while True:
        print("\n========= Yoobee Student Database =========")
        menu_0()
        m0_choice = input("Select an option (1-7): ")
        if m0_choice == "1":
            menu_01_stu()
        elif m0_choice == "2":
            menu_02_inst()
        elif m0_choice == "3":
            menu_03_crse()
        elif m0_choice == "4":
            menu_04_sbjt()
        elif m0_choice == "5":
            menu_05_pay()
        elif m0_choice == "6":
            menu_06_clsrec()
        elif m0_choice == "7":
            print("Thank you for using Dod's Yoobee Student Database.")
            break
        else:
            print("Invalid choice, try again.")
            break
if __name__ == "__main__":
    main()