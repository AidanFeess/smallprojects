#####################################################################
# author: Aidan Feess
# date: 4/24/2024
# description:
#####################################################################

# Don't forget to name this file Height.py and place it in the same
# folder as the provided HeightTest.py file so that they can
# automatically find and use each other.

from math import floor

class Height:
    # A constructor that takes in two arguments for the ft and inch
    # respectively. Default values for both parameters are 0.
    def __init__(self, feet=0, inch=0):
        self.feet = feet
        self.inch = inch

    ####### Accessors and mutators for instance variables ###########
    @property
    def feet(self):
        return self._feet
    @feet.setter
    def feet(self, value):
        # dont allow numbers less than 0 for feet
        self._feet = value if value > 0 else 0
    
    @property
    def inch(self):
        return self._inch
    @inch.setter
    def inch(self, value):
        if value < 0:
            value = 0
        elif value > 12:
            # add inches in excess of 12 to feet and keep remainder
            while value > 12:
                value -= 12
                self._feet += 1
        self._inch = value

    ######### other functions e.g. __str__ and inches ###############

    def inches(self):
        return (self._feet * 12) + self._inch

    def __str__(self):
        return f'''{self.feet}' {self.inch}"'''
    
    ####### overloaded mathematical and comparison operators ########
    ############## i.e. +, -, <, <=, >, >=, ==, != ##################

    def __add__(self, object):
        return Height(0, self.inches() + object.inches())
    
    def __sub__(self, object):
        return Height(0, self.inches() - object.inches())
    
    def __lt__(self, object):
        return self.inches() < object.inches()
    
    def __le__(self, object):
        return self.inches() <= object.inches()
    
    def __gt__(self, object):
        return self.inches() > object.inches()
    
    def __ge__(self, object):
        return self.inches() >= object.inches()
    
    def __eq__(self, object):
        return self.inches() == object.inches()
    
    def __ne__(self, object):
        return not self.__eq__(object)