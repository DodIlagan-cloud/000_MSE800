
"""Week 3 - Activity 5: update the sample code "Sample_code_SQLite3"
Please add a new table named "Students" with three columns: Stu_ID, Stu_name, and Stu_address. 
Insert two sample records into Students, then display all rows from both the Users and Students tables.
main.py - Week 3 Activity 5
Eduardo JR Ilagan
"""



from database import create_table
from database import create_student_table
from user_manager import add_user, view_users, search_user, delete_user, add_Student, view_Students

def menu():
    print("\n==== User Manager ====")
    print("1. Add User")
    print("2. View All Users")
    print("3. Search User by Name")
    print("4. Delete User by ID")
    # Start EJP W3A5
    print("5. Add Student")
    print("6. Display All Records")
    print("7. Exit")
    # End EJP W3A5    
def main():
    create_table()
    create_student_table()
    while True:
        menu()
        choice = input("Select an option (1-5): ")
        if choice == '1':
            name = input("Enter name: ")
            email = input("Enter email: ")
            add_user(name, email)
        elif choice == '2':
            users = view_users()
            for user in users:
                print(user)
        elif choice == '3':
            name = input("Enter name to search: ")
            users = search_user(name)
            for user in users:
                print(user)
        elif choice == '4':
            user_id = int(input("Enter user ID to delete: "))
            delete_user(user_id)
        # Start EJP W3A5
        if choice == '5':
            name = input("Enter Student name: ")
            address = input("Enter Student Address: ")
            add_Student(name, address)
        if choice == '6':
            users = view_users()
            for user in users:
                print(user)
            Students = view_Students()
            for Students in Students:
                print(Students)
        elif choice == '7':
        #elif choice == '5':
        # End  EJP W3A5
            print("Goodbye!")
            break
        else:
            print("Invalid choice, try again.")

if __name__ == "__main__":
    main()
