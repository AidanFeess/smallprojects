#############################################################################
# author: Aidan Feess
# date: 12 / 15 / 2023
# description: Gets a user's name, income, and taxrate to calculate their net income
#############################################################################

# A statement that prompts the user for their name
name = input("Please enter your name: ")

# Statements that prompt the user for their annual income and tax rate
income = int(input(f"Hello {name}, What is your gross annual income? "))
taxrate = float(input("What is the percentage tax rate in your location? "))

# Calculate the user's net income and display final output.
print(f"Well {name}, that means that your net income is ${income-(income*(taxrate*.01))}")