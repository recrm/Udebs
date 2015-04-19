#!/usr/bin/env python3
import sys
import re
import random
import pygame 
from pygame.locals import *
import udebs

"""
To do.

Fix early win.
Fix messages.
"""

#initialize pygame
pygame.mixer.pre_init(44100, -16, 2, 2048)
pygame.init()
mainClock = pygame.time.Clock()

#display
mainSurface = pygame.display.set_mode((400, 500), 0, 32)
pygame.display.set_caption('Tactical RPG demo')

#fonts
basicFont = pygame.font.SysFont(None, 48)
smallFont = pygame.font.SysFont(None, 24)

#music
sound_overworld = pygame.mixer.Sound('static/overworld.ogg')
sound_overworld.set_volume(0.75)
sound_fight = pygame.mixer.Sound('static/fight.ogg')
sound_fight.set_volume(0.75)
sound_boss = pygame.mixer.Sound('static/boss.ogg')
sound_boss.set_volume(1)
sound_overworld.play(-1)

#sfx
sound_fx = {}
for effect in ["attack.wav", "fire.wav", "magic.wav", "pickup.wav", "uberheal.wav", "back.wav", "charge.wav", "heal.wav", "menu.wav", "select.wav", "water.wav", "boom.wav", "hurt.wav", "step.wav"]:
    sound_fx[effect.split(".")[0]] = pygame.mixer.Sound("static/" + effect)

#colour
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
GREY = (125,125,125)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

#Areas of screen
headerRect = pygame.Rect(0, 0, 400, 50)
topRect = pygame.Rect(0, 50, 400, 50)
middleRect = pygame.Rect(0, 100, 400, 300)
bottomRect = pygame.Rect(0, 400, 400, 100)

#Drawing functions
def drawText(text, font, x, y ,color, background):
    words = font.render(text, True, color, background)
    rect = words.get_rect(center=(x,y))
    mainSurface.blit(words, rect)
    return

def ListBox(array, coord, rec, collide=False, mouse=False, high=False, font=smallFont, font_color=BLACK, background=WHITE):
    if collide and not rec.collidepoint(mouse):
        return False
    xvalue = rec.width / (2*coord[0])
    yvalue = rec.height / (2*coord[1])
    tile = pygame.Rect(0, 0, 2*xvalue, 2*yvalue)
    x = 1
    y = 1
    for item in array:
        if x > coord[0]:
            y +=1
            x = 1
        xpos = rec.left + (2*x-1)*xvalue
        ypos = rec.top + (2*y-1)*yvalue
        if collide:
            tile.center = (xpos, ypos)
            if tile.collidepoint(mouse):
                return item
        elif item:
            temp_background = GREEN if item == high else background
            drawText(item, font, xpos, ypos, font_color, temp_background)
        x +=1
        
    return "empty"

#Update the main screens.
def updateOverWorld():
    #Updates the overworld viewer.
    mainSurface.fill(BLACK)
    for x in range(8):
        for y in range(8):
            if main_map.getDistance("hero", (x, y), "pinf") <= 1:
                color = GREEN
            else:
                color = WHITE
            pygame.draw.rect(mainSurface, color, pygame.Rect((50*x, 50*y), (49, 49)))
            unit = main_map.getMap((x, y))
            if unit != 'empty':
                sprite_symbol = main_map.getStat(unit, 'sprite')
                mainSurface.blit(basicFont.render(sprite_symbol, True, BLACK, color), (x*50+10, y*50+10))

    drawText("Level " + str(battle.getStat("recruiter", "LVL")), basicFont, 200,450, GREEN, BLACK)
    main_map.controlLog("Overworld Updated")
    pygame.display.update()
    
def updateRPG(char=False, moveHigh=False, unitHigh=False):
    #draw menu
    mainSurface.fill(WHITE)
    pygame.draw.rect(mainSurface, GREY, middleRect)
    pygame.draw.rect(mainSurface, BLACK, bottomRect)
    #Name and movelist of active unit
    if char:
        drawText(battle.getStat(char, "DESC"), basicFont, 200, 20, BLACK, WHITE)
        movelist = battle.getStat(char, "movelist")
        ListBox(movelist, (3, 2), topRect, high=moveHigh)
    
    #Draw battlefield
    for x in range(3):
        for y in range(3):
            unit = battle.getMap((x, y))
            if unit != "empty" and "ko" not in battle.getStat(unit, "status"):
                size = 50 if unit == "boss" else 10
                fun = battle.getStat
                color = [int(fun(unit, "r")), int(fun(unit,"g")), int(fun(unit,"b"))]
                if (x,y) == unitHigh:
                    pygame.draw.rect(mainSurface, GREEN, pygame.Rect(90 + x*200, 140 + y*100, size + 20, size + 20))
                pygame.draw.rect(mainSurface, color, pygame.Rect(100 + x*200, 150 + y*100, size, size))

    #Stats
    def lstats():
        for label in (False, "HP", "MP"):
            yield label
        units = ("fighter", "bmage", "wmage")
        for unit in units:
            yield unit
            yield str(battle.getStat(unit, "HP"))
            yield str(battle.getStat(unit, "MP"))
            
    ListBox(lstats(), (3,4), bottomRect, background=BLACK, font_color=GREEN)
    pygame.display.update()

#Other custom callables.
def message(*args, font=basicFont, color=BLACK):
    #Displays a message in the overworld.
    pygame.draw.rect(mainSurface, BLACK, bottomRect)
    text = " ".join(args)
    color_text = GREEN
    drawText(text, font, 200,450, color_text, color)
    pygame.display.update()
    while True:
        event = pygame.event.wait()
        if event.type == KEYDOWN or event.type == MOUSEBUTTONDOWN:
            break

def battleFinish():
    battle.controlInit("finish")

def playSound(sound, times):
    sound_fx[sound].play(times)
    main_map.controlLog("played sound effect", sound)

def eventQuit():
    pygame.quit()
    sys.exit()

def getItem():
    battle.controlMove('party', 'treasure', 'get_item')
    for log in battle.getLog():
        if "added to party inventory" in log:
            return re.split("\W+", log)[0]

def subBattle(monster="monster"):
    sound_overworld.fadeout(1000)
    if monster == "boss":
        fight_music = sound_boss
        battle.controlInit("recruitBoss")
    else:
        fight_music = sound_fight
        battle.controlInit("init")
    updateRPG()
    message("Battle Start")
    fight_music.play(-1)
    while len(battle.getGroup("monster")) > 0:
        battle.controlTime(1)
    fight_music.fadeout(1000)
    message("You WIN!!")
    sound_overworld.play(-1)
        
def setChar(new):
    char = new
    updateRPG(new)
    move = False
    target = "empty"
    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                eventQuit()
            
            elif event.type == MOUSEBUTTONDOWN:
                mouse = pygame.mouse.get_pos()
                if topRect.collidepoint(mouse):
                    movelist = battle.getStat(char, "movelist")
                    test = ListBox(movelist, (3,2), topRect, True, mouse)
                    if test != "empty" and test:
                        move = False if move == test else test
                        
                elif middleRect.collidepoint(mouse):
                    x = 1 if mouse[0] > 200 else 0
                    if mouse[1] < 200:
                        y = 0
                    elif mouse[1] < 300:
                        y = 1
                    else:
                        y = 2
                    
                    target = "empty" if target == (x,y) else (x,y)
                            
                updateRPG(char, moveHigh=move, unitHigh=target)
            
            if move and (battle.getStat(move, "skip") or target != "empty"):
                battle.castMove(char, target, move)
                updateRPG()
                return
                
        mainClock.tick(60)

local = {
    "message": {
        "f": "message",
        "all": True,
#        "kwargs": {"color": "-$1"},
#        "default": {"-$1": "WHITE"},
    },
    "soundFX": {
        "f": "playSound",
        "args": ["$1", "$2"],
        "default": {"$2": 0},
    },
    "update": {
        "f": "updateOverWorld",
    },
    "updateRPG": {
        "f": "updateRPG",
        "args": ["$1"],
    },
    "battle_finish": {
        "f": "battleFinish",
    },
    "exit": {
        "f": "eventQuit",
    },
    "getitem": {
        "f": "getItem",
    },
    "battle": {
        "f": "subBattle",
        "args": ["$1"],
    },
    "activate": {
        "f": "setChar",
        "args": ["$1"],
    }
}
glob = {
    "message": message, 
    "playSound": playSound, 
    "updateOverWorld": updateOverWorld,
    "eventQuit": eventQuit,
    "getItem": getItem,
    "subBattle": subBattle,
    "updateRPG": updateRPG,
    "setChar": setChar,
    "battleFinish": battleFinish,
}
udebs.importModule(local, glob)
main_map = udebs.battleStart("xml/zanar2.xml")
battle = udebs.battleStart("xml/rpg.xml")

main_map.controlInit("init")
def main():
    #game loop
    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                eventQuit()
            
            elif event.type == MOUSEBUTTONDOWN:
                mouse = pygame.mouse.get_pos()
                for x in range(8):
                    for y in range(8):
                        if pygame.Rect(49*x, 49*y, 49, 49).collidepoint(mouse):
                            main_map.castMove("hero", (x, y), "hero_travel")
                            main_map.controlTime(1)
                        
            elif event.type == KEYDOWN and event.key == K_q:
                sound_fx['select'].play()
                menuScreen()
                updateOverWorld()
        
        mainClock.tick(60)
        
#Code for equip menu, most of this is done outside Udebs.
def menuScreen():
    #Define order equipment is displayed
    def lEquip(all=True):
        for item in [False, "Weapon", "Hat"]:
            yield item if all else False
        for unit in ['fighter', 'bmage', 'wmage']:
            yield unit
            yield battle.getListGroup(unit, "equip", 'weapon') if all else unit
            yield battle.getListGroup(unit, "equip", 'hat') if all else unit
                
    #Define order stats are displayed
    def lStats():
        stats = ("HP", "MP", "MEL", "MGK")
        for stat in stats:
            yield stat
        for stat in stats:
            value = str(battle.getStat(char, stat))
            if stat in ("HP", "MP"):
                value += "/" + str(battle.getStat(char, "MAX" + stat))
            yield value
    
    char = "fighter"
    
    def updateMenu():
        mainSurface.fill(WHITE)

        #Section bars
        for i in (100, 400):
            pygame.draw.line(mainSurface, BLACK, (0, i), (400, i))
        for i in (175, 250, 325):
            pygame.draw.line(mainSurface, BLACK, (20,i), (380,i))
        for i in (133, 266):
            pygame.draw.line(mainSurface, BLACK, (i, 120), (i, 380))
        
        #Header
        drawText(battle.getStat(char, "DESC"), basicFont, 200, 25, BLACK, WHITE)
        
        #Stats
        ListBox(lStats(), (4, 2), topRect)
        #equipment
        ListBox(lEquip(), (3, 4), middleRect, high=char)
        #inventory
        inventory = battle.getStat("party", "inventory")
        ListBox(inventory, (4, 3), bottomRect)
        
        pygame.display.update()    
    
    updateMenu()
    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                eventQuit()
            
            elif event.type == KEYDOWN:
                return
            
            elif event.type == MOUSEBUTTONDOWN:
                mouse = pygame.mouse.get_pos()
                if middleRect.collidepoint(mouse):
                    test = ListBox(lEquip(all=False), (3,4), middleRect, True, mouse)
                    if test:
                        char = test
                    
                elif bottomRect.collidepoint(mouse):
                    inventory = battle.getStat("party", "inventory")
                    item = ListBox(inventory, (4,3), bottomRect, True, mouse)
                    if item == "empty":
                        battle.controlMove(char, battle.getStat(char, "equip"), "unequip")
                    else:
                        battle.castMove("empty", char, item)
                            
                updateMenu()
        
        mainClock.tick(60)

if __name__ == "__main__":
    main()
