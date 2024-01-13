import pygame
import sys
import math

pygame.init()
WIDTH, HEIGHT = 400, 400
DOTWIDTH, DOTHEIGHT = 2, 2
LINEWIDTH = 3

print("INPUT")
print("DELETE")
print("EXIT")
print("===================")

FUNCTION_LIST = [
<<<<<<< HEAD
    [lambda x: x**.5, "red"],
=======
    [lambda x: eval("1/x"), "red"],
>>>>>>> 2260b3e5305baa34a4a8a753ae4db6eaab819284
]

ALL_ENTERED = False
while not ALL_ENTERED:
    match input("Enter a command: "):
        case "EXIT":
            sys.exit()
        case "INPUT":
             input("EXPRESSION")


SCALELINEWIDTH = 2
XBASE, YBASE = 5, 5
XSCALE, YSCALE = XBASE * 3, YBASE * 3
NUMXLINES, NUMYLINES = int(WIDTH / XSCALE), int(HEIGHT / YBASE)

DEFINITION = 1000
GRAPHRANGE = 25

font = pygame.font.Font('freesansbold.ttf', 10)

CENTERX, CENTERY = WIDTH/2-int(LINEWIDTH/2), HEIGHT/2-int(LINEWIDTH/2)
screen = pygame.display.set_mode((WIDTH, HEIGHT))
running = True

while running:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill("white")
    NUMBERS = []

    def CreateGraphLines():
        # Draw vertical line
        pygame.draw.line(screen, "black", (WIDTH/2-int(LINEWIDTH/2), 0), (WIDTH/2-int(LINEWIDTH/2), HEIGHT), LINEWIDTH)
        # Draw horizontal line
        pygame.draw.line(screen, "black", (0, HEIGHT/2-int(LINEWIDTH)), (WIDTH, HEIGHT/2-int(LINEWIDTH)), LINEWIDTH)

        # Draw X scale lines and create number positions
        for x in range(-NUMXLINES+1, NUMXLINES):
            text = font.render(str(x), True, "black", "white")
            textRect = text.get_rect()
            textRect.center = (CENTERX+(x*XSCALE)-SCALELINEWIDTH/2, CENTERY+9)
            NUMBERS.append([text, textRect])
            pygame.draw.line(screen, "black", (CENTERX+(x*XSCALE)-SCALELINEWIDTH/2, CENTERY+3), (CENTERX+(x*XSCALE)-SCALELINEWIDTH/2, CENTERY-6), SCALELINEWIDTH)
        # Draw Y scale lines
        for y in range(-NUMYLINES+1, NUMYLINES):
            text = font.render(str(y), True, "black", "white")
            textRect = text.get_rect()
            textRect.center = (CENTERX+9, CENTERY+(y*YSCALE)-SCALELINEWIDTH/2)
            NUMBERS.append([text, textRect])
            pygame.draw.line(screen, "black", (CENTERX+6, CENTERY+(y*YSCALE)-SCALELINEWIDTH/2), (CENTERX-6, CENTERY+(y*YSCALE)-SCALELINEWIDTH/2), SCALELINEWIDTH)
    CreateGraphLines()

    def PlotNewPoint(POINTX,POINTY, COLOR = "red"):
        
        newRect = pygame.Rect(CENTERX-POINTX-DOTWIDTH/2, CENTERY-POINTY-DOTHEIGHT/2, DOTWIDTH, DOTHEIGHT)
        pygame.draw.rect(screen, COLOR, newRect)

    def PlotNewFunction(INPUT_FUNCTION, COLOR):
        for x in range(-GRAPHRANGE+1, GRAPHRANGE):
            y = INPUT_FUNCTION(x)
            if y == "err": continue
            for x2 in range(0+(x*DEFINITION), DEFINITION+(x*DEFINITION)):
                y2 = INPUT_FUNCTION(x2/DEFINITION)
                if y2 == "err": continue
                PlotNewPoint((-x2/DEFINITION)*XSCALE, y2*YSCALE, COLOR)

        PlotNewPoint(-x*XSCALE, y*YSCALE, COLOR)

    for FUNCTION_TEST in FUNCTION_LIST:
            FUNCTION = lambda x: FUNCTION_TEST[0](x) if type(FUNCTION_TEST[0](x)) != complex else "err"
            PlotNewFunction(FUNCTION, FUNCTION_TEST[1])

    for TEXT in NUMBERS:
        screen.blit(TEXT[0], TEXT[1])
    pygame.display.flip()