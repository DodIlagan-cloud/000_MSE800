"""Week 2 - Activity 6 : Develop a basic HR project using OO
You are tasked with developing a simple program for the Human Resources (HR) department to store and display basic employee information, 
including each employee’s name, salary, and job title.
Requirements:
Create at least two Employee objects with different data.
Call the display_info() method to show each employee’s details.
Call the give_raise() method to increase an employee’s salary and display the updated amount.
Upload your completed project to GitHub and share the repository link by Friday, 15.8.25, 11:59 PM.
W2A6_HR_Project.py - Week 2 Activity 6
Eduardo JR Ilagan

"""

# Class that displalys (display_info()) the information and process the raise (give_raise()) of the employees.
class HRApp:  
    def __init__(self,emp_detail):
        self.emp_detail = emp_detail
#function under the HR Application app for the display
    def display_info(self,emp_detail):
        name=emp_detail[0]
        title=emp_detail[1]
        salary=emp_detail[2]
        print("Name:",name)
        print("Title:",title)
        print("Salary:",salary)
        return name,title,salary
#function under the HR Application app for the raise
    def give_raise(self,salary,sal_raise):
        new_sal = int(salary)*(1+(int(sal_raise))/100)
        return new_sal

#function that gets the data of the employees and stores it in an array
def get_info():
    employees = []
    print("Please add your employees")
    while True:
        e_name = input("Add Name: ")
        e_title = input("Title: ")
        e_salary = input("Salary: ")
        employees.append([e_name,e_title,e_salary])
        addanother = input("Add another employee? Y/N:".strip())
        if addanother.upper() != "Y":
            break
    #employees =  [["Edu Ilagan","Gen Manager","120000"],["Dod Ilagan","CIO","150000"]] #(Test Data)
    return employees

#main function"""
def main():
    employees=get_info() # function call to get the employee information
    emp_rowid = 0 # row counter for the employees list
    #main loop for processing employees"""
    for emp_row in employees:
        hrapp = HRApp(emp_row)
        emp_row=hrapp.display_info(emp_row)
        give_raise = input("Would you like to give him a raise? Y/N:".strip())
        if give_raise.upper() == "Y":
            how_much = input("How much? enter percentage (e.g.10 for 10%):")
            new_sal = hrapp.give_raise(emp_row[2],how_much)
            print(emp_row[0],"'s Salary has increased to ",new_sal)
            employees[emp_rowid][2]=new_sal
        else:
            print("No raise for ",emp_row[0])
        emp_rowid +=1 # iteration for the next row
    #displays the data of the employees after the raise"""
    for emp_row in employees:
        hrapp = HRApp(emp_row)
        emp_row=hrapp.display_info(emp_row)

if __name__ == "__main__":
    main()