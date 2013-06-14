from __future__ import division
import pygame
import sys
import udebs
import random
from pygame.locals import *

#initialize pygame and udebs
pygame.mixer.pre_init(44100, -16, 2, 2048)
pygame.init()
main_map = udebs.battleStart(u"zanar2.xml")
main_map.controlScript(u'init')
main_map.controlTime(0)
mainClock = pygame.time.Clock()

#display
mainSurface = pygame.display.set_mode((400, 500), 0, 32)
pygame.display.set_caption(u'Tactical RPG demo')
pygame.mouse.set_visible(False)

#fonts
basicFont = pygame.font.SysFont(None, 48)
smallFont = pygame.font.SysFont(None, 24)

##music
#overworld = pygame.mixer.Sound(u'overworld.ogg')
#overworld.play(-1)
#pygame.mixer.music.play(-1)


#colour
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
GREY = (125,125,125)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

def arrow_update(event, selection):
    if event.key == K_RIGHT:
        selection[u'x'] +=1
        if selection[u'x'] > selection[u'xmax']:
            selection[u'x'] = selection[u'xmax']
    elif event.key == K_LEFT:
        selection[u'x'] -=1
        if selection[u'x'] < 0:
            selection[u'x'] = 0
    elif event.key == K_UP:
        selection[u'y'] -=1
        if selection[u'y'] < 0:
            selection[u'y'] = 0
    elif event.key == K_DOWN:
        selection[u'y'] +=1
        if selection[u'y'] > selection[u'ymax']:
            selection[u'y'] = selection[u'ymax']
    return selection

def drawText(text, font, x, y ,color, background):
    words = font.render(text, True, color, background)
    rect = words.get_rect(center=(x,y))
    mainSurface.blit(words, rect)
    return

def main():
    
    def message(text, font=basicFont):
        pygame.draw.rect(mainSurface, BLACK, pygame.Rect(( 0, 400 ), ( 400, 100 )))
        drawText(text, font, 200,450, GREEN, BLACK)
        pygame.display.update()
        while True:
            event = pygame.event.wait()
            if event.type == KEYDOWN and event.key == K_RETURN:
                break
        return
    
    def high_update(move, env):
        highlighted = []
        for x in xrange(8):
            for y in xrange(8):
                target = [x,y]
                targetenv = env.createTarget(u'hero', target, move) 
                if env.testRequire(targetenv) == True:
                    highlighted.append([x,y])
        return highlighted        
    
    #definitions    
    tile = pygame.Rect(( 0, 0 ), ( 49, 49 ))
    selection = {u'x': 0, u'y': 0, u"xmax": 7, u"ymax": 7}
    inport = udebs.battleStart(u"rpg.xml", init=False)
    active_selection = False
    battle = []
    win = False
    boss = False
    
    #initial highlight
    highlighted = []
    highlighted = high_update(u'travel', main_map)
    
    
    #game loop
    while True:
        
        for entry in inport.getLog():
            if u"inventory" in entry:
                message(entry, smallFont)
        
        for mob in battle[:]:
            message(u"BATTLE ENGAGED!!!")
            inport.controlScript(u'init')
            
            inport = subBattle(inport)
            main_map.controlMove(u"hero", mob, u"KO")
            inport.controlMove(u'treasure', u'party', u'get_item')
            for entry in inport.getLog():
                if u"inventory" in entry:
                    message(entry, smallFont)
            highlighted = high_update(u'travel', main_map)
            battle.remove(mob)
            
        if win:
            message(u"Level Complete!!!")
            main_map.controlScript(u'finish')
            inport.controlScript(u'finish')
            main_map.controlScript(u'init')
            main_map.controlTime(0)
            highlighted = high_update(u'travel', main_map)
            win = False
            selection[u'x'] = 0
            selection[u'y'] = 0
            battle = []
        
        if boss:
            message(u"Engaging Boss Monster")
            inport.controlScript(u'boss')
            inport = subBattle(inport)
            main_map.controlMove(u"hero", boss, u"KO")
            
            #you win game is over.
            message(u"You Win! Game Over!")
            sys.exit()
        
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == KEYDOWN:
                arrow_update(event, selection)                              
                
                #selection target
                if event.key == K_RETURN:
                    trgt = [selection[u'x'], selection[u'y']]
                    main_map.controlMove(u'hero', trgt, u'travel')
                    #move enemies
                    for unit in main_map.getActiveUnits():
                        loc = main_map.getLocation(unit)
                        if loc:
                            loc[0] = loc[0] + random.randint(-1, 1)
                            loc[1] = loc[1] + random.randint(-1, 1)
                            main_map.controlMove(unit, loc, u'travel')
                        if main_map.getDistance(u'hero', unit, u'pinf') <= 1:
                            battle.append(unit)
                    #check proximity
                    if main_map.getDistance(u'hero', u'treasure', u'pinf') <= 1:
                        inport.controlMove(u'treasure', u'party', u'get_item')
                        main_map.controlMove(u'hero', u"treasure", u"KO")
                    if main_map.getDistance(u'hero', u'goal', u'pinf') <= 1:
                        win = True
                    if main_map.getDistance(u'hero', u'boss', u'pinf') <= 1:
                        boss = True
                    main_map.controlTime(0)
                    main_map.controlTime(1)
                    highlighted = high_update(u'travel', main_map)              
                 
                if event.key == K_q:
                    inport = menuScreen(inport)
                    
#                if event.key == K_DELETE:
#                    #exit selection mode, and revert. (go back a turn)
#                    highlighted = []
#                    main_map.controlRevert(2)
#                    
#                if event.key == K_r:
#                    #exit selection mode, and revert. (reset)
#                    highlighted = []
#                    main_map.controlRevert(1)
                                        
        #redraw the Unit board 
        mainSurface.fill((0, 0, 0))
        for x in xrange(8):
            for y in xrange(8):
                tile.topleft = (50*x, 50*y)
                colour = WHITE
                if [x,y] in highlighted:
                    colour = GREEN                
                if x == selection[u'x'] and y == selection[u'y']:
                    colour = RED
                pygame.draw.rect(mainSurface, colour, tile)
                unit = main_map.getMap((x, y))
                if unit != u'empty':
                    sprite_colour = BLACK
                    sprite_symbol = main_map.getStat(unit, u'sprite')
                    mainSurface.blit(basicFont.render(sprite_symbol, True, sprite_colour, colour), (x*50+10, y*50+10))
        
        drawText(u"Level " + unicode(inport.getStat(u"recruiter", u"LVL")), basicFont, 200,450, GREEN, BLACK)
        pygame.display.update()  
        mainClock.tick(60)

def menuScreen(inport):    
    #definitions
    mode = u"equip"
    selectBoxMenu = pygame.Rect( 125, 0, 100, 25 )
    selection = {u'x': 0, u'y': 0, u"xmax": 1, u"ymax": 2}
    selectItem = {u'x': 0, u'y': 0, u"xmax": 3, u"ymax": 1}
    
    #game loop
    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            
            #key inputs for menu
            if event.type == KEYDOWN:    
                if mode == u"equip":
                    arrow_update(event, selection)
                elif mode == u"inventory":
                    arrow_update(event, selectItem)
                        
                if event.key == K_q:
                    inport.getLog()
                    return inport
                       
                if event.key == K_ESCAPE:
                    if mode == u"inventory":
                        mode = u"equip"
                        
                if event.key == K_RETURN:
                    if mode == u"equip":
                        mode = u"inventory"
                    elif mode == u"inventory":
                        #collect data
                        oldItem_unit = [u"fighter", u"wmage", u"bmage"][selection[u'y']]
                        oldItem_type = [u"weapon", u"hat"][selection[u'x']]
                        oldItem = inport.getListGroup(oldItem_unit, u"equip", oldItem_type)

                        try:
                            transferItem = inport.getStat(u"party", u"inventory")[selectItem[u'x'] + 4*selectItem[u'y']]
                        except IndexError:
                            transferItem = False
                        transferChar = [u"fighter", u"wmage", u"bmage"][selection[u'y']]
                        
                        #one use items.
                        if transferItem in [u'potion', u'mana']:
                            inport.controlMove(transferChar, transferChar, transferItem)
                            inport.controlTime(0)
                        #change equipment
                        else:
                            #unequip old item
                            if oldItem:
                                inport.controlList(inport.getGroupType(transferChar, u"TEMPLATE"), u"equip", oldItem, u"remove")
                                inport.controlList(u"party", u"inventory", oldItem)
                            
                            #requip new item
                            if transferItem:
                                if transferChar == u"fighter":
                                    weapon = u"sword"
                                else:
                                    weapon = u"staff"
                                if inport.controlList(inport.getGroupType(transferChar, u"TEMPLATE"), u'equip', transferItem):
                                    inport.controlList(u"party", u"inventory", transferItem, u"remove")
                        
                        #cleanup
                        mode = u"equip"
                        del oldItem, transferItem, transferChar
        
        #clear and reprint static                        
        mainSurface.fill((255, 255, 255))
        char = [u"fighter", u"wmage", u"bmage"][selection[u'y']]
        chargroup = inport.getGroupType(char, u"TEMPLATE")
        strhp = unicode(inport.getStat(char, u"HP")) + u"/" + unicode(inport.getStat(chargroup, u"HP"))
        strmp = unicode(inport.getStat(char, u"MP")) + u"/" + unicode(inport.getStat(chargroup, u"MP"))
        
        pygame.draw.line(mainSurface, BLACK, (0,100), (400,100))
        pygame.draw.line(mainSurface, BLACK, (0,400), (400,400))
        pygame.draw.line(mainSurface, BLACK, (20,175), (380,175))
        pygame.draw.line(mainSurface, BLACK, (20,250), (380,250))
        pygame.draw.line(mainSurface, BLACK, (20,325), (380,325))
        pygame.draw.line(mainSurface, BLACK, (133,120), (133,380))
        pygame.draw.line(mainSurface, BLACK, (266,120), (266,380))
        drawText(inport.getStat(char, u"DESC"), basicFont, 200, 25, BLACK, WHITE)
        drawText(u"HP", smallFont, 50, 60, BLACK, WHITE)
        drawText(u"MP", smallFont, 150, 60, BLACK, WHITE)
        drawText(u"Mellee", smallFont, 250, 60, BLACK, WHITE)
        drawText(u"Magic", smallFont, 350, 60, BLACK, WHITE)
        drawText(strhp, smallFont, 50, 85, BLACK, WHITE)
        drawText(strmp, smallFont, 150, 85, BLACK, WHITE)
        drawText(unicode(inport.getStat(char, u"MEL")), smallFont, 250, 85, BLACK, WHITE)
        drawText(unicode(inport.getStat(char, u"MGK")), smallFont, 350, 85, BLACK, WHITE)
        drawText(u"weapon", smallFont, 199, 137, BLACK, WHITE)
        drawText(u"hat", smallFont, 332, 137, BLACK, WHITE)

        #print green indicator
        if mode == u"equip":        
            selectBoxMenu.centerx = 133*selection[u'x'] + 199
            selectBoxMenu.centery = 75*selection[u'y'] + 212
        elif mode == u"inventory":
            selectBoxMenu.centerx = 100*selectItem[u'x'] + 50
            selectBoxMenu.centery = 50*selectItem[u'y'] + 425      
        pygame.draw.rect(mainSurface, (0,255,0), selectBoxMenu)
        
        #print equipment
        i = 0
        for unit in [u'fighter', u'wmage', u'bmage']:
            j = i*75 + 212
            if i == selection[u'y']:
                row = True
            else:
                row = False
            drawText(unit, smallFont, 66, j, BLACK, WHITE)
            weapon = inport.getListGroup(unit, u"equip", u'weapon')
            hat = inport.getListGroup(unit, u"equip", u"hat")
            if weapon:
                if row and selection[u'x'] == 0:
                    colour = GREEN
                else:
                    colour = WHITE
                drawText(weapon, smallFont, 199, j, BLACK, colour)
            if hat:
                if row and selection[u'x'] == 1:
                    colour = GREEN
                else:
                    colour = WHITE
                drawText(hat, smallFont, 332, j, BLACK, colour)
            i +=1
        
        #draw inventory
        inventory = inport.getStat(u"party", u"inventory")
        for index in xrange(len(inventory)):
            if index < 4:
                y = 425
            else:
                y = 475
            if selectItem[u'x'] + 4*selectItem[u'y'] == index and mode == u"inventory":
                colour = GREEN
            else:
                colour = WHITE
            drawText(inventory[index], smallFont, (index % 4)*100+50, y, BLACK, colour)
            
        #increment time
        pygame.display.update()
        mainClock.tick(60)

def subBattle(battle_map):
    
    monster1 = battle_map.getMap((1,0))
    monster2 = battle_map.getMap((1,1))
    monster3 = battle_map.getMap((1,2))
    
    #initialize selection boxes
    selectBoxMenu = pygame.Rect( 125, 0, 150, 20 )
    selectBoxTarget = pygame.Rect(0, 0, 20, 20)
    fun = battle_map.getStat  
    
    #initialize state variables
    mode = u"wait"
    menu = {u'x': 0, u'y': 0, u"xmax": 1, u"ymax": 2}
    target = {u'x': 0, u'y': 0, u"xmax": 1, u"ymax": 2}
    doOnce = False
    activeUnits = []
    unitIndex = 0
    
    fun = battle_map.getStat
    color = {
        u'fighter': [int(fun(u'fighter', u"r")), int(fun(u'fighter',u"g")), int(fun(u'fighter',u"b"))],
        u"wmage": [int(fun(u'wmage', u"r")), int(fun(u'wmage',u"g")), int(fun(u'wmage',u"b"))],
        u'bmage': [int(fun(u'bmage', u"r")), int(fun(u'bmage',u"g")), int(fun(u'bmage',u"b"))],
        monster1: [int(fun(monster1, u"r")), int(fun(monster1,u"g")), int(fun(monster1,u"b"))],
        monster2: [int(fun(monster2, u"r")), int(fun(monster2,u"g")), int(fun(monster2,u"b"))],
        monster3: [int(fun(monster3, u"r")), int(fun(monster3,u"g")), int(fun(monster3,u"b"))],
    }
    
    for mob in [monster1, monster2, monster3]:
        if mob == u'empty':
            color[mob] = GREY
   
   #game loop
    while True:
        #checks for active units.
        if unitIndex >= len(activeUnits):
            activeUnits = battle_map.getActiveUnits()
            if len(activeUnits) > 0:
                mode = u"active"
            else:
                mode = u"wait"
            unitIndex = 0
        
        if mode == u"active":
            #if unit is a monster
            if activeUnits[unitIndex] in [monster1, monster2, monster3]:
                #select move to cast
                caster = activeUnits[unitIndex]
                moveList = battle_map.getStat(caster, u'movelist')    
                moveList_possible = []
                for entry in moveList:
                    test = battle_map.createTarget(caster, u'empty', entry)
                    if battle_map.testRequire(test):
                        moveList_possible.append(entry)
                if len(moveList_possible) == 0:
                    print activeUnits[unitIndex], u"can't attack"  
                else:
                    mindex = random.randint(0, len(moveList_possible)-1)
                    move = moveList_possible[mindex]
                    targets = []
                    if move in [u'heal', u'barrier']:
                        targets = [monster1, monster2, monster3]
                    else:
                        targets = [u'fighter', u'wmage', u'bmage']
                    targets_possible = []
                    for unit in targets:
                        user_status = battle_map.getStat(unit, u"status")
                        if u"KO" not in user_status: 
                            if u'SACRIFICE' not in user_status:
                                targets_possible.append(unit)            
                
                    etarget = targets[random.randint(0, len(targets)-1)]
                    if u'DEFEND' in battle_map.getStat(u'fighter', u'status'):
                        if u'fighter' in targets_possible:
                            etarget = u'fighter'
                        
                    battle_map.controlMove(caster, etarget, move)
                    battle_map.controlTime(0)
                           
                unitIndex +=1
            #else unit is a player
            else:
                mode = u"player-menu"
        
        #check for keyboard input
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            
            #key inputs for menu
            if event.type == KEYDOWN:
                if mode == u"player-menu" and doOnce == False:
                    arrow_update(event, menu)
                    
                    #skip player
                    if event.key == K_ESCAPE:
                        caster = activeUnits[unitIndex]
                        ltarget = u"empty"
                        battle_map.controlMove( caster, ltarget, u'pass' )
                        battle_map.controlTime(0)
                        #reset
                        mode = u"active"
                        target[u'x'] = 0
                        target[u'y'] = 0
                        menu[u'y'] = 0
                        unitIndex +=1
                        doOnce = True

                    #make selection
                    elif event.key == K_RETURN:
                        try:
                            move = battle_map.getStat(activeUnits[unitIndex], u'movelist')[menu[u'y'] +3*menu[u'x']]
                            if battle_map.getStat(move, u'skip'):
                                caster = activeUnits[unitIndex]
                                battle_map.controlMove( caster, u'empty', move )
                                battle_map.controlTime(0)
                                mode = u"active"
                                move = False
                                target[u'x'] = 0
                                target[u'y'] = 0
                                menu[u'y'] = 0
                                menu[u'x'] = 0
                                unitIndex +=1
                            else:
                                mode = u"player-target"
                            doOnce = True
                                
                        except IndexError:
                            pass
                                           
                if mode == u"player-target" and doOnce == False:
                    arrow_update(event, target)
                    
                    if event.key == K_ESCAPE:
                        mode = u"player-menu"
                    
                    #activate move
                    if event.key == K_RETURN:
                        #cast
                        caster = activeUnits[unitIndex]
                        ltarget = (target[u'x'], target[u'y'])
                        battle_map.controlMove( caster, ltarget, move )
                        battle_map.controlTime(0)
                        #reset
                        mode = u"active"
                        move = False
                        target[u'x'] = 0
                        target[u'y'] = 0
                        menu[u'y'] = 0
                        menu[u'x'] = 0
                        unitIndex +=1
                        doOnce = True

        #draw menu
        mainSurface.fill((255, 255, 255))
        pygame.draw.rect(mainSurface, GREY, pygame.Rect((0, 100), (400, 300)))
        
        if mode == u"player-target":
            drawText(battle_map.getStat(move, u"DESC"), smallFont, 200, 60, (0,0,0), (255,255,255))
        
        #This section needs a cleanup
        if mode == u"player-menu":
            drawText(battle_map.getStat(activeUnits[unitIndex], u"DESC"), smallFont, 200, 20, (0,0,0), (255,255,255))
            
            spacing = 40
            _i = 0
            x = 125
            for attack in battle_map.getStat(activeUnits[unitIndex], u'movelist'):
                if _i >= 3:
                    _i = 0
                    spacing = 40
                    x +=175
                
                colour = WHITE
                if menu[u'y'] == _i:
                    if menu[u'x']*175 + 125 == x:
                        selectBoxMenu.centery = spacing
                        selectBoxMenu.centerx = x
                        pygame.draw.rect(mainSurface, GREEN, selectBoxMenu)
                        colour = GREEN
                drawText(battle_map.getStat(attack, u"DESC") , smallFont, x, spacing, BLACK, colour)
                spacing +=20
                _i +=1
        
        
        #draw target selection box
        if mode == u"player-target":
            selectBoxTarget.centerx = 290*target[u'x'] + 55
            selectBoxTarget.centery = 100*target[u'y'] + 155
            pygame.draw.rect(mainSurface, (0,255,0), selectBoxTarget)
        
        #update colour
        for unit in color.keys():
            if unit != u'empty':
                color[unit] = [int(fun(unit, u"r")), int(fun(unit,u"g")), int(fun(unit,u"b"))]
        
        if u"KO" not in battle_map.getStat(u"fighter", u"status"):
            pygame.draw.rect(mainSurface, color[u'fighter'], pygame.Rect((50, 250), (10, 10))) 
        wmage_status = battle_map.getStat(u"wmage", u"status")
        if u"KO" not in wmage_status and u'SACRIFICE' not in wmage_status:
            pygame.draw.rect(mainSurface, color[u'wmage'], pygame.Rect(( 50, 350 ), ( 10, 10 )))
        if u"KO" not in battle_map.getStat(u"bmage", u"status"):
            pygame.draw.rect(mainSurface, color[u'bmage'], pygame.Rect(( 50, 150 ), ( 10, 10 )))
        
        if u"KO" not in battle_map.getStat(monster1, u"status"):
            pygame.draw.rect(mainSurface, color[monster1], pygame.Rect(( 340, 150 ), ( 10, 10 )))
        if u"KO" not in battle_map.getStat(monster2, u"status"):
            if monster2 ==u'boss':
                x = 50
            else:
                x = 10
            pygame.draw.rect(mainSurface, color[monster2], pygame.Rect(( 345 - x/2, 250 ), ( x, x )))
        if u"KO" not in battle_map.getStat(monster3, u"status"):
            pygame.draw.rect(mainSurface, color[monster3], pygame.Rect(( 340, 350 ), ( 10, 10 )))
        
        #draw bmage stats
        drawText(u"Black Mage", smallFont, 50, 425, BLACK, WHITE)
        drawText(unicode(battle_map.getStat(u"bmage", u"HP")), smallFont, 50, 445, RED, WHITE)
        drawText(unicode(battle_map.getStat(u"bmage", u"MP")), smallFont, 50, 465, BLUE, WHITE)
        
        #draw fighter stats
        drawText(u"Fighter", smallFont, 200, 425, BLACK, WHITE)
        drawText(unicode(battle_map.getStat(u"fighter", u"HP")), smallFont, 200, 445, RED, WHITE)
        drawText(unicode(battle_map.getStat(u"fighter", u"MP")), smallFont, 200, 465, BLUE, WHITE)
        
        #draw wmage stats
        drawText(u"White Mage", smallFont, 350, 425, BLACK, WHITE)
        drawText(unicode(battle_map.getStat(u"wmage", u"HP")), smallFont, 350, 445, RED, WHITE)
        drawText(unicode(battle_map.getStat(u"wmage", u"MP")), smallFont, 350, 465, BLUE, WHITE)
        
        #draw messages
        for entry in battle_map.getLog():
            for skip in [u"failed", u"empty", u"delay", u"KO", u"uses POISON", u"OVERHEAL", u"DEFEND_ACTIVE"]:
                if skip in entry:
                    break
            else:
                for add in [u"uses", u"HP", u"added"]:
                    if add in entry:
                        pygame.draw.rect(mainSurface, WHITE, pygame.Rect((0,0), (400,100)))
                        drawText(entry, smallFont, 200,50, [0,0,0], [255,255,255])
                        pygame.display.update()
                        while True:
                            event = pygame.event.wait()
                            if event.type == KEYDOWN and event.key == K_RETURN:
                                pygame.draw.rect(mainSurface, WHITE, pygame.Rect((0,0), (400,100)))
                                break
                   
        #draw win
        if u"KO" in battle_map.getStat(monster1, u"status") or monster1 == u"empty":
            if u"KO" in battle_map.getStat(monster2, u"status") or monster2 == u"empty":
                if u"KO" in battle_map.getStat(monster3, u"status") or monster3 == u"empty":
                    drawText(u"VICTORY!!!", basicFont, 200,250, [0,255,0], [125,125,125])
                    pygame.display.update()
                    while True:
                        event = pygame.event.wait()
                        if event.type == KEYDOWN and event.key == K_RETURN:
                            return battle_map
        #draw lose
        #draw win
        if u"KO" in battle_map.getStat(u'fighter', u"status"):
            if u"KO" in battle_map.getStat(u'wmage', u"status"):
                if u"KO" in battle_map.getStat(u'bmage', u"status"):
                    drawText(u"DEFEAT", basicFont, 200,250, [0,255,0], [125,125,125])
                    pygame.display.update()
                    while True:
                        event = pygame.event.wait()
                        if event.type == KEYDOWN and event.key == K_RETURN:
                            pygame.quit()
                            sys.exit()
                    
        #increment time
        doOnce = False
        pygame.display.update()
        if mode == u"wait":
            battle_map.controlTime()
        mainClock.tick(60)
        
if __name__ == u"__main__":
    main()
