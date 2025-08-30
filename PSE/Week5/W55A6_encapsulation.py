class Student:
    def __init__(self, name, age):
        self.name = name       # public
        self._age = age        # protected
        self.__grade = 'A'     # private

    def get_grade(self):
        return self.__grade

s = Student('Ali', 20)
print(s.name)         # accessible
print(s._age)         # discouraged
print(s.get_grade())  # correct way
