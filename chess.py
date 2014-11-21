import pygame
import sys
import traceback
from udebs import loadxml
from udebs.interpret import importModule
from pygame.locals import *

#Setup pygame
ts = 32
pygame.init()
pygame.display.set_caption('A simple chess GUI.')

surface = pygame.display.set_mode((ts*10, ts*10), 0, 32)
mainClock = pygame.time.Clock()

#Import graphics
boards = pygame.image.load("texture/wood.png").convert_alpha()
token = pygame.image.load("texture/chess_3.png").convert_alpha()

tiles_types = {
    "white": (0, 0),
    "black": (0, 2),
    "T": (3, 0),
    "B": (3, 2),
    "R": (4, 1),
    "L": (2, 1),
    "TL": (2, 0),
    "TR": (4, 0),
    "BL": (2, 2),
    "BR": (4, 2),
}

tiles_token = {
    "P": 0,
    "R": 1,
    "N": 2,
    "B": 3,
    "Q": 4,
    "K": 5,
}

board = {}
sprites = {"B": {}, "W": {}}

for k, v in tiles_types.items():
    board[k] = boards.subsurface(pygame.Rect(v[0]*ts, v[1]*ts, ts, ts))

for col, y in [("W", 0), ("B", 1)]:
    for rank, x in tiles_token.items():
        sprites[col][rank] = token.subsurface(pygame.Rect(x*ts, y*ts*2, ts, 2*ts))

#Setup udebs.
def norecurse(f):
    """Returns True is a function calls itself."""
    def func(*args, **kwargs):
        if len([l[2] for l in traceback.extract_stack() if l[2] == f.__name__]) > 0:
            return True
        return f(*args, **kwargs)
    return func

@norecurse
def check(king, color, instance):
    king = instance.getTarget(king)
    color = "black" if color == "white" else "white"
    
    #stupid case specific fix because pawns move wierd.
    if king.name == "empty":
        y = -1 if color == "black" else 1
        for x in [-1, 1]:
            unit = instance.getMap((king.loc[0]+x, king.loc[1]+y))
            if unit and "pawn" in unit:
                if color in instance.getStat(unit, "group"):
                    return False
    
    for unit in instance.getGroup(color):
        for move in instance.getStat(unit, 'movelist'):
            if move not in {"pawn_travel", "pawn_double", "king_kcastle", "king_qcastle"}:
                if instance.testMove(unit, king, move):
                    return False
    return True

module = {
    "check": {
        "f": "check",
        "args": ["$1", "$2", "self"],
    },
}
importModule(module, {
    "check": check, 
})
main_map = loadxml.battleStart("xml/chess.xml")
main_map.controlInit('init')

#globals
high = set()
activeUnit = False
moves = {}

def redrawBoard():
    surface.fill((0,0,0))  
    for x in range(10):
        for y in range(10):
            
            unit = main_map.getMap((x-1, y-1, "map"))
            tile = main_map.getStat((x, y, "board"), "sprite")
            
            #background
            if tile:
                bg = board[tile].copy()
                if (x-1, y-1) in high:
                    bg.fill((100,200,100, 127))
                elif unit and unit == activeUnit:
                    bg.fill((200, 0, 0, 127))
                surface.blit(bg, (x*ts, y*ts))
            
            #unit
            if unit not in {False, "empty"}:
                sprite = main_map.getStat(unit, "sprite")
                color = main_map.getStat(unit, "colour")
                fg = sprites[color][sprite]
                surface.blit(fg, (x*ts, (y-1)*ts))
          
    pygame.display.flip()

#game loop
while True:
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit() 
        
        elif event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                high.clear()
                moves.clear()
                activeUnit = False
                
            elif event.key == K_q:
                test = main_map.getRevert(2)
                if test:
                    high.clear()
                    moves.clear()
                    activeUnit = False
                    main_map = test
                          
        elif event.type == MOUSEBUTTONDOWN:
            mouse = pygame.mouse.get_pos()
            for x in range(10):
                for y in range(10):
                    if x in {0, 9} or y in {0, 9}:
                        continue
                    current = pygame.Rect(ts*x, ts*y, ts, ts)
                    #Check if user has clicked on a square.
                    if current.collidepoint(mouse):
                        target = (x-1, y-1)
                        if activeUnit:
                            #Unit has been selected, so try and move token.
                            main_map.castMove(activeUnit, target , moves[target])
                            main_map.controlTime(1)
                            high.clear()
                            moves.clear()
                            activeUnit = False
                            
                        else:
                            #Enter selection mode, find all spaces token can move to
                            for x in range(8):
                                for y in range(8):
                                    other = (x,y)
                                    for move in main_map.getStat(target, 'movelist'):
                                        if main_map.testMove(target, other, move):
                                            high.add(other)
                                            moves[other] = move
                                            
                            if len(high) > 0:
                                activeUnit = main_map.getMap(target)
            
    redrawBoard()
    
    #Check if game is over.
    king_list = main_map.getGroup("kings")
    for king in king_list:
        if "captured" in main_map.getStat(king, "status"):
            print("GAME OVER!!")
            pygame.quit()
            sys.exit()       

    mainClock.tick(60)
