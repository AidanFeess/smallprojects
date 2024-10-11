#####################################################################
# author: Aidan Feess
# date: 09/06/2024
# description:
#####################################################################
import pygame
from random import randint, choice
from Item import *
from Constants import *
class Person(pygame.sprite.Sprite, Item):
    pass
########################### main game################################
# DO NOT CHANGE ANYTHING BELOW THIS LINE
#####################################################################
# Initialize pygame library and display
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
# Create a person object
p = Person()
RUNNING = True # A variable to determine whether to get out of the
# infinite game loop
while (RUNNING):
    # Look through all the events that happened in the last frame to see
    # if the user tried to exit.
    for event in pygame.event.get():
        if (event.type == KEYDOWN and event.key == K_ESCAPE):
            RUNNING = False
        elif (event.type == QUIT):
            RUNNING = False
        elif (event.type == KEYDOWN and event.key == K_SPACE):
            print(p)
    # Otherwise, collect the list/dictionary of all the keys that were
    # pressed
    pressedKeys = pygame.key.get_pressed()
    # and then send that dictionary to the Person object for them to
    # update themselves accordingly.
    p.update(pressedKeys)
    # fill the screen with a color
    screen.fill(WHITE)
    # then transfer the person to the screen
    screen.blit(p.surf, p.getPosition())
    pygame.display.flip()
