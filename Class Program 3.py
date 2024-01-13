####################################################################
# author:
# date:
# description:
####################################################################
# A function that is in charge of prompting the user for any input they
# give. It receives an argument representing the required data, prompts
# the user for that data, and then returns it to the calling statement.
def promptuser(data):
    return input(f'What is the value of "{data}":')
# A function that is in charge of printing out the introductory
# statement(s) for the program.
def print_intro():
    print("This program will calculate the integral of the function 3x^3 - 2x^2 between user defined limits: a and b")
# A function that prints out the statement about the accuracy of delta.
def accurate_print():
    print("The accuracy of this calculation depends on the value of n that you use.")
# A function to evaluate the given mathematical formula at a given
# point. It takes a numerical argument that represents x, and returns
# the result of f(x).
def evaluate_math_function(x):
    return 3 * (x**3) - 2 * (x**2)
# A function that calculates an approximation of the integral of f(x)
# using the riemann sum. It takes three arguments that represent the
# lower limit, the upper limit, and the n value. It then returns the
# integral approximation as a result to the calling statement.
def approximate(lower, upper, n):
    ttl = 0
    for i in range(lower, upper):
        ttl += evaluate_math_function(n)
    return ttl
########################### MAIN ##################################
# In the space below, use the functions defined above to solve the
# problem.
###################################################################
# Print the introductory statements of the program
print_intro()
# Prompt the user for both the lower and upper limits
lower = int(promptuser("a"))
upper = int(promptuser("b"))
# Print the statements about n
accurate_print()
# Prompt the user for the n value
nval = int(promptuser("n"))
# Calculate the integral approximation
# Print out the result.
print(f"The integral over the provided limits is {approximate(lower, upper, nval)}")