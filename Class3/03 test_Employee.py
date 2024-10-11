#####################################################################
# author:       anky
# date:         7th March, 2023
# description:  unit test file for the Employee, Faculty and Staff
# classes which are part of a CSC/CYEN 132 programming assignment.
#####################################################################

import unittest         # import the unittest library
from Program3 import *  # import all classes from the Employee.py file

# A class to test the Employee class.
class TestEmployee(unittest.TestCase):

    # A function to test and see whether Employee is in fact an abstract
    # class
    def test_abstractCreation(self):
        with self.assertRaises(TypeError):
            Employee("Jay", "Walker", 200000)

    # A function to test and see if the state of an Employee is properly
    # set during its creation.
    def test_employeeState01(self):
        Employee.__abstractmethods__ = set()
        e1 = Employee("Kay", "Oss", 35000)

        self.assertEqual(e1.firstname, "Kay", "firstname instance variable incorrect")
        self.assertEqual(e1.lastname, "Oss", "lastname instance variable incorrect")
        self.assertEqual(e1.pay, 35000, "pay instance variable incorrect")
        self.assertEqual(e1.email, "kay.oss@latech.edu", "email instance variable incorrect")
        self.assertEqual(e1.position, None, "position instance variable incorrect")
        self.assertEqual(str(e1), "Oss, Kay (kay.oss@latech.edu)", "__str__ function incorrect")

        # check to see that the applyRaise function raises a
        # NotImplementedError
        with self.assertRaises(NotImplementedError):
            e1.applyRaise(3.5)

    # A function to test and see if the range checking and input
    # validation is carried out during object creation
    def test_employeeState02(self):
        e2 = Employee("lEe ", " vitoFF ", 15000)
        e2.position = "President"

        self.assertEqual(e2.firstname, "Lee", "firstname instance variable incorrect")
        self.assertEqual(e2.lastname, "Vitoff", "lastname instance variable incorrect")
        self.assertEqual(e2.pay, 20000, "pay instance variable incorrect")
        self.assertEqual(e2.email, "lee.vitoff@latech.edu", "email instance variable incorrect")
        self.assertEqual(e2.position, "President", "position instance variable incorrect")
        self.assertEqual(str(e2), "Vitoff, Lee (lee.vitoff@latech.edu)", "__str__ function incorrect")

        # more range checking testing
        e2.pay = 30000
        e2.email = "anotherone@email.latech.edu"
        e2.firstname = " paigE"
        e2.lastname = "TuRnEr"

        self.assertEqual(e2.firstname, "Paige", "firstname instance variable incorrect")
        self.assertEqual(e2.lastname, "Turner", "lastname instance variable incorrect")
        self.assertEqual(e2.pay, 30000, "pay instance variable incorrect")
        self.assertEqual(e2.email, "lee.vitoff@latech.edu", "email instance variable incorrect")
        self.assertEqual(e2.position, "President", "position instance variable incorrect")

        e2.pay = 10000
        e2.email = "anotherone@latech.edu"
        self.assertEqual(e2.email, "anotherone@latech.edu", "email instance variable incorrect")
        self.assertEqual(e2.pay, 20000, "pay instance variable incorrect")

        self.assertEqual(str(e2), "Turner, Paige (anotherone@latech.edu)", "__str__ function incorrect")


# A class to test the Employee class.
class TestFaculty(unittest.TestCase):

    # A function to set up an instance of the Faculty object that will
    # be tested repeatedly.
    def setUp(self):
        self.f1 = Faculty("Bennie", "Factor", "Lecturer")

    # a function to test and see whether the Faculty object is properly
    # created.
    def test_Faculty(self):
        self.assertIsInstance(self.f1, Employee, "Looks like Faculty is not a subclass of Employee")
        self.assertEqual(self.f1.firstname, "Bennie", "instance variables not set accurately")
        self.assertEqual(self.f1.lastname, "Factor", "instance variables not set accurately")
        self.assertEqual(self.f1.pay, 50000, "instance variables not set accurately")
        self.assertEqual(self.f1.email, "bennie.factor@latech.edu", "instance variables not set accurately")
        self.assertEqual(self.f1.position, "Lecturer", "instance variables not set accurately")
        self.assertEqual(str(self.f1), "Factor, Bennie (bennie.factor@latech.edu) -- Lecturer", "__str__ function incorrect")

    # A function to test and see whether the Faculty applyRaise function
    # works properly.
    def test_raises(self):
        self.f1.applyRaise(5)
        self.assertAlmostEqual(self.f1.pay, 250000, msg = "incorrect apply raise function")
        self.f1.applyRaise(-5)
        self.assertAlmostEqual(self.f1.pay, 250000, msg = "incorrect apply raise function")
        

# A class to test the Staff class.
class TestStaff(unittest.TestCase):

    # A function to set up an instance of the Faculty object that will
    # be tested repeatedly.
    def setUp(self):
        self.s1 = Staff("Chester", "Minit")

    # a function to test and see whether the Faculty object is properly
    # created.
    def test_Staff(self):
        self.assertIsInstance(self.s1, Employee, "Looks like Staff is not a subclass of Employee")
        self.assertEqual(self.s1.firstname, "Chester", "instance variables not set accurately")
        self.assertEqual(self.s1.lastname, "Minit", "instance variables not set accurately")
        self.assertEqual(self.s1.pay, 40000, "instance variables not set accurately")
        self.assertEqual(self.s1.email, "chester.minit@latech.edu", "instance variables not set accurately")
        self.assertEqual(self.s1.position, None, "instance variables not set accurately")
        self.assertEqual(str(self.s1), "Minit, Chester (chester.minit@latech.edu)", "__str__ function incorrect")

        self.s1.position = "Grant Administrator"
        self.assertEqual(self.s1.position, "Grant Administrator", "instance variables not set accurately")

    # A function to test and see whether the Faculty applyRaise function
    # works properly.
    def test_raises(self):
        self.s1.applyRaise(10000)
        self.assertAlmostEqual(self.s1.pay, 50000, msg = "incorrect apply raise function")
        self.s1.applyRaise(-5000)
        self.assertAlmostEqual(self.s1.pay, 50000, msg = "incorrect apply raise function")


if __name__ == "__main__":
    unittest.main()
