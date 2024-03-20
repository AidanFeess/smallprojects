def double(x):
    return 2*x

def power(a,b):
    return a**b

def average(a,b,c):
    return (a+b+c)/3

def mymax(a,b):
    return a if a > b else b

def square(x):
    return x**2

def join(a,b):
    return a+b

def isin(a,b):
    return str.find(a, b)!=-1

def iseven(a):
    return a%2==0

def cube(x):
    return x**3

def divide(a, b):
    return a/b if b > 0 else "undefined"

def greet(x):
    return f"Hello {x}"

def celstofahr(x):
    return (x*9/5)+32

def lbstokgs(x):
    return x/2.205

def isPrime(x):
    if x <= 1: return False
    for n in range(2, x):
        if x%n==0: 
            return False
    return True