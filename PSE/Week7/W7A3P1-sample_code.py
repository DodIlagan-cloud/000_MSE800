"""Week 7 Activity 3:  Design Pattern - Factory
What problems might arise if a program directly creates objects with in multiple places instead of using a Factory class? 
See teh attached code. Share the GitHub link with your description.

There will be a problem with inconsistent class creation calls. Also, the code could get messy when adding more and the 
standardization of the project wuold not be consistent. 
 
 
Sample_code.py
 """
class Circle:
    def draw(self):
        return "Drawing a Circle"

class Square:
    def draw(self):
        return "Drawing a Square"
    
#start EJP
class Triangle:
    def draw(self):
        return "Drawing a Triangle" 
#end EJP

class ShapeFactory:
    def create_shape(self, shape_type):
        if shape_type == "circle":
            return Circle()
        if shape_type == "square":
            return Square()
#start EJP
        if shape_type == "triangle":
            return Triangle()
#end EJP
        else:
            return None


factory = ShapeFactory()
shape = factory.create_shape("triangle")   
print(shape.draw())  
