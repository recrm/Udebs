#!/usr/bin/env python3
import pygame
import udebs
from pygame.locals import *

def redrawBoard(surface, ts):
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
    ts = 10
    field = udebs.battleStart("xml/life.xml")

    #Setup pygame
    pygame.init()
    pygame.display.set_caption("Conway's game of life.")
    surface = pygame.display.set_mode((ts*field.getMap().x, ts*field.getMap().y), 0, 32)
    mainClock = pygame.time.Clock()

#    #game loop
    for main_map in field.gameLoop(1):
        redrawBoard(surface, ts)
        mainClock.tick(60)

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                main_map.exit()

            elif event.type == MOUSEBUTTONDOWN:
                mouse = pygame.mouse.get_pos()
                for target in main_map.mapIter():
                    rect = pygame.Rect(target.loc[0]*ts, target.loc[1]*ts, ts, ts)
                    if rect.collidepoint(mouse):
                        print(target.loc, main_map.getStat(target, "LIFE"), main_map.getStat(target, "NBR"))

            elif event.type == KEYDOWN:
                if event.key == K_SPACE:
                    main_map.increment = 0 if main_map.increment == 1 else 1

                if event.key == K_DELETE:
                    main_map.next = udebs.battleStart("xml/life.xml")
                    main_map.next.increment = main_map.increment

                elif main_map.increment == 0:
                    # Step back one step
                    if event.key == K_LEFT:
                        test = main_map.getRevert(1)
                        if test:
                            main_map.next = test
                            main_map.next.increment = 0

                    # Step forward one step
                    if event.key == K_RIGHT:
                        main_map.controlTime(1)
