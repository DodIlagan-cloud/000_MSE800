"""
Can you add one more method to the class that uses the private attribute? 
Also, please create a new class to demonstrate the use of the public and protected attributes. See attached file. See slide 3 : 
"""

class Student:
    def __init__(self, name, age):
        self.name = name       # public
        self._age = age        # protected
        self.__grade = 'A'     # private

    def get_grade(self):
        return self.__grade
    
    def chng_grade(self): # Additional Method to modify the grade
        self.__grade = input("Enter Grade: ")
        return self.__grade
    


    def updt_age(self):
        self._age = input("Enter Age: ")
        return self._age

class Instructor:
    def __init__(self, name, age):
        self.name = name       # public
        self._age = age        # protected
        self.__inst_id = 234     # private
    def get_isntid(self):
        return self.__inst_id
    
    def updt_age(self):
        self._age = input("Enter Age: ")
        return self._age



s = Student('Ali', 20)
print(s.name)         # accessible
print(s._age)         # discouraged
print(s.get_grade())  # correct way
print("Assigninig to Private Variable")
#s.__grade = "B"  # Assigning new value for the grade does not work as it takes it as a new variable and not the one declared in the class
#print(s.__grade) # Checking for if the value was assinged to the private varaiable, it was not. The variablel is not accessible.
print(s.chng_grade()) # New method can access the private variable to be changed.
print("After Method to update Private Variable")
#print(s.updt_age()) # # New method can access the protected variable to be changed.
#print(s._age)
print(s.__grade) # checking the final value of the private variable.

i = Instructor('Albus', 95)