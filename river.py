import sys
import math
import pygame
from pygame.locals import *
import udebs

#initialize pygame and udebs
ts = 15
pygame.init()
pygame.display.set_caption('A simple river simulation')
mainClock = pygame.time.Clock()
mainSurface = pygame.display.set_mode((850, 520), 0, 32)
basicFont = pygame.font.SysFont(None, 20)

#Initialize Udebs
field = udebs.battleStart("xml/river.xml")
field.rand.seed(26892201)
field.controlInit('init')

BLACK = (0,0,0)
WHITE = (255,255,255)

colours = {
    'black': (0, 0, 0),
    'grass': (0, 128, 0),
    'deep': (0, 0, 255),
    'shallow': (0, 255, 255),
    'dirt': (139, 69, 19),
    'sand': (218, 165, 32),
}

#globals
loc = (0,0,'map')
pause = False

class hexagon:
    def __init__(self, a, b, ts):
        rad = math.cos(math.pi / 6)
        self.center = (ts*(2*a+b+1.5), ts*(1.5*b/rad+1.5))
        self.points = []

        length = ts / rad
        for i in range(6):
            angle = i * math.pi / 3
            x = self.center[0] + length*math.sin(angle)
            y = self.center[1] + length*math.cos(angle)
            self.points.append((x, y))

        self.square = pygame.Rect(0, 0, ts*1.5, ts*1.5)
        self.square.center = self.center

def drawSurface():
    #redraw the board
    mainSurface.fill(BLACK)
    for y in range(field.getMap().y):
        for x in range(field.getMap().x):
            hexa = hexagon(x, y, ts)
            colour = colours[field.getStat((x,y), 'colour')]
            pygame.draw.polygon(mainSurface, colour, hexa.points, 0)
            pygame.draw.polygon(mainSurface, BLACK, hexa.points, 1)

    i = 15
    for stat in field.stats.union(field.strings):
        value = field.getStat(loc, stat)
        mainSurface.blit(basicFont.render(stat+": "+str(value), True, WHITE, BLACK), (700,i))
        i += 15

    for other in [field.getName(loc), str(field.time)]:
        mainSurface.blit(basicFont.render(other, True, WHITE, BLACK), (700,i))
        i += 15

    pygame.display.update()


#game loop
drawSurface()
while True:
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()

        elif event.type == MOUSEBUTTONDOWN:
            mouse = pygame.mouse.get_pos()
            for y in range(field.getMap().y):
                for x in range(field.getMap().x):
                    if hexagon(x, y, ts).square.collidepoint(mouse):
                        loc = (x, y, "map")

        elif event.type == KEYDOWN:
            if event.key == K_SPACE:
                pause = not pause

    drawSurface()

    if not pause and field.time < 1000000:
        field.controlTime(50)
    mainClock.tick(60)
    if field.time >= 1000:
        sys.exit()
