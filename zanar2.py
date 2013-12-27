import pygame, sys, udebs, random
from pygame.locals import *

#initialize pygame and udebs
pygame.mixer.pre_init(44100, -16, 2, 2048)
pygame.init()
main_map = udebs.battleStart("zanar2.xml")
main_map.controlMove('empty', 'empty', 'init')
main_map.controlTime(0)
mainClock = pygame.time.Clock()

#display
mainSurface = pygame.display.set_mode((400, 500), 0, 32)
pygame.display.set_caption('Tactical RPG demo')
pygame.mouse.set_visible(False)

#fonts
basicFont = pygame.font.SysFont(None, 48)
smallFont = pygame.font.SysFont(None, 24)

#music
#overworld = pygame.mixer.Sound('overworld.ogg')
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
        selection['x'] +=1
        if selection['x'] > selection['xmax']:
            selection['x'] = selection['xmax']
    elif event.key == K_LEFT:
        selection['x'] -=1
        if selection['x'] < 0:
            selection['x'] = 0
    elif event.key == K_UP:
        selection['y'] -=1
        if selection['y'] < 0:
            selection['y'] = 0
    elif event.key == K_DOWN:
        selection['y'] +=1
        if selection['y'] > selection['ymax']:
            selection['y'] = selection['ymax']
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
        for x in range(8):
            for y in range(8):
                target = (x,y)
                targetenv = env.createTarget('hero', target, move) 
                if env.testRequire(targetenv) == True:
                    highlighted.append([x,y])
        return highlighted        
    
    #definitions    
    tile = pygame.Rect(( 0, 0 ), ( 49, 49 ))
    selection = {'x': 0, 'y': 0, "xmax": 7, "ymax": 7}
    inport = udebs.battleStart("rpg.xml")
    active_selection = False
    battle = []
    win = False
    boss = False
    
    #initial highlight
    highlighted = []
    highlighted = high_update('travel', main_map)
    
    
    #game loop
    while True:
        
        for entry in inport.getLog():
            if "inventory" in entry:
                message(entry, smallFont)
        
        for mob in battle[:]:
            message("BATTLE ENGAGED!!!")
            inport.controlMove("empty", "empty", 'init')
            
            inport = subBattle(inport)
            main_map.controlMove("hero", mob, "KO")
            inport.controlMove('treasure', 'party', 'get_item')
            for entry in inport.getLog():
                if "inventory" in entry:
                    message(entry, smallFont)
            highlighted = high_update('travel', main_map)
            battle.remove(mob)
            
        if win:
            message("Level Complete!!!")
            main_map.controlMove("empty", "empty", 'finish')
            inport.controlMove("empty", "empty", 'finish')
            main_map.controlMove('empty', 'empty', 'init')
            main_map.controlTime(1)
            highlighted = high_update('travel', main_map)
            win = False
            selection['x'] = 0
            selection['y'] = 0
            battle = []
        
        if boss:
            message("Engaging Boss Monster")
            inport.controlMove("empty", "empty", 'recruit_boss')
            inport = subBattle(inport)
            
            #you win game is over.
            message("You Win! Game Over!")
            pygame.quit()
            sys.exit()
        
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == KEYDOWN:
                arrow_update(event, selection)                              
                
                #selection target
                if event.key == K_RETURN:
                    trgt = (selection['x'], selection['y'])
                    main_map.controlMove('hero', trgt, 'travel')
                    #move enemies
                    for unit in main_map.getGroup("mob"):
                        if unit == "hero":
                            continue
                        loc = main_map.getLocation(unit)
                        if loc:
                            loc = (loc[0]+random.randint(-1, 1), loc[1]+random.randint(-1, 1))
                            main_map.controlMove(unit, loc, 'travel')
                        if main_map.getDistance('hero', unit, 'pinf') <= 1:
                            battle.append(unit)
                    #check proximity
                    if main_map.getDistance('hero', 'treasure', 'pinf') <= 1:
                        inport.controlMove('treasure', 'party', 'get_item')
                        main_map.controlMove('hero', "treasure", "KO")
                    if main_map.getDistance('hero', 'goal', 'pinf') <= 1:
                        win = True
                    if main_map.getDistance('hero', 'boss', 'pinf') <= 1:
                        boss = True
                    main_map.controlTime(0)
                    main_map.controlTime(1)
                    highlighted = high_update('travel', main_map)              
                 
                if event.key == K_q:
                    inport = menuScreen(inport)
                    
        #redraw the Unit board 
        mainSurface.fill((0, 0, 0))
        for x in range(8):
            for y in range(8):
                tile.topleft = (50*x, 50*y)
                colour = WHITE
                if [x,y] in highlighted:
                    colour = GREEN                
                if x == selection['x'] and y == selection['y']:
                    colour = RED
                pygame.draw.rect(mainSurface, colour, tile)
                unit = main_map.getMap((x, y))
                if unit != 'empty':
                    sprite_colour = BLACK
                    sprite_symbol = main_map.getStat(unit, 'sprite')
                    mainSurface.blit(basicFont.render(sprite_symbol, True, sprite_colour, colour), (x*50+10, y*50+10))
        
        drawText("Level " + str(inport.getStat("recruiter", "LVL")), basicFont, 200,450, GREEN, BLACK)
        pygame.display.update()  
        mainClock.tick(60)

def menuScreen(inport):    
    #definitions
    mode = "equip"
    selectBoxMenu = pygame.Rect( 125, 0, 100, 25 )
    selection = {'x': 0, 'y': 0, "xmax": 1, "ymax": 2}
    selectItem = {'x': 0, 'y': 0, "xmax": 3, "ymax": 1}
    
    #game loop
    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            
            #key inputs for menu
            if event.type == KEYDOWN:    
                if mode == "equip":
                    arrow_update(event, selection)
                elif mode == "inventory":
                    arrow_update(event, selectItem)
                        
                if event.key == K_q:
                    inport.getLog()
                    return inport
                       
                if event.key == K_ESCAPE:
                    if mode == "inventory":
                        mode = "equip"
                        
                if event.key == K_RETURN:
                    if mode == "equip":
                        mode = "inventory"
                    elif mode == "inventory":
                        #collect data
                        oldItem_unit = ["fighter", "wmage", "bmage"][selection['y']]
                        oldItem_type = ["weapon", "hat"][selection['x']]
                        oldItem = inport.getListGroup(oldItem_unit, "equip", oldItem_type)

                        try:
                            transferItem = inport.getStat("party", "inventory")[selectItem['x'] + 4*selectItem['y']]
                        except IndexError:
                            transferItem = False
                        transferChar = ["fighter", "wmage", "bmage"][selection['y']]
                        
                        #one use items.
                        if transferItem in ['potion', 'mana']:
                            inport.controlMove(transferChar, transferChar, transferItem)
                            inport.controlTime(0)
                        
                        #change equipment
                        else:
                            #unequip old item
                            if oldItem:
                                inport.controlList(inport.getListGroup(transferChar, "group", "TEMPLATE"), "equip", oldItem, "remove")
                                inport.controlList("party", "inventory", oldItem, 'add')
                            
                            #requip new item
                            if transferItem:
                                if transferChar == "fighter":
                                    weapon = "sword"
                                else:
                                    weapon = "staff"
                                if inport.controlList(inport.getListGroup(transferChar, "group", "TEMPLATE"), 'equip', transferItem, 'add'):
                                    inport.controlList("party", "inventory", transferItem, "remove")
                        
                        #cleanup
                        mode = "equip"
                        del oldItem, transferItem, transferChar
        
        #clear and reprint static                        
        mainSurface.fill((255, 255, 255))
        char = ["fighter", "wmage", "bmage"][selection['y']]
        chargroup = inport.getListGroup(char, "group", "TEMPLATE")
        strhp = str(inport.getStat(char, "HP")) + "/" + str(inport.getStat(chargroup, "HP"))
        strmp = str(inport.getStat(char, "MP")) + "/" + str(inport.getStat(chargroup, "MP"))
        
        pygame.draw.line(mainSurface, BLACK, (0,100), (400,100))
        pygame.draw.line(mainSurface, BLACK, (0,400), (400,400))
        pygame.draw.line(mainSurface, BLACK, (20,175), (380,175))
        pygame.draw.line(mainSurface, BLACK, (20,250), (380,250))
        pygame.draw.line(mainSurface, BLACK, (20,325), (380,325))
        pygame.draw.line(mainSurface, BLACK, (133,120), (133,380))
        pygame.draw.line(mainSurface, BLACK, (266,120), (266,380))
        drawText(inport.getStat(char, "DESC"), basicFont, 200, 25, BLACK, WHITE)
        drawText("HP", smallFont, 50, 60, BLACK, WHITE)
        drawText("MP", smallFont, 150, 60, BLACK, WHITE)
        drawText("Mellee", smallFont, 250, 60, BLACK, WHITE)
        drawText("Magic", smallFont, 350, 60, BLACK, WHITE)
        drawText(strhp, smallFont, 50, 85, BLACK, WHITE)
        drawText(strmp, smallFont, 150, 85, BLACK, WHITE)
        drawText(str(inport.getStat(char, "MEL")), smallFont, 250, 85, BLACK, WHITE)
        drawText(str(inport.getStat(char, "MGK")), smallFont, 350, 85, BLACK, WHITE)
        drawText("weapon", smallFont, 199, 137, BLACK, WHITE)
        drawText("hat", smallFont, 332, 137, BLACK, WHITE)

        #print green indicator
        if mode == "equip":        
            selectBoxMenu.centerx = 133*selection['x'] + 199
            selectBoxMenu.centery = 75*selection['y'] + 212
        elif mode == "inventory":
            selectBoxMenu.centerx = 100*selectItem['x'] + 50
            selectBoxMenu.centery = 50*selectItem['y'] + 425      
        pygame.draw.rect(mainSurface, (0,255,0), selectBoxMenu)
        
        #print equipment
        i = 0
        for unit in ['fighter', 'wmage', 'bmage']:
            j = i*75 + 212
            if i == selection['y']:
                row = True
            else:
                row = False
            drawText(unit, smallFont, 66, j, BLACK, WHITE)
            weapon = inport.getListGroup(unit, "equip", 'weapon')
            hat = inport.getListGroup(unit, "equip", "hat")
            if weapon:
                if row and selection['x'] == 0:
                    colour = GREEN
                else:
                    colour = WHITE
                drawText(weapon, smallFont, 199, j, BLACK, colour)
            if hat:
                if row and selection['x'] == 1:
                    colour = GREEN
                else:
                    colour = WHITE
                drawText(hat, smallFont, 332, j, BLACK, colour)
            i +=1
        
        #draw inventory
        inventory = inport.getStat("party", "inventory")
        for index in range(len(inventory)):
            if index < 4:
                y = 425
            else:
                y = 475
            if selectItem['x'] + 4*selectItem['y'] == index and mode == "inventory":
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
    mode = "wait"
    menu = {'x': 0, 'y': 0, "xmax": 1, "ymax": 2}
    target = {'x': 0, 'y': 0, "xmax": 1, "ymax": 2}
    doOnce = False
    activeUnits = []
    unitIndex = 0
    
    fun = battle_map.getStat
    color = {
        'fighter': [int(fun('fighter', "r")), int(fun('fighter',"g")), int(fun('fighter',"b"))],
        "wmage": [int(fun('wmage', "r")), int(fun('wmage',"g")), int(fun('wmage',"b"))],
        'bmage': [int(fun('bmage', "r")), int(fun('bmage',"g")), int(fun('bmage',"b"))],
        monster1: [int(fun(monster1, "r")), int(fun(monster1,"g")), int(fun(monster1,"b"))],
        monster2: [int(fun(monster2, "r")), int(fun(monster2,"g")), int(fun(monster2,"b"))],
        monster3: [int(fun(monster3, "r")), int(fun(monster3,"g")), int(fun(monster3,"b"))],
    }
    
    for mob in [monster1, monster2, monster3]:
        if mob == 'empty':
            color[mob] = GREY
   
   #game loop
    while True:
        #checks for active units.
        if unitIndex >= len(activeUnits):
            
            activeUnits = []
            for unit in battle_map.getGroup("party", False) + battle_map.getGroup("monster", False):
                if battle_map.getStat(unit, "ACT") >= 2:
                    activeUnits.append(unit)
            
            if len(activeUnits) > 0:
                mode = "active"
            else:
                mode = "wait"
            unitIndex = 0
        
        if mode == "active":
            #if unit is a monster
            if activeUnits[unitIndex] in [monster1, monster2, monster3]:
                #select move to cast
                caster = activeUnits[unitIndex]
                moveList = battle_map.getStat(caster, 'movelist')    
                moveList_possible = []
                for entry in moveList:
                    test = battle_map.createTarget(caster, 'empty', entry)
                    if battle_map.testRequire(test):
                        moveList_possible.append(entry)
                if len(moveList_possible) == 0:
                    print(activeUnits[unitIndex], "can't attack")  
                else:
                    mindex = random.randint(0, len(moveList_possible)-1)
                    move = moveList_possible[mindex]
                    targets = []
                    if move in ['heal', 'barrier']:
                        targets = [monster1, monster2, monster3]
                    else:
                        targets = ['fighter', 'wmage', 'bmage']
                    targets_possible = []
                    for unit in targets:
                        user_status = battle_map.getStat(unit, "status")
                        if "KO" not in user_status: 
                            if'SACRIFICE' not in user_status:
                                targets_possible.append(unit)            
                
                    etarget = targets[random.randint(0, len(targets)-1)]
                    if 'DEFEND' in battle_map.getStat('fighter', 'status'):
                        if 'fighter' in targets_possible:
                            etarget = 'fighter'
                        
                    battle_map.controlMove(caster, etarget, move)
                    battle_map.controlTime(0)
                           
                unitIndex +=1
            #else unit is a player
            else:
                mode = "player-menu"
        
        #check for keyboard input
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            
            #key inputs for menu
            if event.type == KEYDOWN:
                if mode == "player-menu" and doOnce == False:
                    arrow_update(event, menu)
                    
                    #skip player
                    if event.key == K_ESCAPE:
                        caster = activeUnits[unitIndex]
                        ltarget = "empty"
                        battle_map.controlMove( caster, ltarget, 'pass' )
                        battle_map.controlTime(0)
                        #reset
                        mode = "active"
                        target['x'] = 0
                        target['y'] = 0
                        menu['y'] = 0
                        unitIndex +=1
                        doOnce = True

                    #make selection
                    elif event.key == K_RETURN:
                        try:
                            move = battle_map.getStat(activeUnits[unitIndex], 'movelist')[menu['y'] +3*menu['x']]
                            if battle_map.getStat(move, 'skip'):
                                caster = activeUnits[unitIndex]
                                battle_map.controlMove( caster, 'empty', move )
                                battle_map.controlTime(0)
                                mode = "active"
                                move = False
                                target['x'] = 0
                                target['y'] = 0
                                menu['y'] = 0
                                menu['x'] = 0
                                unitIndex +=1
                            else:
                                mode = "player-target"
                            doOnce = True
                                
                        except IndexError:
                            pass
                                           
                if mode == "player-target" and doOnce == False:
                    arrow_update(event, target)
                    
                    if event.key == K_ESCAPE:
                        mode = "player-menu"
                    
                    #activate move
                    if event.key == K_RETURN:
                        #cast
                        caster = activeUnits[unitIndex]
                        ltarget = (target['x'], target['y'])
                        battle_map.controlMove( caster, ltarget, move )
                        battle_map.controlTime(0)
                        #reset
                        mode = "active"
                        move = False
                        target['x'] = 0
                        target['y'] = 0
                        menu['y'] = 0
                        menu['x'] = 0
                        unitIndex +=1
                        doOnce = True

        #draw menu
        mainSurface.fill((255, 255, 255))
        pygame.draw.rect(mainSurface, GREY, pygame.Rect((0, 100), (400, 300)))
        
        if mode == "player-target":
            drawText(battle_map.getStat(move, "DESC"), smallFont, 200, 60, (0,0,0), (255,255,255))
        
        #This section needs a cleanup
        if mode == "player-menu":
            drawText(battle_map.getStat(activeUnits[unitIndex], "DESC"), smallFont, 200, 20, (0,0,0), (255,255,255))
            
            spacing = 40
            _i = 0
            x = 125
            for attack in battle_map.getStat(activeUnits[unitIndex], 'movelist'):
                if _i >= 3:
                    _i = 0
                    spacing = 40
                    x +=175
                
                colour = WHITE
                if menu['y'] == _i:
                    if menu['x']*175 + 125 == x:
                        selectBoxMenu.centery = spacing
                        selectBoxMenu.centerx = x
                        pygame.draw.rect(mainSurface, GREEN, selectBoxMenu)
                        colour = GREEN
                drawText(battle_map.getStat(attack, "DESC") , smallFont, x, spacing, BLACK, colour)
                spacing +=20
                _i +=1
        
        
        #draw target selection box
        if mode == "player-target":
            selectBoxTarget.centerx = 290*target['x'] + 55
            selectBoxTarget.centery = 100*target['y'] + 155
            pygame.draw.rect(mainSurface, (0,255,0), selectBoxTarget)
        
        #update colour
        for unit in color.keys():
            if unit != 'empty':
                color[unit] = [int(fun(unit, "r")), int(fun(unit,"g")), int(fun(unit,"b"))]
        
        if "KO" not in battle_map.getStat("fighter", "status"):
            pygame.draw.rect(mainSurface, color['fighter'], pygame.Rect((50, 250), (10, 10))) 
        wmage_status = battle_map.getStat("wmage", "status")
        if "KO" not in wmage_status and 'SACRIFICE' not in wmage_status:
            pygame.draw.rect(mainSurface, color['wmage'], pygame.Rect(( 50, 350 ), ( 10, 10 )))
        if "KO" not in battle_map.getStat("bmage", "status"):
            pygame.draw.rect(mainSurface, color['bmage'], pygame.Rect(( 50, 150 ), ( 10, 10 )))
        
        if "KO" not in battle_map.getStat(monster1, "status"):
            pygame.draw.rect(mainSurface, color[monster1], pygame.Rect(( 340, 150 ), ( 10, 10 )))
        if "KO" not in battle_map.getStat(monster2, "status"):
            if monster2 =='boss':
                x = 50
            else:
                x = 10
            pygame.draw.rect(mainSurface, color[monster2], pygame.Rect(( 345 - x/2, 250 ), ( x, x )))
        if "KO" not in battle_map.getStat(monster3, "status"):
            pygame.draw.rect(mainSurface, color[monster3], pygame.Rect(( 340, 350 ), ( 10, 10 )))
        
        #draw bmage stats
        drawText("Black Mage", smallFont, 50, 425, BLACK, WHITE)
        drawText(str(battle_map.getStat("bmage", "HP")), smallFont, 50, 445, RED, WHITE)
        drawText(str(battle_map.getStat("bmage", "MP")), smallFont, 50, 465, BLUE, WHITE)
        
        #draw fighter stats
        drawText("Fighter", smallFont, 200, 425, BLACK, WHITE)
        drawText(str(battle_map.getStat("fighter", "HP")), smallFont, 200, 445, RED, WHITE)
        drawText(str(battle_map.getStat("fighter", "MP")), smallFont, 200, 465, BLUE, WHITE)
        
        #draw wmage stats
        drawText("White Mage", smallFont, 350, 425, BLACK, WHITE)
        drawText(str(battle_map.getStat("wmage", "HP")), smallFont, 350, 445, RED, WHITE)
        drawText(str(battle_map.getStat("wmage", "MP")), smallFont, 350, 465, BLUE, WHITE)
        
        #draw messages
        for entry in battle_map.getLog():
            for skip in ["failed", "empty", "delay", "KO", "uses POISON", "OVERHEAL", "DEFEND_ACTIVE"]:
                if skip in entry:
                    break
            else:
                for add in ["uses", "HP", "added"]:
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
        if "KO" in battle_map.getStat(monster1, "status") or monster1 == "empty":
            if "KO" in battle_map.getStat(monster2, "status") or monster2 == "empty":
                if "KO" in battle_map.getStat(monster3, "status") or monster3 == "empty":
                    drawText("VICTORY!!!", basicFont, 200,250, [0,255,0], [125,125,125])
                    pygame.display.update()
                    while True:
                        event = pygame.event.wait()
                        if event.type == KEYDOWN and event.key == K_RETURN:
                            return battle_map
        #draw lose
        #draw win
        if "KO" in battle_map.getStat('fighter', "status"):
            if "KO" in battle_map.getStat('wmage', "status"):
                if "KO" in battle_map.getStat('bmage', "status"):
                    drawText("DEFEAT", basicFont, 200,250, [0,255,0], [125,125,125])
                    pygame.display.update()
                    while True:
                        event = pygame.event.wait()
                        if event.type == KEYDOWN and event.key == K_RETURN:
                            pygame.quit()
                            sys.exit()
                    
        #increment time
        doOnce = False
        pygame.display.update()
        if mode == "wait":
            battle_map.controlTime()
        mainClock.tick(60)
        
if __name__ == "__main__":
    main()
