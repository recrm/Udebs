import math
import pygame
import sys
from pygame.locals import *
import udebs

#definitions
ts = 20
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)

#Setup pygame
pygame.init()
mainFont = pygame.font.SysFont(None, 48)
mainClock = pygame.time.Clock()
mainSurface = pygame.display.set_mode((500, 400), 0, 32)
pygame.display.set_caption('A simple hex GUI')

#Setup udebs
main_map = udebs.battleStart("xml/hex.xml")
main_map.controlInit('init')

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

def eventUpdate():
    #redraw the board
    mainSurface.fill(BLACK) 
    ACT = main_map.getStat('token', 'ACT')
    highlight = main_map.getFill('token', 'suptravel', ACT)
    direction = main_map.getStat("token", "direction")
    for y in range(8):
        for x in range(8):                      
            loc = (x,y,'map')
            if loc in highlight:
                colour = GREEN
            elif loc in direction:
                colour = RED
            else:
                colour = WHITE
            
            hexa = hexagon(x, y, ts)
            pygame.draw.polygon(mainSurface, colour, hexa.points, 0)
            pygame.draw.polygon(mainSurface, BLACK, hexa.points, 1)
            
            unit = main_map.getMap(loc)
            if unit != 'empty':
                sprite_symbol = main_map.getStat(unit, 'sprite')
                mainSurface.blit(mainFont.render(sprite_symbol, True, BLACK, colour), hexa.square)
    
    pygame.display.update()

#game loop
eventUpdate()
while True:
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        
        elif event.type == MOUSEBUTTONDOWN:
            mouse = pygame.mouse.get_pos()
            for x in range(8):
                for y in range(8):
                    if hexagon(x, y, ts).square.collidepoint(mouse):
                        main_map.controlMove('token', (x,y), 'click')
                        eventUpdate()
            
    mainClock.tick(60)
