#####################################################################
# just a bunch of simple python functions that one can use in their
# programs.
#####################################################################


# a function to return double of the argument it receives
def double(x):
    y = 2 * x
    return y

# a function to return a raised to b
def power(a, b):
    c = a ** b
    return c
    # return a ** b

# a function that returns the average of all its arguments
def average(a, b, c):
    d = (a + b + c)/ 3
    return d


# a function that returns the larger of two values
def mymax(a, b):
    if (a > b):
        return a
    else:
        return b


# a function that returns the square of its arguments
def square(x):
    return x ** 2

#######################################################
# a function that returns the concatenation of two strings
def join(a, b):
    c = str(a) + str(b)
    return c

# a function that tells whether the first string is a part of the second
def isin(a, b):
    if (a in b):
        return True
    else:
        return False
    

# a function to tell whether a number is even
def iseven(a):
    if (a % 2 == 0):
        return True
    else:
        return False

# a function to cube a number
def cube(x):
    return x ** 3

# a function to find the quotient of two numbers
def divide(a, b):
    c = a / b
    return c

######################################################
# a function to greet a person whose name is in the argument
def greet(x):
    #print(f"Hello {x}")
    return f"Hello {x}"

# a function to convert celsius to fahrenheight
def celstofahr(x):
    y = (x * 9 / 5) + 32
    return y

# A function to convert lbs to kgs
def lbstokgs(x):
    return x / 2.205

# a Function to tell whether the argument is a prime number
def isPrime(x):
    i = 2
    while (i < x):
        if (x % i == 0):
            return False
        i += 1
    return True

# a Function to count the number of vowels in a string
def countvowels(a):
    a = a.lower()
    count = a.count("a") + a.count("e") + a.count("i") +\
            a.count("o") + a.count("u")

    return count

# A function to print out menu items from a fictional restaurant.
def displaymenu():
    print("1. eggs")
    print("2. bacon")
    print("3. hashbrowns")
    print("4. coffee")