#####################################################################
# description:  A class to test out the Person class designed in
# CSC/CYEN 132 programming assignment #1
####################################################################

# import everything from the Person file
from Program1 import *

# Create some people
p1 = Person()
p2 = Person("John Doe")
p3 = Person("Jane Doe", 3)
p4 = Person("James Doe", 4, 67)
p3.size = 5
p4.size = 15

print("-" * 60)
print("--People with correct inputs--")
print(f"p1:{p1}")
print(f"p2:{p2}")
print(f"p3:{p3}")
print(f"p4:{p4}")

# Creating some people with wrong input values
p5 = Person("a")
p6 = Person("b", 1000, -600)
p7 = Person("c", -12, 1000)
p7.size = -10

print("-" * 60)
print("--People with wrong inputs--")
print(f"p5:{p5}")
print(f"p6:{p6}")
print(f"p7:{p7}")

# Testing some of the other functions
for i in range(10):
    p1.goLeft()
    p2.goRight()
    p3.goUp()
    p4.goDown()

print("-" * 60)
print("--Testing basic movement--")
print(f"p1:{p1}")
print(f"p2:{p2}")
print(f"p3:{p3}")
print(f"p4:{p4}")
print("-" * 60)
print("--Testing Distance measurement--")
print(f"The distance between p1 and p2 is {p1.getDistance(p2)}")
print(f"The distance between p1 and p3 is {p1.getDistance(p3)}")
print(f"The distance between p1 and p4 is {p1.getDistance(p4)}")
print("-" * 60)

for i in [12, 34, 89, -56, 3]:
    p1.goRight(i)
    p2.goLeft(i)
    p3.goDown(i)
    p4.goUp(i)

print("--Testing more movement--")
print(f"p1:{p1}")
print(f"p2:{p2}")
print(f"p3:{p3}")
print(f"p4:{p4}")
print("-" * 60)
print("--Testing Distance measurement--")
print(f"The distance between p1 and p2 is {p1.getDistance(p2)}")
print(f"The distance between p1 and p3 is {p1.getDistance(p3)}")
print(f"The distance between p1 and p4 is {p1.getDistance(p4)}")
print("-" * 60)

# Testing extreme movement
for i in [200, -500, 700, -1200, 3000]:
    p1.goRight(i)
    p2.goLeft(i)
    p3.goDown(i)
    p4.goUp(i)

print("--Testing extreme movement--")
print(f"p1:{p1}")
print(f"p2:{p2}")
print(f"p3:{p3}")
print(f"p4:{p4}")
print("-" * 60)
print("--Testing Distance measurement--")
print(f"The distance between p1 and p2 is {p1.getDistance(p2)}")
print(f"The distance between p1 and p3 is {p1.getDistance(p3)}")
print(f"The distance between p1 and p4 is {p1.getDistance(p4)}")
print("-" * 60)
