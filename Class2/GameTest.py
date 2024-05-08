#####################################################################
# author:       anky
# date:         7th Feb, 2023
# description:  A file to test out the classes designed in the CardGame
# program.
#####################################################################

TESTING = False     # Change this to False if you want to proceed to the
                    # game itself. Leave it as True if you want to test
                    # the Card and Deck classes.

########## DO NOT CHANGE ANYTHING BELOW THIS LINE ##########

# import the CardGame file and all its classes.
from CardGame import *
import random


if (TESTING):

    # Testing: the CARD class
    c1 = Card(2, "hearts")
    c2 = Card(4, "diamonds")

    print(f"{c1} > {c2}: {c1>c2}")
    print(f"{c1} < {c2}: {c1<c2}")
    print(f"{c1} == {c2}: {c1==c2}")
    print("-" * 40)

    c3 = Card(21, "uno")
    c4 = Card(-6, "queens")

    print(f"{c3} > {c4}: {c3>c4}")
    print(f"{c3} < {c4}: {c3<c4}")
    print(f"{c3} == {c4}: {c3==c4}")
    print("-" * 40)

    c5 = Card(1, "Diamonds")

    print(f"{c5} > {c2}: {c5>c2}")
    print(f"{c5} < {c2}: {c5<c2}")
    print(f"{c5} == {c2}: {c5==c2}")
    print("-" * 40)



    # Testing: The Deck Class
    random.seed(1234)

    d1 = Deck()
    print(d1)
    print("-" * 40)

    d1.shuffle()
    d1.shuffle()
    print(d1)
    print("-" * 40)

    c6 = d1.draw()
    c7 = d1.draw()
    print(f"{c6} > {c7}: {c6>c7}")
    print(f"{c6} < {c7}: {c6<c7}")
    print(f"{c6} == {c7}: {c6==c7}")
    print("-" * 40)

    for i in range(32):
        c8 = d1.draw()

    print(f"c8 = {c8}")
    print(f"d1 = {d1}")

    c8 = d1.draw()
    c8 = d1.draw()
    print(f"c8 = {c8}")
    print(f"d1 = {d1}")

    c8 = d1.draw()
    c8 = d1.draw()
    print(f"c8 = {c8}")
    print(f"d1 = {d1}")
    print("-" * 40)

# Testing: The Game Class
else:
    g1 = Game()
    g1.start()
