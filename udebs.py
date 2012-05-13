import re, sys, random, math, copy
from xml.etree import ElementTree

#---------------------------------------------------
#             predefined variables                 -
#---------------------------------------------------

#global dict
ID = "ID"                   #string
GROUP = "group"             #list

#unit dict
STATUS = "status"           #list
MOVELIST = "movelist"       #list
EQUIP = "equip"             #list
TYPE = "type"               #string
INCREMENT = "INCREMENT"     #number

#move dict
EFFECT = "effect"           #list
REQUIRE = "require"         #list

#env variables
STATS = "STATS"             #list
LISTS = "LISTS"             #list
STRINGS = "STRINGS"         #list
TICK = "TICK"               #list
UNITS = "UNITS"             #list
TIME = "TIME"               #number
DELAY = "DELAY"             #list
MAP = "MAP"                 #list

#built in STATS
ACT = "ACT"                 #number
SPD = "SPD"                 #number
        
#---------------------------------------------------
#                  XML Setup                       -
#---------------------------------------------------

OBJECT = {
    "empty": {ID: "empty"},
    "ENV": {},    
    }
    
STATE = []

#eventually this will be the config parser
def battleStart(xml_file):
    try:
        tree = ElementTree.parse(xml_file)
    except IOError as inst:
        print( "battleStart Error:", inst)
        sys.exit()
    
    root = tree.getroot()
    
    #create ENV
    ENV = OBJECT["ENV"]
    
    def_stats = root.find("stats")   
    
    ENV[STATS] = [ACT, SPD]
    ENV[LISTS] = [EQUIP, MOVELIST, STATUS, GROUP]
    ENV[STRINGS] = [TYPE, ID]
    
    def_stats = root.find("stats")
    if def_stats is not None:    
        for stat in def_stats:
            ENV[STATS].append(stat.text)
            
    def_lists = root.find("lists")
    if def_lists is not None:    
        for stat in def_lists:
            ENV[LISTS].append(stat.text)
            
    def_strings = root.find("strings")
    if def_strings is not None:    
        for stat in def_strings:
            ENV[STRINGS].append(stat.text)
            
    
    ENV[ID] = "ENV"
    ENV[TIME] = 0
    ENV[DELAY] = []
    ENV[TICK] = []
    ENV[UNITS] = []
    
    #set empty
    
    for stat in ENV[STATS]:
        OBJECT['empty'][stat] = 0
        
    for lists in ENV[LISTS] + [EFFECT, REQUIRE]:
        OBJECT['empty'][lists] = []
        
    for string in ENV[STRINGS]:
        OBJECT['empty'][string] = ''
    
    OBJECT['empty'][ID] = 'empty'
    
    #set config
    config = root.find("config")
    if config is not None:
        revert = config.findtext("revert")
        if revert is not None:
            ENV["REVERT"] = int(revert)
        else:
            ENV["REVERT"] = 0
    else:
        ENV["REVERT"] = 0
    
    #sets map
    ENV[MAP] = []
    field_map = root.find("MAP")
    
    if field_map is not None:    
        for row in field_map:
            ENV[MAP].append(re.split("\W*,\W*", row.text))
    
    #loop, create all entity type objects
    entities = root.find("entities")
    
    if entities is not None:
    
        for item in entities:
            new_entity = {}
            
            iden = item.findtext("ID")    
            if iden is not None:
                new_entity[ID] = iden
            
            new_entity[REQUIRE] = []
            require = item.find("require")        
            if require is not None:
                for item2 in require:
                    new_entity[REQUIRE].append(item2.text)
    
            new_entity[EFFECT] = []
            effect = item.find("effect")        
            if effect is not None:
                for item2 in effect:
                    new_entity[EFFECT].append(item2.text)
                    
            new_entity[INCREMENT] = 0
            
            #insert defined stats        
            for stat in ENV[STATS]:
                new_entity[stat] = 0
    
            stats = item.find("stats")
            if stats is not None:
                for stat in stats:
                    new_entity[stat.tag] = int(stat.text)
                    
            #insert all defined strings
            for strings in ENV[STRINGS]:
                value = item.findtext(strings)
                if value is not None:
                    new_entity[strings] = value
                else:
                    new_entity[strings] = ""
            
            #insert all defined lists
            for lst in ENV[LISTS]:
                new_entity[lst] = []
                
                find_list = item.find(lst)
                if find_list is not None:
                    for value in find_list:
                        new_entity[lst].append(value.text)
                        
            OBJECT[new_entity[ID]] = new_entity            

    #create all unit type objects    
    units = root.find("units")
    if units is not None:
        
        for item in units:
            new_unit = {}
    
            iden = item.findtext("ID")    
            if iden is not None:
                new_unit[ID] = iden
            
            new_unit[INCREMENT] = 0
            
            new_unit[REQUIRE] = []
            new_unit[EFFECT] = []
            
            #insert defined stats        
            for stat in ENV[STATS]:
                new_unit[stat] = 0
    
            stats = item.find("stats")
            if stats is not None:
                for stat in stats:
                    new_unit[stat.tag] = int(stat.text)
                    
            #insert all defined strings
            for strings in ENV[STRINGS]:
                value = item.findtext(strings)
                if value is not None:
                    new_unit[strings] = value
                else:
                    new_unit[strings] = ""
            
            #insert all defined lists
            for lst in ENV[LISTS]:
                new_unit[lst] = []
                
                find_list = item.find(lst)
                if find_list is not None:
                    for value in find_list:
                        new_unit[lst].append(value.text)
                
            OBJECT[new_unit[ID]] = new_unit
        
            #sets EVN[TICK] and ENV[UNIT]

            if item.get("active") == "active":
                ENV[UNITS].append(new_unit[ID])
            if item.get("tick") == "tick":
                ENV[TICK].append(new_unit[ID])
    
    init = root.find("init")
    if init is not None:
        for effect in init:
            
            try:
                output = interpret('empty', 'empty', 'empty', effect.text, (0,0), (0,0) ) 
            except:
                print("Interpreter Error:", effect)
                raise
            try:
                exec(output)
            except:
                print("invalid effect (", effect,"), (", output,")")
                raise
                
    battleTick(0)
    
    STATE.append(copy.deepcopy(OBJECT))  
    return

#---------------------------------------------------
#            State Functions                       -
#---------------------------------------------------

#adds time units to the main clock, and other things.
def battleTick(time=1):   
    
    if type(time) != type(int()):
        raise Exception("battleTick Error: Only accepts int as argument")
    
    ENV = OBJECT["ENV"]

    if time != 0:
        controlStat("ENV", TIME, time)
        
        for unit in ENV[TICK]:
            controlStat(unit, ACT, time*getStat(unit, SPD))
        for delay in ENV[DELAY]:
            delay["DELAY"] -=time    
    while True:
        check = 0
        #this is a copy of ENV[DELAY] any changes delayed casting makes to this list will come into effect in the next loop.
        for delay in ENV[DELAY][:]:
            if delay["DELAY"] <= 0:
                check +=1
                ENV[DELAY].remove(delay)
                controlMove(delay["CASTER"], delay["TARGET"], delay["MOVE"], delay["COMMAND"], -1)
        if check == 0:
            print("")
            break
    
    #update STATE
    if time != 0:
        #while len(STATE) >= OBJECT["ENV"]["REVERT"]:
        #    STATE.pop(0)
        STATE.append(copy.deepcopy(OBJECT))
    return

def battleRevert(state=1):
    
    if type(state) != type(int()) or state <= 0:
        raise Exception("battleRevert Error: Only accepts int > 0 as argument")
    
    if len(STATE) < state:
        print("Revert failed. Choosen state not available.")
        return
    
    i = len(STATE)
    index = i - state
    if index < 0:
        print("warning negative number")
    
    
    OBJECT.update(copy.deepcopy(STATE[index]))
    
    for count in range(index+1, i):
        del STATE[count]

    print ("revert successful")
    return    
      
#---------------------------------------------------
#                  Get Functions                   -
#---------------------------------------------------
            
#returns a list of all units that can perform at least one move
def getActiveUnits():
    active = []
    for char in OBJECT['ENV'][UNITS]:
        if len(getActiveMoves(char)) > 0:
            active.append(char)
    return active

#returns a list of all moves a unit can perform right now
def getActiveMoves(unit):
    mlist = []
    for move in getStat(unit, MOVELIST):
        flag = testMove(unit, unit, move)
        if flag == True:
            mlist.append(move)
    return mlist

#returns the effective stat for any object.
def getStat(dictionary, stat):
    
    if stat in OBJECT["ENV"][STRINGS] + [TIME]:
        return OBJECT[dictionary][stat]
    
    #STATS, SIZE
    elif stat in OBJECT['ENV'][STATS] + [TIME]:
        
        count = 0
        count +=OBJECT[dictionary][stat]
        
        status_list = OBJECT[dictionary][STATUS][:]
        equip_list = OBJECT[dictionary][EQUIP][:]
        
        #fill out group lists
        for cls in OBJECT[dictionary][GROUP]:
            
            count +=OBJECT[cls][stat]
            status_list.extend( OBJECT[cls][STATUS] ) 
            equip_list.extend( OBJECT[cls][EQUIP] )
        
        #status effects and their groups
        for stus in status_list:
            count +=getStat(stus, stat)
        
        #equip inventories and their groups
        for item in equip_list:
            count +=getStat(item, stat)
        
        return count
    
    #MOVELIST, EFFECT, REQUIRE, INVENTORY, EQUIP
    elif stat in OBJECT['ENV'][LISTS] + [EFFECT, REQUIRE]:
        
        lst = []
        lst.extend(OBJECT[dictionary][stat])
        
        status_list = OBJECT[dictionary][STATUS][:]
        equip_list = OBJECT[dictionary][EQUIP][:]
        
        #fill out group lists
        for cls in OBJECT[dictionary][GROUP]:
            lst.extend( OBJECT[cls][stat] )
            status_list.extend( OBJECT[cls][STATUS] )
            equip_list.extend( OBJECT[cls][EQUIP] )        
        
        #why did I put these here?
        #status effects and their groups
        for stus in status_list:
            lst.extend( getStat(stus, stat) )
        
        #equip inventories and their groups
        for item in equip_list:
            lst.extend( getStat(item, stat) )
        
        return lst
    else:
        raise Exception("Unknown Stat in GetStat") 

#swiss army function. Should probobly break this up.
def getMap(target="all"):
    temp_map = OBJECT['ENV'][MAP]
    
    #returns raw map if no attribute is given
    if target == "all":
        return temp_map        
    
    #returns length of axis if 'x' or 'y' is given.
    elif target == "y":
        return len(temp_map)
    elif target == "x":
        return len(temp_map[0])
    
    #if coordinates are given, returns what is in that spot
    elif type(target) == type(()) or type(target) == type([]):
        try:
            return temp_map[target[1]][target[0]]   
        except IndexError:
            return 'empty'
    else:
        raise Exception("Unknown command in getMap")

#Returns coordinates of a unit, I'd like to make it faster.                
def getLocation( unit ):
    y = 0
    for column in OBJECT['ENV'][MAP]:
        try:
            x = column.index( unit )
            return [x, y]
        except ValueError:
            y +=1
            continue
    return False
    
#returns distance between two objects.
def getDistance(one, two, method):
    
    if type( one ) == type (''):
        one = getLocation( one )
    elif type( two ) == type (''):
        two = getLocation( two )
    if one == False or two == False:
        return float("inf")
    
    #return how far away the objects are along y
    if method == 'y':
        return int( abs( one[1] - two[1] ) )
    
    #return how far away the objects are along x
    elif method == 'x':
        return int( abs( one[0] - two[0] ) )
    
    #x + y, normal rpg distance
    elif method == "p1":
        return int(abs(one[0] - two[0]) + abs(one[1] - two[1]))
    
    #root(x^2 + y^2), real world distance. Rounds down
    elif method == "p2":
        return int(math.sqrt(math.pow(one[0] - two[0], 2) + math.pow(one[1] - two[1], 2)))
    
    #max( x , y ), returns the largest distance either x or y.
    elif method =="pinf":
        if abs(one[0] - two[0]) > abs(one[1] - two[1]):
            return int(abs(one[0] - two[0]))
        else:
            return int(abs(one[1] - two[1]))
    else:
        raise Exception("Unknown Command in getDistance")

#returns every unit in a particular group. Terrible function
#for use with targeting data only. Will change in future releases       
def getGroup( group ):
    group_list = OBJECT['ENV'][UNITS]
    return_list = []
    for unit in group_list:
        if group in getStat( unit, GROUP ):
            return_list.append(unit)
    return return_list

#---------------------------------------------------
#               Control Functions                  -
#---------------------------------------------------
def controlRecruit(clone, position=None):
    
    if clone == 'empty':
        return
    
    try:
        new_unit = copy.deepcopy(STATE[0][clone])
    except KeyError:
        ("recruit failed, unit to clone not found")
        return
       
    increment = OBJECT[clone][INCREMENT]
    increment +=1      
    OBJECT[clone][INCREMENT] = increment
    
    new_unit[ID] = clone + str(increment)
    
    OBJECT[new_unit[ID]] = new_unit
    
    print(new_unit[ID], "has been recruited")       
            
    if position is not None:
        controlTravel(new_unit[ID], position)
    
#moves units for effects
def controlTravel(caster, targetLoc, command='travel'):
    
    ENV = OBJECT['ENV']
    
    if command != 'travel':
        tempLoc = getLocation(caster)
        if command == 'x':
            tempLoc[0] +=targetLoc
        elif command == 'y':
            tempLoc[1] +=targetLoc
        elif command =='xy':
            tempLoc[0] +=targetLoc[0]
            tempLoc[1] +=targetLoc[1]
        targetLoc = tempLoc
    
    casterLoc = getLocation(caster)
    target = getMap( targetLoc )
    
    #erase old location
    if casterLoc:
        ENV[MAP][casterLoc[1]][casterLoc[0]] = 'empty'
    
    #move caster to new location 
    ENV[MAP][targetLoc[1]][targetLoc[0]] = caster
    if caster != 'empty':
        print (getStat(caster, ID), "has moved to", targetLoc)
    if target != 'empty':
        print (target, "has been bumped")

#activates stat changes brought on by effects        
def controlStat( target, stat, increment ):
    if target == 'empty':
        return
    
    newValue = OBJECT[target][stat] + increment
    OBJECT[target][stat] = newValue
    print(target, stat, "changed by", increment, "is now", getStat(target, stat))

def controlString( target, desc, new):
    if target == 'empty':
        return
    
    if desc == "ID":
        print("String update failed, ID cannot be changed.")
    OBJECT[target][desc] = new
    print(target, desc, "is now", new)
    
    
def controlList( target, lst, entry, command='add'):
    if target == 'empty':
        return
    
    check = OBJECT[target][lst]
    
    if command == "add":
        check.append(entry)
        print(entry, "added to", target, lst)
    
    elif command == "remove":
        if entry in check:
            check.remove(entry)
            print(entry, "removed from", target, lst)
    
#Activates moves, and statuses. 
def controlMove( caster, target , move, command="cast", delay=-1):
    
    delay = int(delay)
    
    #accepted commands, cast, force, remove, add, item, equip   
    if command not in ['cast', 'chain']:
        raise Exception("Unknown command in controlMove.")
    
    #check to see if target is a list of targets. (target could be a position, this is ignored for now.)
    if type(target) == type([]):
        if type(target[0]) != type(0):
            for trgt in target:
                controlMove( caster, trgt, move, command, delay )
            return True
            
    #if delay is positive or 0, sends move to delay.
    if delay >= 0:
        print(command, getStat(move, ID), "added to Delay for", delay)
        OBJECT['ENV'][DELAY].append({"DELAY": delay, "COMMAND": command, "CASTER": caster, "TARGET": target, "MOVE": move})
        return True
    
    #if cast is called, only continue if the move is in the movelist.
    elif command == "cast":
        if move not in getStat(caster, MOVELIST):
            print("move failed,", getStat(move, ID), "not in caster movelist")
            return False
    
    check = testMove(caster, target, move)
    if check != True:
        print(getStat(caster, ID), command, getStat(move, ID), "failed because", check)
        return False
    del check
    
    #Print success.
    if type(target) == type([]):
        trgt = getMap(target)
    else:
        trgt = target
    print(caster, "uses", move, "on", trgt)
   
    #activate effects
    controlEffect(caster, target, move)
    return True
    
    
def controlEffect(caster, target, move):    
    casterLocation = getLocation(caster)
    if type(target) == type([]) or type(target) == type(()):
        targetLocation = target
        target = getMap(targetLocation)
    else:
        targetLocation = getLocation(target)
    
    #activate all the effects
    for effect in getStat(move, EFFECT):
        try:
            output = interpret(caster, target, move, effect, casterLocation, targetLocation) 
        except:
            print("Interpreter Error:", effect)
            raise
        try:
            exec(output)
        except:
            print("invalid effect (", effect,"), (", output,")")
            raise
    return True
    
#---------------------------------------------------
#                 test Functions                   -
#---------------------------------------------------

def testBlock( start, finish, path ):
    
    check = []
    
    #accepted paths (x, y, diag)
    if type( start ) != type( [] ) and type( start ) != type ( () ):
        start = getLocation(start)
    if type( finish ) != type( [] ) and type( finish ) != type ( () ):
        finish = getLocation(finish)
        
    if start == False or finish == False:
        return False
    
    def changeX( start ):
        new = copy.copy(start)
        if start[0] < finish[0]:
            n = 1
        else:
            n = -1
        for i in range(n, finish[0] - start[0] + n, n):
            new = (start[0] + i, start[1])
            check.append(new)
        return new
    
    def changeY( start ):
        new = copy.copy(start)
        if start[1] < finish[1]:
            n = 1
        else:
            n = -1
        for i in range(n, finish[1] - start[1] + n, n):
            new = (start[0], start[1] + i)
            check.append(new)
        return new
        
    if path == "x":
        recent = changeX( start )
        changeY( recent )
            
    elif path == "y":
        recent = changeY( start )
        changeX( recent )
        
    if path == "diag":
        recent = start
        i = 1
    
        if start[0] < finish[0]:
            if start[1] < finish[1]:
                #downright
                while recent[0] < finish[0] and recent[1] < finish[1]:
                    recent = (start[0] + i, start[1] + i)
                    check.append(recent) 
                    i +=1                
            else:
                #upright
                while recent[0] < finish[0] and recent[1] > finish[1]:
                    recent = (start[0] + i, start[1] - i)
                    check.append(recent) 
                    i +=1
        else:
            if start[1] < finish[1]:
                #downleft
                while recent[0] > finish[0] and recent[1] < finish[1]:
                    recent = (start[0] - i, start[1] + i)
                    check.append(recent) 
                    i +=1
            
            else:
                #upleft
                while recent[0] > finish[0] and recent[1] > finish[1]:
                    recent = (start[0] - i, start[1] - i)
                    check.append(recent) 
                    i +=1
        recent = changeX(recent)
        changeY(recent)
    if len(check) > 0:
        check.remove(check[-1])        
    for spot in check:
        if getMap(spot) != 'empty':
            return False
    return True

def testMove(caster, target, move):
    
    casterLocation = getLocation(caster)
    if type(target) == type([]) or type(target) == type( () ):
        targetLocation = target
        target = getMap(targetLocation)
    else:
        targetLocation = getLocation(target)
        
    #check requires to see if move can actually activate
    for require in getStat(move, REQUIRE):
        try:
            check = interpret(caster, target, move, require, casterLocation, targetLocation)
        except:
            print("Interpreter error:", require)
        try:
            if not eval(check):
                return require
        except:
            print ("invalid (", require, ") (", check, ")")
            raise
    return True
    
def testInterpret(string):
    value = interpret('caster', 'target', 'move', string, (0, 0), (1,1))
    print(value)
    return value


#---------------------------------------------------
#                 The Interpreter                  -
#---------------------------------------------------

def interpret(casterID, targetID, moveID, string, casterLocation, targetLocation):
    
    #targeting
    def CASTER(stringList, index):
        stringList[index] = "'" + casterID + "'" 
    
    def TARGET(stringList, index):
        stringList[index] = "'" + targetID + "'"
    
    def SELF(stringList, index):
        stringList[index] = "'" + moveID + "'"
    
    def CLASS(stringList, index):
        trgt = stringList[index - 1]
        trgt = trgt[1:len(trgt)-1]
        group_type = stringList[index + 1]
        
        if trgt != 'empty':
        
            #finds the group ID
            for group in getStat( trgt, GROUP ):
                if getStat(group, TYPE) == group_type:
                    print_group = getStat(group, ID)
                    break
            else:
                print (getStat( trgt, ID), "has no group", group_type)
                raise Exception("Interpret could not find Group")
        else:
            print_group = 'empty'            
        stringList[index + 1] = "'" + print_group  + "'"
        stringList[index] = stringList[index - 1] = ""
        
    def LOCATION(stringList, index):
        stringList[index] = "getMap("
        end = stringList.index(")")
        stringList[end] = ")"
        
        new = interpret(casterID, targetID, moveID, " ".join(stringList[index:end + 1]), casterLocation, targetLocation)+ ")"
        formula = eval(new)
        
        if formula == None:
            stringList[end] = "'empty'"
        else:
            stringList[end] = "'"+formula+"'"
        for i in range(index, end):
            stringList[i] = ''
    
    #controlMove
    def ACTIVATE(stringList, index):
        group_name = stringList[index + 1]
        item_list = getStat( casterID, EQUIP )
        for item in item_list:              
            flag = False
            for group in getStat( item, GROUP):
                if group == group_name:
                    flag = True
                    mve = item
                    break
            if flag == True:
                break
        else:
            mve = 'empty'
        chain(stringList, index, 'chain', mve)
    
    def CAST(stringList, index):
        chain(stringList, index, 'chain')
        
    def chain(stringList, index, command, mve=None):
        
        if mve == None:
            mve = stringList[index + 1 ]            
        
        trgt = stringList[index - 1 ]
        
        stringList[index] = "controlMove('"+ casterID +"', "+ trgt +", '"+ mve +"', '"+ command +"', "
        
        if 'DELAY' not in stringList:
            stringList.append("-1")
        
        stringList.append(")")
        stringList[index-1] = stringList[index + 1] = ""
        
    def DELAY(stringList, index):
        stringList.append(")")
        stringList[index] = "("
    
    #controlList
    
    def GETS(stringList, index):
        trgt = stringList[index -1]
        stat = stringList[index +1]
        
        stringList[index] = "controlList(" + trgt + ", '" + stat +"', " 
        stringList.append(", 'add')")
        
        stringList[index -1] = stringList[index +1] = ''
    
    def LOSES(stringList, index):
        trgt = stringList[index -1]
        stat = stringList[index +1]
        
        stringList[index] = "controlList(" + trgt + ", '" + stat +"', " 
        stringList.append(", 'remove')")
        
        stringList[index -1] = stringList[index +1] = ''
    
    #controlStat
    def CHANGE(stringList, index):
        trgt = stringList[index - 1]
        stat = stringList[index + 1]
        
        stringList[index] = "controlStat( "+ trgt +", '"+ stat +"', ("
        stringList.append("))")
        
        stringList[index - 1] = stringList[index + 1] = ""
        
    #controlString
    def REPLACE(stringList, index):
        trgt = stringList[index -1]
        stat = stringList[index +1]
        
        stringList[index] = "controlString( " + trgt + ", '" + stat + "', '"
        stringList.append("')")
        
        stringList[index +1] = stringList[index -1] = ''
    
    #control Recruit
    def RECRUIT(stringList, index):
        trgt = stringList[index - 1]
        
        stringList[index] = "controlRecruit(" + trgt +", "
        stringList.append(")")
        
        stringList[index-1] = '' 
        
    #control Travel
    def TRAVEL(stringList, index):
        stringList[index] = "controlTravel( '"+ casterID +"', targetLocation )"
        
    def MOVE(stringList, index):
        trgt = stringList[index -1]
        command = stringList[index +1]
        
        stringList[index] = "controlTravel("+ trgt +", ("
        stringList.append("), '" + command +"')")
        
        stringList[index -1] = stringList[index +1] = ""
        
    def BUMP(stringList, index):
        trgt = stringList[index -1]
        
        stringList[index] = "controlTravel( 'empty', getLocation("+ trgt +") )"
        
        stringList[index -1] = ''  
    
    #instant requires
    
    def BLOCK(stringList, index):
        command = stringList[index + 1]
        stringList[index] = "testBlock( casterLocation, targetLocation, '"+ command +"')"
        stringList[index + 1] = ""
    
    #numerical values
    def POSITION(stringList, index):
        if stringList[index -1] == "'"+casterID+"'":
            trgt = "casterLocation"
        elif stringList[index - 1] == "'"+targetID+"'":
            trgt = "targetLocation"
        
        if stringList[index + 1] == "x":
            command = "[0]"
        elif stringList[index + 1] == 'y':
            command = "[1]"
        else:
            command = ''
        
        stringList[index] = trgt+command
        stringList[index - 1] = ""
        if command != '':
            stringList[index + 1] = ''
    
    def DISTANCE(stringList, index):
        dtype = stringList[index + 1]
        stringList[index] = "getDistance('"+ casterID +"', targetLocation, '" + dtype + "')"
        stringList[index +1] = ""
        
    def DICE(stringList, index):
        stringList[index] = "random.randint(1,"
        end = stringList.index(")")
        stringList[end] = "))"
          
        
    keyword = {
        'MOVE': MOVE,
        'CASTER': CASTER,
        'TARGET': TARGET,
        'SELF': SELF,
        'CLASS': CLASS,
        'ACTIVATE': ACTIVATE,
        'GETS': GETS,
        'LOSES': LOSES,
        'CAST': CAST,
        'DELAY': DELAY,
        'CHANGE': CHANGE,
        'TRAVEL': TRAVEL,
        'BUMP': BUMP,
        'RECRUIT': RECRUIT,
        'BLOCK': BLOCK,
        'DISTANCE': DISTANCE,
        'POSITION': POSITION,
        'DICE': DICE,
        "REPLACE": REPLACE,
        "SELF": SELF,
        "LOCATION": LOCATION,
    }
    
    #parse the string
    stringList = re.split(" ", string)
    
    for index in range(len(stringList)):
        
        check = stringList[index]
        
        try:
            keyword[check](stringList, index)
            continue
        except KeyError:
            pass
        
        #Core Stats, Don't know how to move this to the functions yet
        if stringList[index] in OBJECT['ENV'][STATS] + OBJECT['ENV'][LISTS] + OBJECT['ENV'][STRINGS]:
            trgt = stringList[index - 1]
            stat = stringList[index]
            stringList[index] = "getStat(" + trgt + ", '" + stat + "')"
            stringList[index-1] = ""
            continue
        
        #wraps any remaining defined string in quotes    
        if stringList[index] in OBJECT.keys():
            stringList[index] = "'"+stringList[index]+"'"
            continue
    
    #prevents indentation errors
    while "" in stringList:
        stringList.remove("")
    
    return " ".join(stringList)
            
#---------------------------------------------------
#                  AI Functions                    -
#---------------------------------------------------
#a short AI script, it's a hack designed to help me test. Does not do anything
#general yet.
def randomAI(caster, target):
    
    moveList = getActiveMoves(caster)
    if len(moveList) > 0:
        mindex = random.randint(0, len(moveList)-1)
        controlMove( caster, target, moveList[mindex] )
        battleTick(0)
    else:
        print(getStat(caster, ID), "can't attack")
    return

