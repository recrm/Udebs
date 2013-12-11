import pygame, sys, udebs, random, math
from pygame.locals import *

#initialize pygame and udebs
pygame.init()
mainClock = pygame.time.Clock()
main_map = udebs.battleStart("hex.xml")
main_map.controlMove('empty', 'empty', 'init')

#definitions
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
basicFont = pygame.font.SysFont(None, 48)
pygame.display.set_caption('A simple hex GUI')
mainSurface = pygame.display.set_mode((425, 300), 0, 32)

def createHex(center, length):
    found = []
    for i in range(6):
        angle = i * math.pi / 3
        x = center[0] + length*math.sin(angle)
        y = center[1] + length*math.cos(angle)
        found.append((x, y))
    return found

#variables
selection = {'x': 0, 'y': 0}
highlighted = main_map.getFill('token1', 'suptravel', main_map.getStat('token', 'ACT'))

#game loop
while True:
  
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        
        if event.type == KEYDOWN:
        
            if event.key == K_RETURN:
                main_map.controlMove('token1', (selection['x'], selection['y']), 'travel')
                highlighted = main_map.getFill('token1', 'suptravel', main_map.getStat('token', 'ACT'))
 
        
        #selection right/left
            if event.key == K_RIGHT:
                selection['x'] +=1
                if selection['x'] >= 8:
                    selection['x'] = 7
                    
            if event.key == K_LEFT:
                selection['x'] -=1
                if selection['x'] < 0:
                    selection['x'] = 0
                    
            #selection up/down
            if event.key == K_UP:
                selection['y'] -=1
                if selection['y'] < 0:
                    selection['y'] = 0
                    
            if event.key == K_DOWN:
                selection['y'] +=1
                if selection['y'] >= 8:
                    selection['y'] = 7
                  
    #redraw the board
    mainSurface.fill(BLACK)
    i = 0    
    for y in range(8):
        for x in range(8):                      
            
            colour = WHITE
            if (x,y) in highlighted:
                colour = GREEN
            if selection == {'x': x, 'y': y}:
                colour = RED
            
            pygame.draw.polygon(mainSurface, colour, createHex((x*35+30 + i,y*30 + 30), 20), 0)
            pygame.draw.polygon(mainSurface, BLACK, createHex((x*35+30 + i,y*30 + 30), 20), 1)
            
            unit = main_map.getMap((x, y))
            if unit != 'empty':
                sprite_symbol = main_map.getStat(unit, 'sprite')
                mainSurface.blit(basicFont.render(sprite_symbol, True, BLACK, colour), (x*35+18+i, y*30+16))
        i += 18
    
    pygame.display.update()
    mainClock.tick(60)
