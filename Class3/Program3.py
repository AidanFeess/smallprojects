#####################################################################
# author: Aidan Feess
# date: 10/08/2024
# description:
#####################################################################
# import the abc library to make abstract classes
from abc import ABC, abstractmethod
######################################################################
# An employee class. Its constructor takes the first name, last name and
# pay. It also has email and position as instance variables. It contains
# a single abstract method i.e. applyRaise, and a createEmail function
# that creates an appropriate email address from the employee's first
# and last names.
class Employee(ABC):
    
    def __init__(self, firstname: str, lastname: str, pay: int):
        self.firstname = firstname
        self.lastname = lastname
        self.pay = pay
        self.email = ""
        self.email = self.createEmail()
        self.position = None

    @property
    def firstname(self):
        return self._firstname
    
    @firstname.setter
    def firstname(self, value):
        # Sanitize the firstname
        SanitizedName = str.strip(value)
        SanitizedName = str.upper(SanitizedName[0]) + str.lower(SanitizedName[1:])
        self._firstname = SanitizedName

    @property
    def lastname(self):
        return self._lastname
    
    @lastname.setter
    def lastname(self, value):
        # Sanitize the lastname
        SanitizedName = str.strip(value)
        SanitizedName = str.upper(SanitizedName[0]) + str.lower(SanitizedName[1:])
        self._lastname = SanitizedName

    @property
    def pay(self):
        return self._pay
    
    @pay.setter
    def pay(self, value):
        # cap the pay at >= 20000
        if value < 20000:
            self._pay = 20000
        else:
            self._pay = value

    @property
    def email(self):
        return self._email
    
    @email.setter
    def email(self, value):
        
        if not str.endswith(value[str.find(value, "@"):], "@latech.edu"):
            self._email = self.createEmail()
        else:
            self._email = value

    def createEmail(self):
        return f"{str.lower(self._firstname)}.{str.lower(self._lastname)}@latech.edu"

    def __str__(self):
        return f"{self._lastname}, {self._firstname} ({self._email})"

    @abstractmethod
    def applyRaise(self, rate: int):
        raise NotImplementedError

######################################################################
######################################################################
# A faculty class is a subclass of the Employee class above. Its
# constructor receives both names as well as the position. The Faculty
# class also overrides the applyRaise function by multiplying the pay by
# the rate provided as an argument. It also slightly tweaks the __str__
# function in the super class.
class Faculty(Employee):
    
    def __init__(self, firstname: str, lastname: str, position: str):
        super().__init__(firstname, lastname, pay=50000)
        self.position = position

    def applyRaise(self, rate: int):
        if rate <= 0:
            return
        self.pay *= rate

    def __str__(self):
        return super().__str__() + f" -- {self.position}"
######################################################################
######################################################################
# A Staff class is a subclass of the Employee class above. Its
# constructor only receives both names. It also overrides the applyraise
# function but adding the increase (provided as the argument) to the
# pay. It doesn't change anything else from the Employee class.
######################################################################
class Staff(Employee):
    
    def __init__(self, firstname: str, lastname: str):
        super().__init__(firstname, lastname, pay=40000)
    
    def applyRaise(self, rate: int):
        if rate <= 0:
            return
        self.pay += rate