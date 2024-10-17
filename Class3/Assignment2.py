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

    def __init__(self, name = "player 1", x = 0, y = 0, size = 1):
        pygame.sprite.Sprite.__init__(self)
        Item.__init__(self, name, x, y, size)
        self.color = COLORS[1]
        self.surf = pygame.Surface((1 * self.size, 1 * self.size))

    def setColor(self):
        newhex = choice(COLORS)
        self.color = newhex
        self.surf.fill(newhex) # filling surf with new color

    def setSize(self):
        newsize = randint(10, 100)
        self.size = newsize
        self.surf = pygame.Surface((1 * self.size, 1 * self.size))

    def update(self, pressed: dict):
        if pressed[pygame.K_LEFT]:
            self.goLeft()
        if pressed[pygame.K_RIGHT]:
            self.goRight()
        if pressed[pygame.K_UP]:
            self.goUp()
        if pressed[pygame.K_DOWN]:
            self.goDown()
        if pressed[pygame.K_SPACE]:
            self.setColor()
            self.setSize()
        p.surf.fill(p.color)

    def setRandomPosition(self):
        self.x, self.y = randint(0, WIDTH), randint(0, HEIGHT)

    def getPosition(self) -> tuple:
        return (self.x - self.size / 2, self.y - self.size / 2)

    def __str__(self) -> str:
        return super().__str__() + f"       color: {self.color}"

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
