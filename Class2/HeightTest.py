#####################################################################
# author:       anky
# date:         2nd Jan, 2023
# description:  A file to test out the Height class.
# Make sure that your Height class design is in a file called Height.py
# and that it is in the same folder as this HeightTest.py file. You will
# only be required to submit the Height.py file for the assignment.
#####################################################################

# DO NOT CHANGE ANYTHING IN THIS FILE. ALL ADJUSTMENTS TO MAKE THIS WORK
# SHOULD BE DONE IN YOUR Height.py FILE WHERE THE HEIGHT CLASS EXISTS.

from Height import *    # Import everything in the Height.py file

# Testing creation and printing of Height objects
h1 = Height(6, 5)
h2 = Height(1, 23)
h3 = Height()
h4 = Height(4)
h5 = Height(0, 77)
h6 = Height(-5, -4)
print(f"h1 = {h1}")
print(f"h2 = {h2}")
print(f"h3 = {h3}")
print(f"h4 = {h4}")
print(f"h5 = {h5}")
print(f"h6 = {h6}")
print("=" * 40)

# Testing inches function
print(f"{h1} is in fact {h1.inches()} inches")
print(f"{h3} is in fact {h3.inches()} inches")
print(f"{h5} is in fact {h5.inches()} inches")
print("=" * 40)

# Testing addition and subtraction
h3 = h1 + h2
h6 = h5 - Height(4, 10)
h7 = h4 - h5
h8 = h1 + Height(0, 1)
h9 = Height(2, 10)
print(f"{h1} + {h2} = {h3}")
print(f"{h5} - {Height(4, 10)} = {h6}")
print(f"{h4} - {h5} = {h7}")
print(f"{h1} + {Height(0,1)} = {h8}")
print("=" * 40)

# Testing comparison operators
print(f"{h1} > {h2}: {h1>h2}")
print(f"{h1} < {h5}: {h1<h5}")
print(f"{h1} >= {h5}: {h1>=h5}")
print(f"{h2} <= {h1}: {h2<=h1}")
print(f"{h3} == {h3}: {h3==h3}")
print(f"{h1} == {h8}: {h1==h8}")
print(f"{h1} >= {h8}: {h1>=h8}")
print(f"{h1} == {h5}: {h1==h5}")
print(f"{h9} != {h2}: {h9!=h2}")
print("=" * 40)
