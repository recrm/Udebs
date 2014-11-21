import sys
import math
from pygame.locals import *
import pygame
from udebs import loadxml
from udebs.interpret import importModule

#initialize pygame and udebs
ts = 15
pygame.init()
pygame.display.set_caption('A simple river simulation')
mainClock = pygame.time.Clock()
mainSurface = pygame.display.set_mode((850, 520), 0, 32)
basicFont = pygame.font.SysFont(None, 20)
pause = False

field = loadxml.battleStart("xml/river.xml")
field.rand.seed(26892201)
field.controlInit('init')
loc = (0,0,'map')

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

def drawSurface():
    #redraw the board
    mainSurface.fill((0,0,0))
    for y in range(field.getMap().y()):
        for x in range(field.getMap().x()):                      
            colour = colours[field.getStat((x,y), 'colour')]
            pygame.draw.polygon(mainSurface, colour, createHex(x, y, ts), 0)
            pygame.draw.polygon(mainSurface, (0,0,0), createHex(x, y, ts), 1)
    
    i = 15
    for stat in field.stats.union(field.strings):
        value = field.getStat((x,y), stat)
        mainSurface.blit(basicFont.render(stat+": "+str(value), True, (255,255,255), (0,0,0)), (700,i))
        i += 15
        
    for other in [field.getName(loc), str(field.time)]:
        mainSurface.blit(basicFont.render(other, True, (255,255,255), (0,0,0)), (700,i))
        i += 15
    
    pygame.display.update()


#game loop
while True:
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
            
        elif event.type == MOUSEBUTTONDOWN:
            collide = pygame.Rect(0, 0, 1.5*ts, 1.5*ts)
            for y in range(field.getMap().y()):
                for x in range(field.getMap().x()):   
                    collide.center = (ts*(2*x+y+1.5), ts*(1.5*y/math.cos(math.pi/6)+1.5))
                    if collide.collidepoint(pygame.mouse.get_pos()):
                        loc = (x, y, "map")
            
        elif event.type == KEYDOWN:
            if event.key == K_SPACE:
                pause = not pause
                
    drawSurface()
    
    if not pause and field.time < 10000:
        field.controlTime(50)
    mainClock.tick(60)
    if field.time >= 10000:
        sys.exit()
    
