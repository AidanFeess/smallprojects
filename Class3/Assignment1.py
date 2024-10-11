#####################################################################
# author: Aidan Feess
# date: 09/05/2024
# description: A program that implements a class
#####################################################################
import math
# global Constants to restrict the maximum x and y values that a person object
# can have.
MAX_X = 800
MAX_Y = 600
# A class representing a person. A person can be initialized with a
# name, as well as x and y coordinates. However, there are default
# values for all those (i.e. player 1, 0 and 0 respectively). A person
# also has a size which is set to 1 by default. A person can go left,
# go right, go up and go down. A person also has a string function
# that prints out their name location, and size. A person also has a
# function that calculates the euclidean distance from another person
# object.
class Person:

    # setup of default values
    def __init__(self, name = "player 1", x = 0, y = 0, size = 1):
        self._name = name
        self._x = x
        self._y = y
        self._size = size

        self.name = name
        self.x = x
        self.y = y
        self.size = size

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if type(value) == str:
            if len(value) >= 2:
                self._name = value

    @property
    def x(self):
        return self._x
    
    @x.setter
    def x(self, value):
        if type(value) == int:
            if value < 0:
                self._x = 0
            elif value > MAX_X:
                self._x = MAX_X
            else:
                self._x = value

    @property
    def y(self):
        return self._y
    
    @y.setter
    def y(self, value):
        if type(value) == int:
            if value < 0:
                self._y = 0
            elif value > MAX_Y:
                self._y = MAX_Y
            else:
                self._y = value

    @property
    def size(self):
        return self._size
    
    @size.setter
    def size(self, value):
        if type(value) == float or type(value) == int:
            if value >= 1:
                self._size = value

    # Directional movement, reducing or increasing the desired coordinate by the value variable
    def goLeft(self, value = 1):
        self.x -= value

    def goRight(self, value = 1):
        self.x += value

    def goUp(self, value = 1):
        self.y -= value

    def goDown(self, value = 1):
        self.y += value

    # Function to get the distance between the current person and another person
    def getDistance(self, other: 'Person'):
        '''
        The long way of doing it
        return math.sqrt((other.x - self.x)**2 + (other.y - self.y)**2)
        '''

        return math.dist([self.x, self.y], [other.x, other.y])

    def __str__(self):
        return f"Person({self.name + '):':<15}   size = {str(self.size) + ',':<10}x = {str(self.x) + ',':<10}y = {self.y} "