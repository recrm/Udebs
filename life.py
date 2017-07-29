import pygame
import udebs
from pygame.locals import *

def createMap():
    main_map = udebs.battleStart("xml/life.xml")
    main_map.controlInit('init')
    main_map.resetState()
    return main_map

def redrawBoard(surface):
    surface.fill((0,0,0))
    for target in main_map.mapIter():
        if main_map.getStat(target, "LIFE"):
            rect = pygame.Rect(target.loc[0]*(ts), target.loc[1]*(ts), ts, ts)
            pygame.draw.rect(surface, (100,200,100, 127), rect)
            
    pygame.display.update()

def dedup(lst):
    return list(set(lst))

if __name__ == "__main__":
    # Setup Udebs
    module = {"dedup": {
        "f": "dedup",
        "args": ["$1"],
    }}
    udebs.importModule(module, {"dedup": dedup})

     # State variables
    run = True
    main_map = createMap()
    ts = 10
    
    #Setup pygame
    pygame.init()
    pygame.display.set_caption("Conway's game of life.")
    surface = pygame.display.set_mode((ts*main_map.getMap().x, ts*main_map.getMap().y), 0, 32)
    mainClock = pygame.time.Clock()

    #game loop
    for i in range(50):
#    while True:
        redrawBoard(surface)    
        
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                exit()
                
            elif event.type == MOUSEBUTTONDOWN:
                mouse = pygame.mouse.get_pos()
                for target in main_map.mapIter():
                    rect = pygame.Rect(target.loc[0]*ts, target.loc[1]*ts, ts, ts) 
                    if rect.collidepoint(mouse):
                        print(target.loc, main_map.getStat(target, "LIFE"), main_map.getStat(target, "NBR"))
                        
            elif event.type == KEYDOWN:
                if event.key == K_SPACE:
                    run = not run
                    
                if event.key == K_DELETE:
                    main_map = createMap()
                    
                elif not run:
                    # Step back one step
                    if event.key == K_LEFT:
                        test = main_map.getRevert(1)
                        if test:
                            main_map = test
                    
                    # Step forward one step
                    elif event.key == K_RIGHT:
                        main_map.controlTime(1)
                        
        if run:
            main_map.controlTime(1)
        
        mainClock.tick(60)
