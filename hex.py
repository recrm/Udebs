import pygame
import sys
from udebs import loadxml
import math
from pygame.locals import *
pygame.init()

#definitions
ts = 20
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
FONT = pygame.font.SysFont(None, 48)
CLOCK = pygame.time.Clock()

def eventLoad():
    S = {}
    pygame.display.set_caption('A simple hex GUI')
    S["surface"] = pygame.display.set_mode((500, 400), 0, 32)
    S["map"] = loadxml.battleStart("xml/hex.xml")
    S["map"].controlInit('init')
    S["mouse"] = None
    S['path'] = []
    S["high"] = updateHigh(S)
    return S

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

def updateHigh(S):
    ACT = S["map"].getStat('token', 'ACT')
    return S["map"].getFill('token1', 'suptravel', ACT)

def eventUpdate(S):
    #redraw the board
    S["surface"].fill(BLACK) 
    for y in range(8):
        for x in range(8):                      
            #check for click updates
            if S["mouse"]:
                eventClick(S, x, y)
            
            loc = (x,y,'map')
            if loc in S["high"]:
                colour = GREEN
            elif loc in S['path']:
                colour = RED
            else:
                colour = WHITE
            
            pygame.draw.polygon(S["surface"], colour, createHex(x, y, ts), 0)
            pygame.draw.polygon(S["surface"], BLACK, createHex(x, y, ts), 1)
            
            unit = S["map"].getMap(loc)
            if unit != 'empty':
                sprite_symbol = S["map"].getStat(unit, 'sprite')
                S["surface"].blit(FONT.render(sprite_symbol, 
                    True, BLACK, colour), (ts*(2*x+y+1), ts*(y*1.73+1)))
    
    pygame.display.update()

def eventExit():
    pygame.quit()
    sys.exit()

def eventClick(S, x, y):
    collide = pygame.Rect(0, 0, 1.5*ts, 1.5*ts)
    collide.center = (ts*(2*x+y+1.5), ts*(1.5*y/math.cos(math.pi/6)+1.5))
    
    if collide.collidepoint(S["mouse"]):
        S["mouse"] = None
        loc = (x, y, "map")
        if loc in S['high']:
            S["map"].controlMove('token1', loc, 'travel')
            S['high'] = updateHigh(S)
            S["path"] = []
        else:
            S["path"] = S['map'].pathTowards('token1', loc, 'notempty')
            if not S["path"]:
                S["path"] = []
            
#game loop
S = eventLoad()
while True:
    for event in pygame.event.get():
        if event.type == QUIT:
            eventExit()
        
        elif event.type == MOUSEBUTTONDOWN:
            S["mouse"] = pygame.mouse.get_pos()
        
    eventUpdate(S)
    CLOCK.tick(60)
