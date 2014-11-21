import math
import pygame
from pygame.locals import *
from udebs import loadxml

#definitions
pygame.init()
ts = 20
path = []
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
FONT = pygame.font.SysFont(None, 48)
CLOCK = pygame.time.Clock()
mainSurface = pygame.display.set_mode((500, 400), 0, 32)
pygame.display.set_caption('A simple hex GUI')
main_map = loadxml.battleStart("xml/hex.xml")
main_map.controlInit('init')

def createHex(a, b, ts):
    rad = math.cos(math.pi / 6)
    center = (ts*(2*a+b+1.5), ts*(1.5*b/rad+1.5))
    length = ts / rad
    
    found = []
    for i in range(6):
        angle = i * math.pi / 3
        x = center[0] + length*math.sin(angle)
        y = center[1] + length*math.cos(angle)
        found.append((x, y))
    return found

def eventUpdate():
    #redraw the board
    mainSurface.fill(BLACK) 
    for y in range(8):
        for x in range(8):                      
            loc = (x,y,'map')
            ACT = main_map.getStat('token', 'ACT')
            if loc in main_map.getFill('token', 'suptravel', ACT):
                colour = GREEN
            elif loc in main_map.getStat("token", "direction"):
                colour = RED
            else:
                colour = WHITE
            
            pygame.draw.polygon(mainSurface, colour, createHex(x, y, ts), 0)
            pygame.draw.polygon(mainSurface, BLACK, createHex(x, y, ts), 1)
            
            unit = main_map.getMap(loc)
            if unit != 'empty':
                sprite_symbol = main_map.getStat(unit, 'sprite')
                mainSurface.blit(FONT.render(sprite_symbol, True, BLACK, colour), (ts*(2*x+y+1), ts*(y*1.73+1)))
    
    pygame.display.update()

#game loop
eventUpdate()
while True:
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        
        elif event.type == MOUSEBUTTONDOWN:
            collide = pygame.Rect(0, 0, 1.5*ts, 1.5*ts)
            for x in range(8):
                for y in range(8):
                    collide.center = (ts*(2*x+y+1.5), ts*(1.5*y/math.cos(math.pi/6)+1.5))
                    if collide.collidepoint(pygame.mouse.get_pos()):
                        main_map.controlMove('token', (x,y), 'click')
                        eventUpdate()
            
    CLOCK.tick(60)
