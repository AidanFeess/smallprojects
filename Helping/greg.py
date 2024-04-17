# Program Name: Lab10
# Course: IT1114/Section W02
# Student Name: Gregory Kelley
# Assignment Number: Lab10
# Due Date: 04/13/2024
# Purpose: These are methods for the data on office workers from their employee number to time worked and salary.
# W3 Schools and Stackoverflow
import datetime

class Worker:
    def __init__(self):
        self.employee_number = None
        self.office_number = None
        self.first_name = None
        self.last_name = None
        self.birthdate = None
        self.total_hours_worked = 0
        self.total_overtime_hours = 0
        self.hourly_salary = 0
        self.overtime_hourly_salary = 0

    def get_employee_number(self):
        return self.employee_number

    def set_employee_number(self, x):
        if not isinstance(x, int):
            raise ValueError("Employee number must be an integer")
        self.employee_number = x

    def get_office_number(self):
        return self.office_number

    def set_office_number(self, x):
        if not (100 <= x <= 500):
            raise ValueError("Office number must be between 100 and 500")
        self.office_number = x

    def get_name(self):
        return f"{self.first_name} {self.last_name}"

    def set_name(self, x):
        if not x:
            raise ValueError("Name cannot be empty")
        invalid_characters = ['_', '.', '-']
        cleaned_name = ''.join(char for char in x if char not in invalid_characters)
        if not cleaned_name:
            raise ValueError("Name cannot consist only of invalid characters")

        split_name = cleaned_name.split(" ", maxsplit=2)

        try:
            self.first_name = split_name[0]
            self.last_name = split_name[1]
        except:
            pass

    def set_birthdate(self, m, d, y):
        if not (1 <= m <= 12):
            raise ValueError("Month must be between 1 and 12")
        if not (1 <= d <= 31):
            raise ValueError("Day must be between 1 and 31")
        self.birthdate = datetime.date(y, m, d)

    def get_hours_worked(self):
        return self.total_hours_worked

    def add_hours(self, x):
        if x < 0:
            raise ValueError("Number of hours being added cannot be less than 0")
        if x > 9:
            self.total_hours_worked += 9
            self.total_overtime_hours += x - 9
        else:
            self.total_hours_worked += x

    def get_hours_overtime(self):
        return self.total_overtime_hours

    def set_hourly_salary(self, x):
        if x < 0:
            raise ValueError("Hourly salary cannot be less than 0")
        self.hourly_salary = x

    def set_overtime_salary(self, x):
        if x < 0:
            raise ValueError("Overtime hourly salary cannot be less than 0")
        self.overtime_hourly_salary = x

    def get_hourly_salary(self):
        return self.hourly_salary

    def get_overtime_salary(self):
        return self.overtime_hourly_salary

    def get_pay(self):
        return (self.total_hours_worked * self.hourly_salary) + (self.total_overtime_hours * self.overtime_hourly_salary)