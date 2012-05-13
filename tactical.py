import pygame, sys, udebs
from pygame.locals import *

#initialize pygame and udebs
pygame.init()
udebs.battleStart("tactical.xml")
mainClock = pygame.time.Clock()

#define Color
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)

#initialize fonts
basicFont = pygame.font.SysFont(None, 48)

#Rects
#( left corner, top corner ), ( width, height )
tile = pygame.Rect(( 0, 0 ), ( 49, 49 ))

#initialize main surface
pygame.display.set_caption('Tactical RPG demo')
mainSurface = pygame.display.set_mode((400, 500), 0, 32)

#variables
selection = {'x': 0, 'y': 0}
phase = 'recruit'
highlighted = []
active_selection = False

def high_update(move):
    highlighted = []
    for x in range(8):
        for y in range(8):
            trgt = [x,y]
            if udebs.testMove('hero', trgt, move) == True:
                highlighted.append( [x,y] )
    return highlighted

#game loop
while True:
  
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        if event.type == KEYDOWN:
                                
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
            
            #selection change turn phase
            if event.key == K_ESCAPE:
                if phase == 'recruit':
                    phase = 'move'
                    highlighted = high_update('travel')      
                elif phase == 'move':
                    phase = 'attack'
                    highlighted = high_update('AOE')
                elif phase == 'attack':
                    phase = 'recruit'
                    highlighted = []
                    udebs.battleTick(1)
            
            #selection target    
            if event.key == K_RETURN:
                trgt = [ selection['x'], selection['y'] ]
                if phase == 'recruit':
                    udebs.controlMove('recruiter', trgt, 'recruit', 'cast')
                elif phase == 'move':
                    udebs.controlMove('hero', trgt, 'travel', 'cast')
                    highlighted = high_update('travel')
                elif phase == 'attack':
                    udebs.controlMove('hero', trgt, 'AOE', 'cast')
                    highlighted = high_update('AOE')
                udebs.battleTick(0)
                
            if event.key == K_DELETE:
                #exit selection mode, and revert. (go back a turn)
                highlighted = []
                phase = 'recruit'
                udebs.battleRevert(2)
                
            if event.key == K_r:
                #exit selection mode, and revert. (reset)
                highlighted = []
                phase = 'recruit'
                udebs.battleRevert(1)
                
                    
    #redraw the board  
    mainSurface.fill((0, 0, 0))
    for x in range(8):
        for y in range(8):
            tile.topleft = (50*x, 50*y)
            
            #The tile colours
            colour = WHITE
            
            #if square is highlighted
            if [x,y] in highlighted:
                colour = GREEN
            
            #if Curser is currently on the square.                       
            if selection == {'x': x, 'y': y}:
                colour = RED
            
            #draw the tile
            pygame.draw.rect(mainSurface, colour, tile)
            
            #draw any unit on the tile.
            unit = udebs.getMap((x, y))

            if unit != 'empty':
                sprite_colour = BLACK
                sprite_symbol = udebs.getStat(unit, 'sprite')
               
                mainSurface.blit(basicFont.render(sprite_symbol, True, sprite_colour, colour), (x*50+10, y*50+10))
    
    mainSurface.blit(basicFont.render(phase, True, WHITE, BLACK), (150, 430))
    pygame.display.update()  
    mainClock.tick(60)
