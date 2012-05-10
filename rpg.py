import pygame, sys, udebs, random
from pygame.locals import *

#initialize pygame and udebs
pygame.init()
udebs.battleStart("rpg.xml")


#quick function to make printing to screen easier.
def drawText(text, font, surface, x, y ,color, background):
    words = font.render(text, True, color, background)
    rect = words.get_rect(center=(x,y))
    surface.blit(words, rect)
    return

#initialize pygame clock
mainClock = pygame.time.Clock()

#define Color
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
GREY = (125, 125, 125)

#initialize fonts
basicFont = pygame.font.SysFont(None, 48)
smallFont = pygame.font.SysFont(None, 24)

#initialize main surface
pygame.display.set_caption('A simple RPG battle system')
mainSurface = pygame.display.set_mode((400, 800), 0, 32)

#initialize screen areas
#( left corner, top corner ), ( width, height )
menu = {"color": WHITE, 'rect': pygame.Rect(( 0, 0 ), ( 400, 200 )) }
battle = {"color": GREY, 'rect': pygame.Rect(( 0, 200 ), ( 400, 400 )) }
public = {'color': WHITE, 'rect': pygame.Rect(( 0, 600 ), ( 400, 200 )) }

#initialize selection boxes
selectBoxMenu = pygame.Rect( 125, 0, 150, 20 )
selectBoxTarget = pygame.Rect(0, 0, 20, 20)

#initialize player "sprites"
sfighter = {'rect': pygame.Rect(( 50, 400 ), ( 10, 10 )), 'color': RED}      
swmage =   {'rect': pygame.Rect(( 50, 500 ), ( 10, 10 )), 'color': WHITE}   
sbmage =   {'rect': pygame.Rect(( 50, 300 ), ( 10, 10 )), 'color': BLACK}     
szombie1 = {'rect': pygame.Rect(( 340, 300 ), ( 10, 10 )), 'color': GREEN}
szombie2 = {'rect': pygame.Rect(( 340, 400 ), ( 10, 10 )), 'color': GREEN}
szombie3 = {'rect': pygame.Rect(( 340, 500 ), ( 10, 10 )), 'color': GREEN}

#initialize state variables
activeMenu = False
selectMenu = 0

activeTarget = False
selectTarget = {'x': 1, 'y': 0}

doOnce = False
pause = False

unitIndex = 0
activeUnits = []

#game loop
while True:
    
    #rebuilds active unit if list was empty, or unitIndex has rolled over
    if unitIndex >= len( activeUnits ):
        activeUnits = udebs.getActiveUnits()
        unitIndex = 0

    #controls if menues or AI program should run.    
    if activeTarget == False:
        if len( activeUnits ) > 0:
            pause = True
            if len(udebs.getActiveMoves( activeUnits[unitIndex] ) ) > 0:
                if activeUnits[ unitIndex ] in ["zombie1", "zombie2", "zombie3"]:
                    user = []
                    for player in ["fighter", "wmage", "bmage"]:
                        if "KO" not in udebs.getStat(player, udebs.STATUS):
                            user.append(player)
                
                    pygame.time.wait(500)
                    udebs.randomAI(activeUnits[ unitIndex ], user[random.randint(0, len(user)-1) ] )
                    unitIndex +=1
                else:
                    activeMenu = True
                    activeTarget = False
            else:
                unitIndex +=1
        else:
            pause = False
    
    #check for keyboard input
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        
        #key inputs for menu
        if event.type == KEYDOWN and activeMenu == True and doOnce == False:
            if event.key == K_ESCAPE:
                unitIndex +=1
                selectMenu = 0
                activeMenu = False
                doOnce = True
                
            #menu up    
            if event.key == K_UP:
                selectMenu -=1
                if selectMenu < 0:
                    selectMenu = 0
                doOnce = True            
            #menu down
            if event.key == K_DOWN:
                selectMenu +=1
                if selectMenu > len(udebs.getStat( activeUnits[ unitIndex ], "movelist"))-1:
                    selectMenu = len(udebs.getStat( activeUnits[ unitIndex ], "movelist"))-1
                doOnce = True
            #make selection
            if event.key == K_RETURN:
                activeTarget = True
                activeMenu = False
                doOnce = True
                
        if event.type == KEYDOWN and activeTarget == True and doOnce == False:
            #return to move select
            if event.key == K_ESCAPE:
                activeTarget = False
                activeMenu = True
                selectTarget = {'x': 1, 'y': 0}
                doOnce = True
            
            #Move target up
            if event.key == K_UP:
                selectTarget['y'] -=1
                if selectTarget['y'] < 0:
                    selectTarget['y'] = 0
                doOnce = True
            #move target down
            if event.key == K_DOWN:
                selectTarget['y'] +=1
                if selectTarget['y'] > udebs.getMap("y")-1:
                    selectTarget['y'] = udebs.getMap("y")-1
                doOnce = True
            #move target right
            if event.key == K_RIGHT:
                selectTarget['x'] +=1
                if selectTarget['x'] > udebs.getMap("x")-1:
                    selectTarget['x'] = udebs.getMap("x")-1
                doOnce = True
            #move target left
            if event.key == K_LEFT:
                selectTarget['x'] -=1
                if selectTarget['x'] < 0:
                    selectTarget['x'] = 0
                doOnce = True
            #activate move
            if event.key == K_RETURN:
                activeTarget = False
                udebs.controlMove( activeUnits[ unitIndex ], [ selectTarget['x'], selectTarget['y'] ], udebs.getActiveMoves(activeUnits[unitIndex])[selectMenu] )
                udebs.battleTick(0)
                selectTarget = {'x': 1, 'y': 0}
                selectMenu = 0
                unitIndex +=1
                doOnce = True
    
    #draw menu          
    pygame.draw.rect(mainSurface, menu['color'], menu['rect'])
    
    #draw current active menu
    if activeMenu == True:
        drawText(udebs.getStat(activeUnits[ unitIndex], "DESC"), smallFont, mainSurface, 200, 20, BLACK, WHITE)
        spacing = 40
        _i = 0
        for attack in udebs.getActiveMoves( activeUnits[ unitIndex ] ):
            if selectMenu == _i:
                selectBoxMenu.centery = spacing
                pygame.draw.rect(mainSurface, GREEN, selectBoxMenu)
                drawText(udebs.getStat(attack, "DESC") , smallFont, mainSurface, 200, spacing, BLACK, GREEN)
            else:
                drawText(udebs.getStat(attack, "DESC") , smallFont, mainSurface, 200, spacing, BLACK, WHITE)
            spacing +=20
            _i +=1
    
    #draw battle board         
    pygame.draw.rect(mainSurface, battle['color'], battle['rect'] )
    
    #draw target selection box
    if activeTarget == True:
        selectBoxTarget.centerx = 290*selectTarget['x'] + 55
        selectBoxTarget.centery = 100*selectTarget['y'] + 305
        pygame.draw.rect(mainSurface, GREEN, selectBoxTarget)
    
    #draw each combatant
    if "KO" not in udebs.getStat("fighter", "status"):
        pygame.draw.rect(mainSurface, sfighter['color'], sfighter['rect']) 
    if "KO" not in udebs.getStat("wmage", "status"):
        pygame.draw.rect(mainSurface, swmage['color'], swmage['rect'])
    if "KO" not in udebs.getStat("bmage", "status"):
        pygame.draw.rect(mainSurface, sbmage['color'], sbmage['rect'])
    if "KO" not in udebs.getStat("zombie1", "status"):
        pygame.draw.rect(mainSurface, szombie1['color'], szombie1['rect'])
    if "KO" not in udebs.getStat("zombie2", "status"):
        pygame.draw.rect(mainSurface, szombie2['color'], szombie2['rect'])
    if "KO" not in udebs.getStat("zombie3", "status"):
        pygame.draw.rect(mainSurface, szombie3['color'], szombie3['rect'])
    
    #draw public            
    pygame.draw.rect(mainSurface, public['color'], public['rect'])
    
    #draw bmage stats
    drawText("Black Mage", smallFont, mainSurface, 50, 700, BLACK, WHITE)
    drawText(str(udebs.getStat("bmage", "HP")), smallFont, mainSurface, 50, 720, RED, WHITE)
    drawText(str(udebs.getStat("bmage", "MP")), smallFont, mainSurface, 50, 740, BLUE, WHITE)
    
    #draw fighter stats
    drawText("Fighter", smallFont, mainSurface, 200, 700, BLACK, WHITE)
    drawText(str(udebs.getStat("fighter", "HP")), smallFont, mainSurface, 200, 720, RED, WHITE)
    drawText(str(udebs.getStat("fighter", "MP")), smallFont, mainSurface, 200, 740, BLUE, WHITE)
    
    #draw wmage stats
    drawText("White Mage", smallFont, mainSurface, 350, 700, BLACK, WHITE)
    drawText(str(udebs.getStat("wmage", "HP")), smallFont, mainSurface, 350, 720, RED, WHITE)
    drawText(str(udebs.getStat("wmage", "MP")), smallFont, mainSurface, 350, 740, BLUE, WHITE)
    
    #increment time
    doOnce = False
    pygame.display.update()
    if pause == False:
        udebs.battleTick()        
    mainClock.tick(60)
    
