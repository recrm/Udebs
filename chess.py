import pygame
import sys
import traceback
from udebs import loadxml
from udebs.interpret import importModule
from pygame.locals import *

ts = 32

#custom engine function
def norecurse(f):
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
            unit = instance.getMap((king.x+x, king.y+y))
            if unit and "pawn" in unit:
                if color in instance.getStat(unit, "group"):
                    return False
    
    for unit in instance.getGroup(color):
        for move in instance.getStat(unit, 'movelist'):
            if move not in {"pawn_travel", "pawn_double", "king_kcastle", "king_qcastle"}:
                if instance.testMove(unit, king, move):
                    return False
    return True

def eventLoad():   
    pygame.init()
    pygame.display.set_caption('A simple chess GUI.')
    
    S = {
        "high": set(),
        "active_unit": False,
        "moves": {},
        "mouse": False,
        "surface": pygame.display.set_mode((ts*10, ts*10), 0, 32),
        "mainClock": pygame.time.Clock(),
        "main_map": loadxml.battleStart("xml/chess.xml"),
        "board": {},
        "sprites": {"B": {}, "W": {}},
    }
    
    board = pygame.image.load("texture/wood.png").convert_alpha()
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
    
    for k, v in tiles_types.items():
        S["board"][k] = board.subsurface(pygame.Rect(v[0]*ts, v[1]*ts, ts, ts))
    
    for col, y in [("W", 0), ("B", 1)]:
        for rank, x in tiles_token.items():
            S["sprites"][col][rank] = token.subsurface(pygame.Rect(x*ts, y*ts*2, ts, 2*ts))
    
    S["main_map"].controlInit('init')
    return S
    
def redrawBoard(S):
    S["surface"].fill((0,0,0))  
    for x in range(10):
        for y in range(10):
            #check for click updates
            if S["mouse"]:
                eventClick(S, x, y)
                    
            unit = S["main_map"].getMap((x-1, y-1, "map"))
            
            #background
            tile = S["main_map"].getStat((x, y, "board"), "sprite")
            if tile:
                bg = S["board"][tile].copy()
                if (x-1, y-1) in S["high"]:
                    bg.fill((100,200,100, 127))
                elif unit and unit == S["active_unit"]:
                    bg.fill((200, 0, 0, 127))
                S["surface"].blit(bg, (x*ts, y*ts))
            
            #unit
            if unit not in {False, "empty"}:
                sprite = S["main_map"].getStat(unit, "sprite")
                color = S["main_map"].getStat(unit, "colour")
                fg = S["sprites"][color][sprite]
                S["surface"].blit(fg, (x*ts, (y-1)*ts))
          
    pygame.display.flip()

def eventClick(S, x, y):
    if x in {0, 9} or y in {0, 9}:
        return
    current = pygame.Rect(ts*x, ts*y, ts, ts)
    if current.collidepoint(S["mouse"]):
        if S["active_unit"]:
            eventMove(S, (x-1, y-1))
        else:
            eventHigh(S, (x-1, y-1))
        S["mouse"] = False
    
def eventHigh(S, loc):
    if -1 in loc or 8 in loc:
        return
    for x in range(8):
        for y in range(8):
            target = (x,y)
            for move in S["main_map"].getStat(loc, 'movelist'):
                if S["main_map"].testMove(loc, target, move):
                    S["high"].add(target)
                    S["moves"][target] = move
                    
    if len(S["high"]) > 0:
        S["active_unit"] = S["main_map"].getMap(loc)
    
def eventMove(S, target):
    if target in S["high"]:
        caster = S["active_unit"]
        move = S["moves"][target]
        S["main_map"].castMove(caster, target, move)
        S["main_map"].controlTime(1)
    
    #leave selection mode
    eventEscape(S)
    
def eventEscape(S):
    S["high"].clear()
    S["moves"].clear()
    S["active_unit"] = False

def eventQuite():
    pygame.quit()
    sys.exit()   
    
def eventRevert(S):
    test = S["main_map"].getRevert(2)
    if test:
        eventEscape(S)
        S["main_map"] = test

module = {"check": {
    "f": "check",
    "args": ["$1", "$2", "self"],
}}
importModule(module, {"check": check})
S = eventLoad()
    
#game loop
while True:
    for event in pygame.event.get():
        if event.type == QUIT:
            eventQuite()
        
        elif event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                eventEscape(S)
                
            elif event.key == K_q:
                eventRevert(S)
                          
        elif event.type == MOUSEBUTTONDOWN:
            S["mouse"] = pygame.mouse.get_pos()
            
    redrawBoard(S)
    
    king_list = S["main_map"].getGroup("kings")
    for king in king_list:
        if "captured" in S["main_map"].getStat(king, "status"):
            print("GAME OVER!!")
            eventQuite()        

    S["mainClock"].tick(60)
