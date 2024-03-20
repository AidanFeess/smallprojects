####################################################################
# name: Aidan Feess
# date: 1/5/2024
# description: Calculate annual compound intrest
####################################################################
# A function that receives no arguments, prompts the user for their
# name, and returns that value to the calling statement.
def GetUserName():
    return input("Please enter your name: ")
# A function that receives a single argument (a string that describes a
# piece of data), prompts the user for that data, and then returns the
# data to the calling statement.
def GetData(data):
    return input(f"Please enter the {data}: ")
# A function that receives three arguments that represent the principal
# amount, annual compound interest rate, and the number of years, and
# returns the total amount after compound interest growth.
def Calculate(principal, rate, num_of_years):
    return principal * (1+(rate / 100)) ** num_of_years
###################### MAIN #########################
# using the function(s) above as appropriate, complete the algorithm
# below.
# prompt the user for their name
name = GetUserName()
# prompt the user for the principal amount, annual compound interest
principal = float(GetData("principal"))
# rate, and number of years
rate = float(GetData("annual percentage rate"))
num_of_years = float(GetData("number of years"))
# Calculate the total amount
total = Calculate(principal, rate, num_of_years)
# Print out the final amount
print(f"Hello {name}, the final amount after {num_of_years} years at {rate} is ${total}")