"""Week 7 Activity 3:  Part 2 - Design Pattern - Factory
What problems might arise if a program directly creates objects with in multiple places instead of using a Factory class? 
See teh attached code. Share the GitHub link with your description.

Answer:
 It appears that the abstract method is used to be able to create classes that are not hard coded. 
 This way utilizes the inheritance and encapsulation features of OOP by having a template from which the classes are based on.
 
Sample_code.py
 """


# New Code - EJI
from abc import ABC, abstractmethod

# 1) Abstract Product
class Shape(ABC):
    @abstractmethod
    def draw(self) -> str:
        """Render the shape and return a description."""
        pass


# 2) Concrete Products
class Circle(Shape):
    def draw(self) -> str:
        return "Drawing a Circle"


class Square(Shape):
    def draw(self) -> str:
        return "Drawing a Square"


# 3) Factory
class ShapeFactory:
    _registry = {
        "circle": Circle,
        "square": Square,
    }

    @classmethod
    def register(cls, name: str, shape_cls: type[Shape]) -> None:
        """Optionally register new shapes without modifying factory code."""
        if not issubclass(shape_cls, Shape):
            raise TypeError("Registered class must inherit from Shape")
        cls._registry[name.lower()] = shape_cls

    @classmethod
    def create(cls, shape_type: str) -> Shape:
        shape_cls = cls._registry.get(shape_type.lower())
        if shape_cls is None:
            raise ValueError(f"Unknown shape type: {shape_type!r}. "
                             f"Available: {', '.join(cls._registry)}")
        return shape_cls()

class Triangle(Shape):
    def draw(self):
        return "Drawing Triangle EJI"
    
# 4) Client code (examples)
if __name__ == "__main__":
    factory = ShapeFactory

    circle = factory.create("circle")
    print(circle.draw())  

    square = factory.create("square")
    print(square.draw()) 

#5 EJI Modification

    factory.register("triangle",Triangle)
    tri = factory.create("triangle")
    print(tri.draw())

"""start Original - EJi
class Circle:
    def draw(self):
        return "Drawing a Circle"

class Square:
    def draw(self):
        return "Drawing a Square"
    
#start EJI
class Triangle:
    def draw(self):
        return "Drawing a Triangle" 
#end EJI

class ShapeFactory:
    def create_shape(self, shape_type):
        if shape_type == "circle":
            return Circle()
        if shape_type == "square":
            return Square()
#start EJI
        if shape_type == "triangle":
            return Triangle()
#end EJI
        else:
            return None


factory = ShapeFactory()
shape = factory.create_shape("triangle")   
print(shape.draw())  
end Original - EJi"""

