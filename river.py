import pygame, sys, udebs, random, math
from pygame.locals import *

#initialize pygame and udebs
pygame.init()
field = udebs.battleStart("river.xml")
field.controlMove('empty', 'empty', 'init')

#definitions
basicFont = pygame.font.SysFont(None, 48)
pygame.display.set_caption('A simple river simulation')
surface = pygame.display.set_mode((850, 520), 0, 32)

#colours

colours = {
    'black': (0, 0, 0),
    'grass': (0, 128, 0),
    'deep': (0, 0, 255),
    'shallow': (0, 255, 255),
    'dirt': (139, 69, 19),
    'sand': (218, 165, 32),
}

def createHex(center, length):
    found = []
    for i in range(6):
        angle = i * math.pi / 3
        x = center[0] + length*math.sin(angle)
        y = center[1] + length*math.cos(angle)
        found.append((x, y))
    return found

#game loop
while True:
  
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
                          
    #redraw the board
    surface.fill((0,0,0))
    i = 0    
    for y in range(len(field.map)):
        for x in range(len(field.map[0])):                      
            colour = colours[field.getStat((x,y), 'colour')]
            pygame.draw.polygon(surface, colour, createHex((x*35+30 + i,y*30 + 30), 20), 0)
            pygame.draw.polygon(surface, (0,0,0), createHex((x*35+30 + i,y*30 + 30), 20), 1)
        
        i += 18
    
    surface.blit(basicFont.render(str(field.time), True, (255,255,255), (0,0,0)), (750,50)) 
    
    pygame.display.update()
    field.controlTime(25)
    
