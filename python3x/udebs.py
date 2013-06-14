import re
import sys
import random 
import math 
import copy
from xml.etree import ElementTree

#---------------------------------------------------
#             predefined variables                 -
#---------------------------------------------------

#global dict
ID = "ID"                   #string
GROUP = "group"             #list

#Object
MOVELIST = "movelist"       #list chopping block (get active moves?)
TYPE = "type"               #string
INCREMENT = "INCREMENT"     #number
EFFECT = "effect"           #list
REQUIRE = "require"         #list

#ENV variables
STATS = "stats"             #list
LISTS = "lists"             #list
STRINGS = "strings"         #list
SLIST = 'slist'             #dict
RLIST = 'rlist'             #list
TICK = "tick"               #code I should move this to scripts

#var variables
UNITS = "units"             #list
TIME = "time"               #number
DELAY = "delay"             #list
MAP = "map"                 #list
REVERT = "revert"           #needs to be added
STATE = "state"
        
#---------------------------------------------------
#                 Main Class                       -
#---------------------------------------------------

class instance:
    
    def __init__(self, OBJECT={}, ENV={}, VAR={}, SCRIPTS={}, LOG=[]):
        self.object = OBJECT
        self.env = ENV
        self.var = VAR
        self.log = LOG
        self.scripts = SCRIPTS
    
    #---------------------------------------------------
    #                 Get Functions                    -
    #---------------------------------------------------
    
    def getActiveUnits(self):
        active = []
        for char in self.var[UNITS]:
            if len(self.getActiveMoves(char)) > 0:
                active.append(char)
        return active

    def getActiveMoves(self, unit):
        if type(unit) == type(()) or type(unit) == type([]):
            unit = self.getMap(unit)
        if unit == 'empty':
            return
        
        mlist = []
        for move in self.getStat(unit, MOVELIST):
            env = self.createTarget(unit, unit, move)
            flag = self.testRequire(env)
            if flag == True:
                mlist.append(move)
        return mlist

    def getStat(self, unit, stat):
        
        if type(unit) == type(()) or type(unit) == type([]):
            unit = self.getMap(unit)
        
        if stat in self.env[STRINGS]:
            return self.object[unit][stat]
        
        recursive_list = []
        classes = self.object[unit][GROUP] + [unit]
        for cls in classes:
            for lst in self.env[RLIST]:
                recursive_list.extend(self.object[cls][lst])
        
        if stat in self.env[STATS]:
            count = 0
            for cls in classes:    
                count +=self.object[cls][stat]
            for item in recursive_list:
                count +=self.getStat(item, stat)
            return count
            
        elif stat in self.env[LISTS]:    
            lst = []
            for cls in classes:
                lst.extend(self.object[cls][stat])       
            for item in recursive_list:
                lst.extend(self.getStat(item, stat))
            return lst
        else:
            raise Exception("Unknown Stat in GetStat")
            
    #returns combined stat for all elements in a list
    def getListStat(self, unit, lst, stat):
        if type(unit) == type(()) or type(unit) == type([]):
            unit = self.getMap(unit)
        
        start = self.getStat(unit, lst)
        
        found = []
        for element in start:
            item = self.getStat(element, stat)
            if type(item) == type([]):
                for entry in item:
                    found.append(entry)
            else:
                found.append(item)
        return found
        
    #returns first element in list contained in group    
    def getListGroup(self, unit, lst, group):
        if type(unit) in [type(()), type([])]:
            unit = self.getMap(unit)
        
        start = self.getStat(unit, lst)
        for item in start:
            if group in self.getStat(item, 'group'):
                return item
        return False
        
    def getMap(self, target="all"):
        temp_map = self.var[MAP]
        if target == "all":
            return temp_map        
        elif target == "y":
            return len(temp_map)
        elif target == "x":
            return len(temp_map[0])
        try:
            return temp_map[target[1]][target[0]]   
        except IndexError:
            return False
                   
    def getLocation(self, unit):
        if unit == "empty":
            return False
        if type(unit) in [type(()), type([])]:
            return unit
        y = 0
        for column in self.var[MAP]:
            try:
                x = column.index( unit )
                return [x, y]
            except ValueError:
                y +=1
                continue
        return False
        
    def getDistance(self, one, two, method):
        if type(one) == type (''):
            one = self.getLocation( one )
        if type(two) == type (''):
            two = self.getLocation( two )
        if one == False or two == False:
            return float("inf")
        elif method == 'y':
            return int( abs( one[1] - two[1] ) )
        elif method == 'x':
            return int( abs( one[0] - two[0] ) )
        elif method == "p1":
            return int(abs(one[0] - two[0]) + abs(one[1] - two[1]))
        elif method == "p2":
            return int(math.sqrt(math.pow(one[0] - two[0], 2) + math.pow(one[1] - two[1], 2)))
        elif method =="pinf":
            if abs(one[0] - two[0]) > abs(one[1] - two[1]):
                return int(abs(one[0] - two[0]))
            else:
                return int(abs(one[1] - two[1]))
        else:
            raise Exception("Unknown Command in getDistance")
    
    def getGroupType(self, unit, group_type, lst='group'):
        if type(unit) == type(()) or type(unit) == type([]):
            unit = self.getMap(unit)
        
        for item in self.getStat(unit, lst):              
            if self.getStat(item, TYPE) == group_type:
                print_group = item
                break
        else:
            self.controlLog(unit, "has no group", group_type)
            print_group = "empty"
        return print_group
        
    def getGroup(self, group):
        return_list = []
        for unit in self.var[UNITS]:
            if group in self.getStat(unit, GROUP):
                return_list.append(unit)
        return return_list
        
    def getLog(self):
        test = copy.deepcopy(self.log)
        self.controlLog(clear=True)
        return test
    
    #---------------------------------------------------
    #                Export Functions                  -
    #---------------------------------------------------
    
    #neither of the import functions are being activly maintained. I don't need them anymore.
    
    def export(self, *item):
        ENV = copy.deepcopy(self.env)
        
        def find(unit, found, test=False):
            for lst in ENV[LISTS]:
                for obj in self.object[unit][lst]:
                    try:
                        if obj not in found:
                            found.append(obj)
                            found = find(obj, found)
                    except KeyError:
                        continue
            return found
        
        found = list(item)
        for obj in item:
            found = find(obj, found)
        
        #add all of these elements into export object
        OBJECT = {}
        for entity in found:
            try:
                OBJECT[entity] = copy.deepcopy(self.object[entity])
            except KeyError:
                continue
        return instance(OBJECT, ENV)
        
    def inport(self, inst):
        if self.env == inst.env:
            #bug! inport fails if lists not same order.
            self.object.update(inst.object)
            return True
        else:
            print("import failed. Instances are not compatible.")
            return False
        

    #---------------------------------------------------
    #               Control Functions                  -
    #---------------------------------------------------
    
    #change so controlTime is pulling from scripts
    def controlTime(self, time=1):   
        if type(time) != type(int()):
            raise Exception("controlTime Error: Only accepts int as argument")
        
        if time != 0:
            self.var[TIME] +=time
            self.controlLog('Env time', "changed by", time, "is now", self.var[TIME])
            for unit in self.var[UNITS]:
                env = self.createTarget("empty", unit, "empty", ("time", time))
                exec(self.env[TICK], env)
            for delay in self.var[DELAY]:
                delay["DELAY"] -=time    
    
        while True:
            check = 0
            for delay in copy.deepcopy(self.var[DELAY]):
                if delay["DELAY"] <= 0:
                    check +=1
                    self.controlMove(delay["CASTER"], delay["TARGET"], 
                                     delay["MOVE"], -1, delay['MULTI'])
                    self.var[DELAY].remove(delay)
            if check == 0:
                self.controlLog()
                break
    
#        if time != 0:
#            #Broken, make sure STATE isn't longer then revert.
#            #while len(STATE) >= self.env["REVERT"]:
#            #    STATE.pop(0)
#            self.state.append(copy.deepcopy(self.object))
        return True

    #revert is completely broken
    def controlRevert(self, state=1):
        if type(state) != type(int()) or state <= 0:
            raise Exception("controlRevert only accepts int > 0 as argument")
        if len(self.state) < state:
            self.controlLog("Revert failed. Choosen state not available.")
            return
    
        index = len(self.state) - state
        self.object.update(copy.deepcopy(self.state[index]))
        for count in range(index+1, index):
            del self.state[count]
        self.controlLog("revert successful")
        return
    
    def controlLog(self, *args, clear=False):
        if clear:
            self.log = []
            return True
        log = ""
        for text in args:
            log = log + " " + str(text)
        log = log[1:]
        self.log.append(log)
        print(log)
        return True

    def controlStat(self, target, stat, increment ):
        increment = int(increment)
        
        if type(target) == type(()) or type(target) == type([]):
            target = self.getMap(target)
        if target == 'empty':
            return False
        if increment == 0:
            return True
        
        newValue = self.object[target][stat] + increment
        self.object[target][stat] = newValue
        self.controlLog(target, stat, "changed by", increment, "is now", self.getStat(target, stat))
        return True

    def controlString(self, target, desc, new):
        if type(target) == type(()) or type(target) == type([]):
            target = self.getMap(target)
        if target == 'empty':
            return False
        if desc == "ID":
            self.controlLog("String update failed, ID cannot be changed.")
            return False
            
        self.object[target][desc] = new
        self.controlLog(target, desc, "is now", new)
        return True
        
    def controlList(self, target, lst, entry, command='add'):
        if type(target) == type(()) or type(target) == type([]):
            target = self.getMap(target)
        if target == 'empty' or entry == 'empty':
            return False
        
        current = self.object[target][lst]
        
        if command == 'remove':
            if entry in current:
                current.remove(entry)
                self.controlLog(entry, "removed from", target, lst)
            return True
        
        elif command == 'add':
            if lst in self.env[SLIST].keys():
                if self.env[SLIST][lst] in self.getStat(entry, "group"):
                    env = self.createTarget(target, target, entry)
                    check = self.testRequire(env)
                    if check != True:  
                        self.controlLog(target, "special list", lst, entry, 
                                        "failed because", check)
                        return False
                else:
                    self.controlLog(target, "special list", lst, entry, 
                                    "failed because invalid type")
                    return False

            current.append(entry)
            self.controlLog(entry, "added to", target, lst)
            return True
        
    def controlRecruit(self, clone, position=None):
        if type(clone) == type(()):
            clone = self.getMap(clone)
        if clone == 'empty':
            self.controlLog("Warning tried to clone empty.")
            return False
        try:
            new_unit = copy.deepcopy(self.object[clone])
        except KeyError:
            self.controlLog("recruit failed, unit to clone not found")
            return False
        
        increment = self.object[clone][INCREMENT] + 1
        self.object[clone][INCREMENT] = increment
        new_unit[ID] = clone + str(increment)
        
        self.object[new_unit[ID]] = new_unit
        self.var[UNITS].append(new_unit[ID])
        
        self.controlLog(new_unit[ID], "has been recruited")       
        if position is not None:
            self.controlTravel(new_unit[ID], position)
        
        env = self.createTarget("empty", new_unit[ID], "empty")
        self.controlScript('recruit', new_unit[ID])
        
        return True
            
    def controlTravel(self, caster, targetLoc, command='travel'):    
        
        if type(caster) == type(()) or type(caster) == type([]):
            casterLoc = list(caster)
            caster = self.getMap(caster)
        else:
            casterLoc = self.getLocation(caster)
        
        if command != 'travel':
            tempLoc = copy.copy(casterLoc)
            if command == 'x':
                tempLoc[0] +=targetLoc
            elif command == 'y':
                tempLoc[1] +=targetLoc
            elif command =='xy':
                tempLoc[0] +=targetLoc[0]
                tempLoc[1] +=targetLoc[1]
            targetLoc = tempLoc
        target = self.getMap(targetLoc)
        
        if not target or targetLoc[0] < 0 or targetLoc[1] < 0:
            self.controlLog("Warning", caster, "trying to move off the stage.")
            return False
        
        if casterLoc:
            self.var[MAP][casterLoc[1]][casterLoc[0]] = 'empty'
        self.var[MAP][targetLoc[1]][targetLoc[0]] = caster
        
        if caster != 'empty':
            self.controlLog(caster, "has moved to", targetLoc)
        if target != 'empty' and target != caster:
            self.controlLog(target, "has been bumped")
        return True
         
    def controlMove(self, caster, target , move, delay=-1, multi=False):             
     
        delay = int(delay)
        if delay >= 0:
            new_delay = {
                "DELAY": delay,  
                "CASTER": caster, 
                "TARGET": target, 
                "MOVE": move,
                "MULTI": multi,
            }
            self.controlLog('cast', move, "added to delay for", delay)
            self.var[DELAY].append(new_delay)
            return True
            
        if multi:
            for entry in target:
                self.controlMove(caster, entry, move, delay)
            return True
        
        env = self.createTarget(caster, target, move)
        check = self.testRequire(env)
        if check != True:
            self.controlLog(env["casterID"], "cast", env["moveID"], "failed because", check)
            return False
        
        self.controlLog(env["casterID"], "uses", env["moveID"], "on", env["targetID"])
        self.controlEffect(env)
        return True
        
    def controlEffect(self, env):
        for effect in self.getStat(env["moveID"], EFFECT):
            output = interpret(effect, self)        
            try:
                exec(output, env)
            except:
                print("invalid (", effect,") interpreted as (", output, ")")
                raise
            
        return True
        
    def controlScript(self, script="init", target='empty'):
        env = self.createTarget("empty", target, "empty")
        try:
            init = self.scripts[script]            
        except KeyError:
            return False
        
        for effect in init:
            output = interpret(effect, self)
            try:
                exec(output, env)
            except:
                print("invalid (", effect,") interpreted as (", output, ")")
                raise
        return True

    #---------------------------------------------------
    #                 Test Functions                   -
    #---------------------------------------------------

    def testBlock(self, start, finish, path ):
        check = []
        
        #accepted paths (x, y, diag)
        if type( start ) != type( [] ) and type( start ) != type ( () ):
            start = self.getLocation(start)
        if type( finish ) != type( [] ) and type( finish ) != type ( () ):
            finish = self.getLocation(finish)
            
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
            if self.getMap(spot) != 'empty':
                return False
        return True

    def testRequire(self, env0):
        env = copy.copy(env0)
        
        env['target'] = env['targetID']
        
        for require in self.getStat(env["moveID"], REQUIRE):
            check = interpret(require, self)
            try:
                if not eval(check, env):
                    return require
            except:
                print ("invalid (", require, ") interpreted as (", check, ")")
                raise
        return True
    
    def createTarget(self, caster, target, move, *args):
        if type(caster) == type(()) or type(caster) == type([]):
            casterID = self.getMap(caster)
            casterLocation = list(caster)
        else:
            casterID = caster
            casterLocation = self.getLocation(caster)
        
        if type(target) == type(()) or type(target) == type([]):
            targetID = self.getMap(target)
            targetLocation = list(target)
        else:
            targetID = target
            targetLocation = self.getLocation(target)
        
        targetting = {
            "target": target,
            "casterID": casterID,
            "targetID": targetID,
            "targetLocation": targetLocation,
            "casterLocation": casterLocation,
            "self": self,
            "random": random,
            "moveID": move,
        }
        
        for arg in args:
            targetting[arg[0]] = arg[1]
         
        return targetting
        
#---------------------------------------------------
#                      XML parser                  -
#---------------------------------------------------

#Creates and instance object from xml file.
def battleStart(xml_file, init=True):
    
    try:
        tree = ElementTree.parse(xml_file)
    except IOError as inst:
        print( "battleStart Error:", inst)
        sys.exit()
    
    #set vars
    OBJECT = {}
    VAR = {
        TIME: 0,
        DELAY: [],
        TICK: [],
        UNITS: [],
        MAP: [],
        STATE: [],
    }
    ENV = {
        STATS: [],
        LISTS: [MOVELIST, GROUP, EFFECT, REQUIRE],
        STRINGS: [TYPE, ID],
        RLIST: [],
        SLIST: {},
        TICK: "",
    }
    LOG = []
    SCRIPTS = {}
      
    root = tree.getroot()
    
    #printout
    out = root.find("name")
    if out is not None:
        print("INITIALIZING", out.text, "\n")
    
    #definitions
    defs = root.find("definitions")
        
    def_stats = defs.find("stats")
    if def_stats is not None:
        for stat in def_stats:
            ENV[STATS].append(stat.text)
            
    def_lists = defs.find("lists")
    if def_lists is not None:
        for stat in def_lists:
            ENV[LISTS].append(stat.text)
            if stat.get('rlist') == "rlist":
                ENV[RLIST].append(stat.text)
            if stat.get('slist') is not None:
                ENV[SLIST][stat.text] = stat.get('slist')
                
                       
    def_strings = defs.find("strings")
    if def_strings is not None:
        for stat in def_strings:
            ENV[STRINGS].append(stat.text)
    
    #map
    field_map = root.find("map")
    if field_map is not None:
        dim_map = field_map.find("dim")
        if dim_map is not None:
            x = int(dim_map.find('x').text)
            y = int(dim_map.find('y').text)
            VAR[MAP] = []
            for element in range(y):
                VAR[MAP].append(['empty' for i in range(x)])
                
        else:
            for row in field_map:
                VAR[MAP].append(re.split("\W*,\W*", row.text))
    
    #scripts
    script = root.find("scripts")
    if script is not None:
        for entry in script:
            effects = []
            for item in entry:
                effects.append(item.text)
            SCRIPTS[entry.tag] = effects             
            
#    config = root.find("config")
#    if config is not None:
#        revert = config.findtext("revert")
#        if revert is not None:
#            VAR["REVERT"] = int(revert)
#        else:
#            VAR["REVERT"] = 0
#    else:
#        VAR["REVERT"] = 0
    
    #Set empty
    empty = {}
    for stat in ENV[STATS]:
        empty[stat] = 0
    for lists in ENV[LISTS]:
        empty[lists] = []
    for string in ENV[STRINGS]:
        empty[string] = ''
    empty[ID] = 'empty'
    
    OBJECT['empty'] = empty
    
    #Create all entity type objects.
    entities = root.find("entities")
    if entities is not None:
        for item in entities:
            new_entity = {
                REQUIRE: [],
                EFFECT: [],
                INCREMENT: 0,
            }
            
            iden = item.findtext("ID")
            if iden is not None:
                new_entity[ID] = iden
            
            require = item.find("require")
            if require is not None:
                for item2 in require:
                    new_entity[REQUIRE].append(item2.text)
    
            effect = item.find("effect")
            if effect is not None:
                for item2 in effect:
                    new_entity[EFFECT].append(item2.text)
            
            for stat in ENV[STATS]:
                new_entity[stat] = 0
            stats = item.find("stats")
            if stats is not None:
                for stat in stats:
                    new_entity[stat.tag] = int(stat.text)
                    
            for strings in ENV[STRINGS]:
                value = item.findtext(strings)
                if value is not None:
                    new_entity[strings] = value
                else:
                    new_entity[strings] = ""
            
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
            new_unit = {
                INCREMENT: 0,
                REQUIRE: [],
                EFFECT: [],
            }
            
            iden = item.findtext("ID")
            if iden is not None:
                new_unit[ID] = iden
            
            for stat in ENV[STATS]:
                new_unit[stat] = 0
            stats = item.find("stats")
            if stats is not None:
                for stat in stats:
                    new_unit[stat.tag] = int(stat.text)
                    
            for strings in ENV[STRINGS]:
                value = item.findtext(strings)
                if value is not None:
                    new_unit[strings] = value
                else:
                    new_unit[strings] = ""
            
            for lst in ENV[LISTS]:
                new_unit[lst] = []
                find_list = item.find(lst)
                if find_list is not None:
                    for value in find_list:
                        new_unit[lst].append(value.text)
                
            OBJECT[new_unit[ID]] = new_unit
            
            #Sets ENV variables for units.
            VAR[UNITS].append(new_unit[ID])
            if item.get("tick") == "tick":
                VAR[TICK].append(new_unit[ID])
            elif item.get("tick") == "clone":
                VAR[CTICK].append(new_unit[ID])
    
    VAR[STATE].append(copy.deepcopy(OBJECT))
    field = instance(OBJECT, ENV, VAR, SCRIPTS, LOG)
    
    try:
        def_tick = field.scripts["tick"][0]
        def_tick = interpret(def_tick, field)
        def_tick = compile(def_tick, '<string>', "exec")
    except KeyError:
        print("warning, no tick is defined.")
        def_tick = ""
    field.env[TICK] = def_tick
    
    return field
     
#---------------------------------------------------
#                  Interpreter                     -
#---------------------------------------------------

def interpret(string, env=False, debug=False):
    if string == None:
        return ''
    
    def isdef(value):
        if env:
            if value in env.object.keys():
                return "'"+value+"'"
        return value
    
    #targeting
    def CLASS(stringList, index):
        trgt = stringList[index - 1]
        group_type = stringList[index + 1]
        stringList[index + 1] = "self.getGroupType(" + isdef(trgt)  + ", '" + group_type + "', 'group')"
        stringList[index] = stringList[index - 1] = ""
        
    def SUB(stringList, index):
        #Do this better.
        stat = stringList[index +1]
        stringList[index] = ".__getitem__("+stat+")"
        stringList[index +1] = ""
    
    #controlMove
    def ACTIVATE(stringList, index):
        trgt = stringList[index - 1]
        group_name = stringList[index + 1]
        mve = "self.getGroupType( casterID, '" + group_name + "', 'equip')"
        chain(stringList, index, mve)
    
    def ALL(stringList, index):
        #WARNING!! All is designed to be used only with move.
        #Nothing else accepts multi targets yet.
        group = stringList[index +1]
        stringList[index +1] = 'self.getGroup("' + group + '")'
        stringList[index] = ''
        
        chain(stringList, index + 2, multi=True)       
    
    def CAST(stringList, index):
        chain(stringList, index)
        
    def chain(stringList, index, mve=None, multi=False):
        if mve == None:
            mve = stringList[index + 1 ]
        trgt = stringList[index - 1 ]
        stringList[index] = "self.controlMove(casterID, "+ isdef(trgt) +", "+ isdef(mve) +", "
        
        if 'DELAY' not in stringList:
            stringList.append("-1")
        else:
            stringList[stringList.index('DELAY')] = ''
        stringList.append(', '+ str(multi) + ")")
        stringList[index-1] = stringList[index + 1] = ""
        
    #controlList
    def GETS(stringList, index):
        trgt = stringList[index -1]
        stat = stringList[index +1]
        string = stringList[index +2]
        stringList[index] = "self.controlList("+isdef(trgt)+", '"+stat+"', "+isdef(string)+", 'add')" 
        stringList[index -1] = stringList[index +1] = stringList[index +2] = ''
    
    def LOSES(stringList, index):
        trgt = stringList[index -1]
        stat = stringList[index +1]
        string = stringList[index +2]
        stringList[index] = "self.controlList("+isdef(trgt)+", '"+stat+"', "+isdef(string)+", 'remove')"
        stringList[index -1] = stringList[index +1] = stringList[index +2] = ''
    
    #controlStat
    def CHANGE(stringList, index):
        trgt = stringList[index - 1]
        stat = stringList[index + 1]
        amount = stringList[index + 2]
        stringList[index] = "self.controlStat( "+isdef(trgt)+", '"+ stat +"', "+amount+")"
        stringList[index - 1] = stringList[index + 1] = stringList[index +2] = ""
        
    #controlString
    def REPLACE(stringList, index):
        trgt = stringList[index -1]
        stat = stringList[index +1]
        change = stringList[index +2]
        stringList[index] = "self.controlString(" + isdef(trgt) + ", '" + stat + "', '" + change + "')"
        stringList[index +1] = stringList[index -1] = stringList[index +2] = ''
    
    #control Recruit
    def RECRUIT(stringList, index):
        trgt = stringList[index - 1]
        loc = stringList[index + 1]
        stringList[index] = "self.controlRecruit(" + isdef(trgt) +", "+loc+")"
        stringList[index-1] = stringList[index +1] = '' 
        
    #control Travel
    def TRAVEL(stringList, index):
        stringList[index] = "self.controlTravel( casterID, targetLocation )"
        
    def MOVE(stringList, index):
        trgt = stringList[index -1]
        loc = stringList[index +2]
        command = stringList[index +1]
        stringList[index] = "self.controlTravel("+ isdef(trgt) +", "+ loc + ", '" + command +"')"
        stringList[index -1] = stringList[index +1] = stringList[index +2] = ""
        
    def BUMP(stringList, index):
        trgt = stringList[index -1]
        stringList[index] = "self.controlTravel( 'empty', self.getLocation("+ isdef(trgt) +") )"
        stringList[index -1] = ''
    
    #instant requires
    def BLOCK(stringList, index):
        command = stringList[index + 1]
        stringList[index] = "self.testBlock( casterLocation, targetLocation, '"+ command +"')"
        stringList[index + 1] = ""
        
    def ONBOARD(stringList, index):
        stringList[index] = "self.getLocation(targetID)"
    
    #numerical values
    def POSITION(stringList, index):
        if stringList[index -1] == "casterID":
            trgt = "casterLocation"
        elif stringList[index - 1] in ["targetID", 'target']:
            trgt = "targetLocation"
        
        if stringList[index + 1] == "x":
            command = "0"
        elif stringList[index + 1] == 'y':
            command = "1"
        else:
            command = ''
        stringList[index] = trgt+'.__getitem__('+ command +')'
        stringList[index - 1] = ""
        if command != '':
            stringList[index + 1] = ''
    
    def DISTANCE(stringList, index):
        dtype = stringList[index + 1]
        stringList[index] = "self.getDistance(casterID, targetLocation, '" + dtype + "')"
        stringList[index +1] = ""
        
    def DICE(stringList, index):
        value = stringList[index +1]
        stringList[index] = "random.randint(1," + value + ")"
        stringList[index +1] = ""
    
    #getStat
    def STAT(stringList, index):
        trgt = stringList[index - 1]
        stat = stringList[index + 1]
        stringList[index] = "self.getStat(" + isdef(trgt) + ", '" + stat + "')"
        stringList[index-1] = stringList[index +1] = ""
    
    def LISTSTAT(stringList, index):
        trgt = stringList[index - 1]
        lst = stringList[index + 1]
        stat = stringList[index + 2]
        stringList[index] = "self.getListStat(" + isdef(trgt) + ", '" + lst + "', '" + stat + "')"
        stringList[index-1] = stringList[index +1] = stringList[index + 2] = ""
        
    keyword = {
        'ONBOARD': ONBOARD,
        'ALL': ALL,
        'LISTSTAT': LISTSTAT,
        'STAT': STAT,
        'S': STAT,
        'MOVE': MOVE,
        'CLASS': CLASS,
        'ACTIVATE': ACTIVATE,
        'GETS': GETS,
        'LOSES': LOSES,
        'CAST': CAST,
        'CHANGE': CHANGE,
        'TRAVEL': TRAVEL,
        'BUMP': BUMP,
        'RECRUIT': RECRUIT,
        'BLOCK': BLOCK,
        'DISTANCE': DISTANCE,
        'POSITION': POSITION,
        'DICE': DICE,
        "REPLACE": REPLACE,
        "SUB": SUB,
    }
    
    if debug:
        print(string)
    
    #Deal with Square brackets
    while "[" in string:
        start = string.find("[")
        end = string.find("]")
        substr = string[start:end + 1]
        while substr.count("[") != substr.count("]"):
            end = string[end +1:].find("]") + end+1 
            substr = string[start:end+1]
        
        formula = string[start+1:end]
        if debug:
            print("entering subshell")
        formula = interpret(formula, env, debug)
        if debug:
            print("exiting subshell")
        formula = "("+formula+")"
        formula = formula.replace(" ", "")
        string = string[:start] + formula + string[end+1:]
        
    #parse remaining strings.
    stringList = re.split(" ", string)
    
    #quotize
    for index in range(len(stringList)):
        if stringList[index] in ["CASTER", "C"]:
            stringList[index] = "casterID"
        elif stringList[index] in ["TARGET", "T"]:
            stringList[index] = "target"
        elif stringList[index] == "SELF":
            stringList[index] = "moveID"
    
    #compute remaining values
    for index in range(len(stringList)):
        if debug:
            print(stringList)
        check = stringList[index]
        try:
            keyword[check](stringList, index)
            continue
        except KeyError:
            pass
        if env:
            if stringList[index] in env.object.keys():
                stringList[index] = "'"+stringList[index]+"'"
                continue

    #prevents indentation errors
    while "" in stringList:
        stringList.remove("")
    return " ".join(stringList)

