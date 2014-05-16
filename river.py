import pygame
import sys
import math
from udebs import loadxml
from udebs.interpret import importModule
from pygame.locals import *

def createSet(value = None, old = None):
    if not old:
        old = set()
    if value:
        old.add(value)
    return old

module = {"SET": {
    "f": "createSet",
    "args": ["$1", "$2"],
    "default": {"$1": None, "$2": None},
}}
importModule(module, {"createSet": createSet})


#initialize pygame and udebs
pygame.init()
pygame.display.set_caption('A simple river simulation')
mainClock = pygame.time.Clock()
field = loadxml.battleStart("xml/river.xml")
field.rand.seed(26892201)
field.controlInit('init')

#definitions
S = {
    "ts": 15,
    "pause": False,
    "surface": pygame.display.set_mode((850, 520), 0, 32),
    "mouse": None,
    "loc": (0,0,'map'),
}    

basicFont = pygame.font.SysFont(None, 20)
colours = {
    'black': (0, 0, 0),
    'grass': (0, 128, 0),
    'deep': (0, 0, 255),
    'shallow': (0, 255, 255),
    'dirt': (139, 69, 19),
    'sand': (218, 165, 32),
}

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

def eventClick(S, x, y):
    ts = S['ts']
    collide = pygame.Rect(0, 0, 1.5*ts, 1.5*ts)
    collide.center = (ts*(2*x+y+1.5), ts*(1.5*y/math.cos(math.pi/6)+1.5))
    
    if collide.collidepoint(S["mouse"]):
        S["loc"] = (x, y, "map")
        S["mouse"] = False

def drawSurface(S, field):
    #redraw the board
    S["surface"].fill((0,0,0))
    for y in range(field.getMap().y()):
        for x in range(field.getMap().x()):                      
            if S["mouse"]:
                eventClick(S, x, y)
            
            colour = colours[field.getStat((x,y), 'colour')]
            pygame.draw.polygon(S["surface"], colour, createHex(x, y, S["ts"]), 0)
            pygame.draw.polygon(S["surface"], (0,0,0), createHex(x, y, S["ts"]), 1)
    
    i = 15
    for stat in field.stats.union(field.strings):
        value = field.getStat(S['loc'], stat)
        S["surface"].blit(basicFont.render(stat+": "+str(value), True, (255,255,255), (0,0,0)), (700,i))
        i += 15
    
    value = str(field.getStat(S['loc'], "W") + field.getStat(S['loc'], "D"))
    S["surface"].blit(basicFont.render(value, True, (255,255,255), (0,0,0)), (700,i)) 
    i += 15
    S["surface"].blit(basicFont.render(field.getName(S['loc']), True, (255,255,255), (0,0,0)), (700,i)) 
    i += 15
    S["surface"].blit(basicFont.render(str(field.time), True, (255,255,255), (0,0,0)), (700,i)) 


#game loop
while True:
  
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
            
        elif event.type == MOUSEBUTTONDOWN:
            S['mouse'] = pygame.mouse.get_pos()
            
        elif event.type == KEYDOWN:
            if event.key == K_SPACE:
                S['pause'] = not S['pause']
                
                
    drawSurface(S, field)
    pygame.display.update()
    if not S['pause'] and field.time < 100000:
        field.controlTime(100)
    mainClock.tick(60)
#    sys.exit()
    
