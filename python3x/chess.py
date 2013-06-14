import pygame, sys, udebs, random
from pygame.locals import *

#initialize pygame and udebs
pygame.init()
main_map = udebs.battleStart("chess.xml")
main_map.controlScript('init')
mainClock = pygame.time.Clock()

#definitions
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
basicFont = pygame.font.SysFont(None, 48)
pygame.display.set_caption('A simple chess GUI')
mainSurface = pygame.display.set_mode((400, 400), 0, 32)
#( left corner, top corner ), ( width, height )
tile = pygame.Rect(( 0, 0 ), ( 50, 50 ))

#variables
selection = {'x': 0, 'y': 0}
active_unit = False
highlighted = []
active_selection = False

#game loop
while True:
  
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        if event.type == KEYDOWN:
            
            if event.key == K_DELETE:
                #exit selection mode, and revert.
                active_unit = False
                highlighted = []
                active_selection = False
                main_map.battleRevert(2)
            
            if event.key == K_ESCAPE:
                #exit selection mode.
                active_unit = False
                highlighted = []
                active_selection = False
                
            if event.key == K_RETURN:
                if active_unit != False:
                    
                    #activates move.
                    trgt = [ selection['x'], selection['y'] ]
                    test = False
                    for move in main_map.getStat(active_unit, 'movelist'):
                        test = main_map.controlMove(active_unit, trgt, move)
                        if test == True:
                            break
                    main_map.controlTime(0)
                    
                    #leave selection mode
                    active_unit = False
                    highlighted = []
                    active_selection = False
                    
                    #pass turn.
                    if test == True:
                        main_map.controlTime(1)
                else:
                    if main_map.getMap((selection['x'], selection['y'])) != 'empty':
                        
                        #enter selection mode
                        active_selection = ( selection['x'], selection['y'] )
                        active_unit = main_map.getMap( active_selection )
                        
                        #update selection board.
                        active_unit = main_map.getMap( ( selection['x'], selection['y'] ) )
                        for x in range(8):
                            for y in range(8):
                                trgt = [x,y]
                                for move in main_map.getStat(active_unit, 'movelist'):
                                    env = main_map.createTarget(active_unit, trgt, move)
                                    if main_map.testRequire(env) == True:
                                        highlighted.append( [x,y] )
                                
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
        i = 0    
        for x in range(8):
            for y in range(8):
                tile.topleft = (50*x, 50*y)
                
                #The base board
                if i % 2 == 1:
                    colour = WHITE
                else:
                    colour = BLACK
                
                #if square is highlighted
                if active_unit != False:
                    if [x,y] in highlighted or active_selection == [x,y]:
                        colour = GREEN
                
                #if Curser is currently on the square.                       
                if selection == {'x': x, 'y': y}:
                    colour = RED
                
                #draw the tile
                pygame.draw.rect(mainSurface, colour, tile)
                
                #draw any unit on the tile.
                unit = main_map.getMap((x, y))
                if unit != 'empty':
                    #print(unit)
                    colour_list = main_map.getStat(unit, 'colour')
                    sprite_colour = tuple([int(number) for number in colour_list])
                    sprite_symbol = main_map.getStat(unit, 'sprite')[0]
                   
                    mainSurface.blit(basicFont.render(sprite_symbol, True, sprite_colour, colour), (x*50+10, y*50+10))
                del colour
                del unit
                i +=1
            i +=1
        del i 
    
    pygame.display.update()
        
    mainClock.tick(60)

