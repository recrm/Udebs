import pygame
import sys
import traceback
import udebs
from pygame.locals import *

#Setup pygame
ts = 32
pygame.init()
pygame.display.set_caption('A simple chess GUI.')
surface = pygame.display.set_mode((ts*10, ts*10), 0, 32)
mainClock = pygame.time.Clock()

#Tiles
sheet = pygame.image.load("static/wood.png").convert_alpha()
tiles = ["white", "black", "T", "B", "R", "L", "TL", "TR", "BL", "BR"]
positions = [(0, 0),(0, 2),(3, 0),(3, 2),(4, 1),(2, 1),(2, 0),(4, 0),(2, 2),(4, 2)]
board = {}
for k, (x,y) in zip(tiles, positions):
    board[k] = sheet.subsurface(pygame.Rect(x*ts, y*ts, ts, ts))

#Sprites
sheet = pygame.image.load("static/chess_3.png").convert_alpha()
tiles = ["P", "R", "N", "B", "Q", "K"]
positions = [0,1,2,3,4,5]
sprites = {"B": {}, "W": {}}
for col, y in [("W", 0), ("B", 1)]:
    for rank, x in zip(tiles, positions):
        sprites[col][rank] = sheet.subsurface(pygame.Rect(x*ts, y*ts*2, ts, 2*ts))

@udebs.norecurse
def check(king, color, instance):
    """
    Check if space is under attack.

    king - Spot to check if under attack.
    color - Player that can't be under attack.
    """
    king = instance.getEntity(king)
    color = "black" if color == "white" else "white"

    #stupid case specific fix for castling because pawns move wierd.
    if king.name == "empty":
        y = -1 if color == "black" else 1
        for x in [-1, 1]:
            unit = instance.getName((king.loc[0]+x, king.loc[1]+y))
            if unit and "pawn" in unit:
                if color in instance.getStat(unit, "group"):
                    return False

    for unit in instance.getGroup(color):
        if "captured" not in instance.getStat(unit, "status"):
            for move in instance.getStat(unit, 'movelist'):
                if move not in {"pawn_travel", "pawn_double", "king_kcastle", "king_qcastle"}:
                    if instance.testMove(unit, king, move):
                        return False

    return True

module = {"check": {
    "f": "check",
    "args": ["$1", "$2", "self"],
}}
udebs.importModule(module, {"check": check})
main_map = udebs.battleStart("xml/chess.xml")
main_map.resetState()

#globals
BLACK = (0,0,0)
GREEN = (100,200,100, 127)
RED = (200, 0, 0, 127)
high = set()
activeUnit = False
moves = {}

def redrawBoard():
    surface.fill(BLACK)
    for x in range(10):
        for y in range(10):

            target = (x-1, y-1)
            unit = main_map.getName(target)
            tile = main_map.getStat((x, y, "board"), "sprite")

            #background
            if tile:
                bg = board[tile].copy()
                if target in high:
                    bg.fill(GREEN)
                elif unit and unit == activeUnit:
                    bg.fill(RED)

                surface.blit(bg, (x*ts, y*ts))

            #unit
            if unit not in {False, "empty"}:
                sprite = main_map.getStat(unit, "sprite")
                color = main_map.getStat(unit, "colour")
                fg = sprites[color][sprite]
                surface.blit(fg, (x*ts, (y-1)*ts))

    pygame.display.update()

def eventQuit():
    pygame.quit()
    sys.exit()

def eventClear():
    high.clear()
    moves.clear()
    global activeUnit
    activeUnit = False

#game loop
redrawBoard()
while True:
    for event in pygame.event.get():
        if event.type == QUIT:
            eventQuit()

        elif event.type == KEYDOWN and event.key == K_q:
            test = main_map.getRevert(1)
            if test:
                eventClear()
                main_map = test
                redrawBoard()

        elif event.type == MOUSEBUTTONDOWN:
            mouse = pygame.mouse.get_pos()
            for x in range(1,9):
                for y in range(1,9):
                    #Check if user has clicked on a square.
                    if pygame.Rect(ts*x, ts*y, ts, ts).collidepoint(mouse):
                        target = (x-1, y-1)
                        if activeUnit:
                            #Unit has been selected, so try and move token.
                            if target in moves:
                                main_map.castMove(activeUnit, target , moves[target])
                                main_map.controlTime(1)
                            eventClear()

                        else:
                            #Enter selection mode, find all spaces token can move to
                            movelist = main_map.getStat(target, 'movelist')
                            for x in range(8):
                                for y in range(8):
                                    other = (x,y)
                                    for move in movelist:
                                        if main_map.testMove(target, other, move):
                                            high.add(other)
                                            moves[other] = move
                                            break

                            if len(high) > 0:
                                activeUnit = main_map.getName(target)

                        redrawBoard()

    #Check if game is over.
    for king in main_map.getGroup("kings"):
        if "captured" in main_map.getStat(king, "status"):
            print("GAME OVER!!")
            eventQuit()

    mainClock.tick(60)
