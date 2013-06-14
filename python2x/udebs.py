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
ID = u"ID"                   #string
GROUP = u"group"             #list

#Object
MOVELIST = u"movelist"       #list chopping block (get active moves?)
TYPE = u"type"               #string
INCREMENT = u"INCREMENT"     #number
EFFECT = u"effect"           #list
REQUIRE = u"require"         #list

#ENV variables
STATS = u"stats"             #list
LISTS = u"lists"             #list
STRINGS = u"strings"         #list
SLIST = u'slist'             #dict
RLIST = u'rlist'             #list
TICK = u"tick"               #code I should move this to scripts

#var variables
UNITS = u"units"             #list
TIME = u"time"               #number
DELAY = u"delay"             #list
MAP = u"map"                 #list
REVERT = u"revert"           #needs to be added
STATE = u"state"
        
#---------------------------------------------------
#                 Main Class                       -
#---------------------------------------------------

class instance(object):
    
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
        if unit == u'empty':
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
            raise Exception(u"Unknown Stat in GetStat")
            
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
            if group in self.getStat(item, u'group'):
                return item
        return False
        
    def getMap(self, target=u"all"):
        temp_map = self.var[MAP]
        if target == u"all":
            return temp_map        
        elif target == u"y":
            return len(temp_map)
        elif target == u"x":
            return len(temp_map[0])
        try:
            return temp_map[target[1]][target[0]]   
        except IndexError:
            return False
                   
    def getLocation(self, unit):
        if unit == u"empty":
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
        if type(one) == type (u''):
            one = self.getLocation( one )
        if type(two) == type (u''):
            two = self.getLocation( two )
        if one == False or two == False:
            return float(u"inf")
        elif method == u'y':
            return int( abs( one[1] - two[1] ) )
        elif method == u'x':
            return int( abs( one[0] - two[0] ) )
        elif method == u"p1":
            return int(abs(one[0] - two[0]) + abs(one[1] - two[1]))
        elif method == u"p2":
            return int(math.sqrt(math.pow(one[0] - two[0], 2) + math.pow(one[1] - two[1], 2)))
        elif method ==u"pinf":
            if abs(one[0] - two[0]) > abs(one[1] - two[1]):
                return int(abs(one[0] - two[0]))
            else:
                return int(abs(one[1] - two[1]))
        else:
            raise Exception(u"Unknown Command in getDistance")
    
    def getGroupType(self, unit, group_type, lst=u'group'):
        if type(unit) == type(()) or type(unit) == type([]):
            unit = self.getMap(unit)
        
        for item in self.getStat(unit, lst):              
            if self.getStat(item, TYPE) == group_type:
                print_group = item
                break
        else:
            self.controlLog(unit, u"has no group", group_type)
            print_group = u"empty"
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
            print u"import failed. Instances are not compatible."
            return False
        

    #---------------------------------------------------
    #               Control Functions                  -
    #---------------------------------------------------
    
    #change so controlTime is pulling from scripts
    def controlTime(self, time=1):   
        if type(time) != type(int()):
            raise Exception(u"controlTime Error: Only accepts int as argument")
        
        if time != 0:
            self.var[TIME] +=time
            self.controlLog(u'Env time', u"changed by", time, u"is now", self.var[TIME])
            for unit in self.var[UNITS]:
                env = self.createTarget(u"empty", unit, u"empty", (u"time", time))
                exec(self.env[TICK], env)
            for delay in self.var[DELAY]:
                delay[u"DELAY"] -=time    
    
        while True:
            check = 0
            for delay in copy.deepcopy(self.var[DELAY]):
                if delay[u"DELAY"] <= 0:
                    check +=1
                    self.controlMove(delay[u"CASTER"], delay[u"TARGET"], 
                                     delay[u"MOVE"], -1, delay[u'MULTI'])
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
            raise Exception(u"controlRevert only accepts int > 0 as argument")
        if len(self.state) < state:
            self.controlLog(u"Revert failed. Choosen state not available.")
            return
    
        index = len(self.state) - state
        self.object.update(copy.deepcopy(self.state[index]))
        for count in xrange(index+1, index):
            del self.state[count]
        self.controlLog(u"revert successful")
        return
    
    def controlLog(self, *args, **_3to2kwargs):
        if 'clear' in _3to2kwargs: clear = _3to2kwargs['clear']; del _3to2kwargs['clear']
        else: clear = False
        if clear:
            self.log = []
            return True
        log = u""
        for text in args:
            log = log + u" " + unicode(text)
        log = log[1:]
        self.log.append(log)
        print log
        return True

    def controlStat(self, target, stat, increment ):
        increment = int(increment)
        
        if type(target) == type(()) or type(target) == type([]):
            target = self.getMap(target)
        if target == u'empty':
            return False
        if increment == 0:
            return True
        
        newValue = self.object[target][stat] + increment
        self.object[target][stat] = newValue
        self.controlLog(target, stat, u"changed by", increment, u"is now", self.getStat(target, stat))
        return True

    def controlString(self, target, desc, new):
        if type(target) == type(()) or type(target) == type([]):
            target = self.getMap(target)
        if target == u'empty':
            return False
        if desc == u"ID":
            self.controlLog(u"String update failed, ID cannot be changed.")
            return False
            
        self.object[target][desc] = new
        self.controlLog(target, desc, u"is now", new)
        return True
        
    def controlList(self, target, lst, entry, command=u'add'):
        if type(target) == type(()) or type(target) == type([]):
            target = self.getMap(target)
        if target == u'empty' or entry == u'empty':
            return False
        
        current = self.object[target][lst]
        
        if command == u'remove':
            if entry in current:
                current.remove(entry)
                self.controlLog(entry, u"removed from", target, lst)
            return True
        
        elif command == u'add':
            if lst in self.env[SLIST].keys():
                if self.env[SLIST][lst] in self.getStat(entry, u"group"):
                    env = self.createTarget(target, target, entry)
                    check = self.testRequire(env)
                    if check != True:  
                        self.controlLog(target, u"special list", lst, entry, 
                                        u"failed because", check)
                        return False
                else:
                    self.controlLog(target, u"special list", lst, entry, 
                                    u"failed because invalid type")
                    return False

            current.append(entry)
            self.controlLog(entry, u"added to", target, lst)
            return True
        
    def controlRecruit(self, clone, position=None):
        if type(clone) == type(()):
            clone = self.getMap(clone)
        if clone == u'empty':
            self.controlLog(u"Warning tried to clone empty.")
            return False
        try:
            new_unit = copy.deepcopy(self.object[clone])
        except KeyError:
            self.controlLog(u"recruit failed, unit to clone not found")
            return False
        
        increment = self.object[clone][INCREMENT] + 1
        self.object[clone][INCREMENT] = increment
        new_unit[ID] = clone + unicode(increment)
        
        self.object[new_unit[ID]] = new_unit
        self.var[UNITS].append(new_unit[ID])
        
        self.controlLog(new_unit[ID], u"has been recruited")       
        if position is not None:
            self.controlTravel(new_unit[ID], position)
        
        env = self.createTarget(u"empty", new_unit[ID], u"empty")
        self.controlScript(u'recruit', new_unit[ID])
        
        return True
            
    def controlTravel(self, caster, targetLoc, command=u'travel'):    
        
        if type(caster) == type(()) or type(caster) == type([]):
            casterLoc = list(caster)
            caster = self.getMap(caster)
        else:
            casterLoc = self.getLocation(caster)
        
        if command != u'travel':
            tempLoc = copy.copy(casterLoc)
            if command == u'x':
                tempLoc[0] +=targetLoc
            elif command == u'y':
                tempLoc[1] +=targetLoc
            elif command ==u'xy':
                tempLoc[0] +=targetLoc[0]
                tempLoc[1] +=targetLoc[1]
            targetLoc = tempLoc
        target = self.getMap(targetLoc)
        
        if not target or targetLoc[0] < 0 or targetLoc[1] < 0:
            self.controlLog(u"Warning", caster, u"trying to move off the stage.")
            return False
        
        if casterLoc:
            self.var[MAP][casterLoc[1]][casterLoc[0]] = u'empty'
        self.var[MAP][targetLoc[1]][targetLoc[0]] = caster
        
        if caster != u'empty':
            self.controlLog(caster, u"has moved to", targetLoc)
        if target != u'empty' and target != caster:
            self.controlLog(target, u"has been bumped")
        return True
         
    def controlMove(self, caster, target , move, delay=-1, multi=False):             
     
        delay = int(delay)
        if delay >= 0:
            new_delay = {
                u"DELAY": delay,  
                u"CASTER": caster, 
                u"TARGET": target, 
                u"MOVE": move,
                u"MULTI": multi,
            }
            self.controlLog(u'cast', move, u"added to delay for", delay)
            self.var[DELAY].append(new_delay)
            return True
            
        if multi:
            for entry in target:
                self.controlMove(caster, entry, move, delay)
            return True
        
        env = self.createTarget(caster, target, move)
        check = self.testRequire(env)
        if check != True:
            self.controlLog(env[u"casterID"], u"cast", env[u"moveID"], u"failed because", check)
            return False
        
        self.controlLog(env[u"casterID"], u"uses", env[u"moveID"], u"on", env[u"targetID"])
        self.controlEffect(env)
        return True
        
    def controlEffect(self, env):
        for effect in self.getStat(env[u"moveID"], EFFECT):
            output = interpret(effect, self)        
            try:
                exec(output, env)
            except:
                print u"invalid (", effect,u") interpreted as (", output, u")"
                raise
            
        return True
        
    def controlScript(self, script=u"init", target=u'empty'):
        env = self.createTarget(u"empty", target, u"empty")
        try:
            init = self.scripts[script]            
        except KeyError:
            return False
        
        for effect in init:
            output = interpret(effect, self)
            try:
                exec(output, env)
            except:
                print u"invalid (", effect,u") interpreted as (", output, u")"
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
            for i in xrange(n, finish[0] - start[0] + n, n):
                new = (start[0] + i, start[1])
                check.append(new)
            return new
        
        def changeY( start ):
            new = copy.copy(start)
            if start[1] < finish[1]:
                n = 1
            else:
                n = -1
            for i in xrange(n, finish[1] - start[1] + n, n):
                new = (start[0], start[1] + i)
                check.append(new)
            return new
            
        if path == u"x":
            recent = changeX( start )
            changeY( recent )
                
        elif path == u"y":
            recent = changeY( start )
            changeX( recent )
            
        if path == u"diag":
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
            if self.getMap(spot) != u'empty':
                return False
        return True

    def testRequire(self, env0):
        env = copy.copy(env0)
        
        env[u'target'] = env[u'targetID']
        
        for require in self.getStat(env[u"moveID"], REQUIRE):
            check = interpret(require, self)
            try:
                if not eval(check, env):
                    return require
            except:
                print u"invalid (", require, u") interpreted as (", check, u")"
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
            u"target": target,
            u"casterID": casterID,
            u"targetID": targetID,
            u"targetLocation": targetLocation,
            u"casterLocation": casterLocation,
            u"self": self,
            u"random": random,
            u"moveID": move,
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
    except IOError, inst:
        print u"battleStart Error:", inst
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
        TICK: u"",
    }
    LOG = []
    SCRIPTS = {}
      
    root = tree.getroot()
    
    #printout
    out = root.find(u"name")
    if out is not None:
        print u"INITIALIZING", out.text, u"\n"
    
    #definitions
    defs = root.find(u"definitions")
        
    def_stats = defs.find(u"stats")
    if def_stats is not None:
        for stat in def_stats:
            ENV[STATS].append(stat.text)
            
    def_lists = defs.find(u"lists")
    if def_lists is not None:
        for stat in def_lists:
            ENV[LISTS].append(stat.text)
            if stat.get(u'rlist') == u"rlist":
                ENV[RLIST].append(stat.text)
            if stat.get(u'slist') is not None:
                ENV[SLIST][stat.text] = stat.get(u'slist')
                
                       
    def_strings = defs.find(u"strings")
    if def_strings is not None:
        for stat in def_strings:
            ENV[STRINGS].append(stat.text)
    
    #map
    field_map = root.find(u"map")
    if field_map is not None:
        dim_map = field_map.find(u"dim")
        if dim_map is not None:
            x = int(dim_map.find(u'x').text)
            y = int(dim_map.find(u'y').text)
            VAR[MAP] = []
            for element in xrange(y):
                VAR[MAP].append([u'empty' for i in xrange(x)])
                
        else:
            for row in field_map:
                VAR[MAP].append(re.split(u"\W*,\W*", row.text))
    
    #scripts
    script = root.find(u"scripts")
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
        empty[string] = u''
    empty[ID] = u'empty'
    
    OBJECT[u'empty'] = empty
    
    #Create all entity type objects.
    entities = root.find(u"entities")
    if entities is not None:
        for item in entities:
            new_entity = {
                REQUIRE: [],
                EFFECT: [],
                INCREMENT: 0,
            }
            
            iden = item.findtext(u"ID")
            if iden is not None:
                new_entity[ID] = iden
            
            require = item.find(u"require")
            if require is not None:
                for item2 in require:
                    new_entity[REQUIRE].append(item2.text)
    
            effect = item.find(u"effect")
            if effect is not None:
                for item2 in effect:
                    new_entity[EFFECT].append(item2.text)
            
            for stat in ENV[STATS]:
                new_entity[stat] = 0
            stats = item.find(u"stats")
            if stats is not None:
                for stat in stats:
                    new_entity[stat.tag] = int(stat.text)
                    
            for strings in ENV[STRINGS]:
                value = item.findtext(strings)
                if value is not None:
                    new_entity[strings] = value
                else:
                    new_entity[strings] = u""
            
            for lst in ENV[LISTS]:
                new_entity[lst] = []
                find_list = item.find(lst)
                if find_list is not None:
                    for value in find_list:
                        new_entity[lst].append(value.text)
                        
            OBJECT[new_entity[ID]] = new_entity

    #create all unit type objects
    units = root.find(u"units")
    if units is not None:
        for item in units:
            new_unit = {
                INCREMENT: 0,
                REQUIRE: [],
                EFFECT: [],
            }
            
            iden = item.findtext(u"ID")
            if iden is not None:
                new_unit[ID] = iden
            
            for stat in ENV[STATS]:
                new_unit[stat] = 0
            stats = item.find(u"stats")
            if stats is not None:
                for stat in stats:
                    new_unit[stat.tag] = int(stat.text)
                    
            for strings in ENV[STRINGS]:
                value = item.findtext(strings)
                if value is not None:
                    new_unit[strings] = value
                else:
                    new_unit[strings] = u""
            
            for lst in ENV[LISTS]:
                new_unit[lst] = []
                find_list = item.find(lst)
                if find_list is not None:
                    for value in find_list:
                        new_unit[lst].append(value.text)
                
            OBJECT[new_unit[ID]] = new_unit
            
            #Sets ENV variables for units.
            VAR[UNITS].append(new_unit[ID])
            if item.get(u"tick") == u"tick":
                VAR[TICK].append(new_unit[ID])
            elif item.get(u"tick") == u"clone":
                VAR[CTICK].append(new_unit[ID])
    
    VAR[STATE].append(copy.deepcopy(OBJECT))
    field = instance(OBJECT, ENV, VAR, SCRIPTS, LOG)
    
    try:
        def_tick = field.scripts[u"tick"][0]
        def_tick = interpret(def_tick, field)
        def_tick = compile(def_tick, u'<string>', u"exec")
    except KeyError:
        print u"warning, no tick is defined."
        def_tick = u""
    field.env[TICK] = def_tick
    
    return field
     
#---------------------------------------------------
#                  Interpreter                     -
#---------------------------------------------------

def interpret(string, env=False, debug=False):
    if string == None:
        return u''
    
    def isdef(value):
        if env:
            if value in env.object.keys():
                return u"'"+value+u"'"
        return value
    
    #targeting
    def CLASS(stringList, index):
        trgt = stringList[index - 1]
        group_type = stringList[index + 1]
        stringList[index + 1] = u"self.getGroupType(" + isdef(trgt)  + u", '" + group_type + u"', 'group')"
        stringList[index] = stringList[index - 1] = u""
        
    def SUB(stringList, index):
        #Do this better.
        stat = stringList[index +1]
        stringList[index] = u".__getitem__("+stat+u")"
        stringList[index +1] = u""
    
    #controlMove
    def ACTIVATE(stringList, index):
        trgt = stringList[index - 1]
        group_name = stringList[index + 1]
        mve = u"self.getGroupType( casterID, '" + group_name + u"', 'equip')"
        chain(stringList, index, mve)
    
    def ALL(stringList, index):
        #WARNING!! All is designed to be used only with move.
        #Nothing else accepts multi targets yet.
        group = stringList[index +1]
        stringList[index +1] = u'self.getGroup("' + group + u'")'
        stringList[index] = u''
        
        chain(stringList, index + 2, multi=True)       
    
    def CAST(stringList, index):
        chain(stringList, index)
        
    def chain(stringList, index, mve=None, multi=False):
        if mve == None:
            mve = stringList[index + 1 ]
        trgt = stringList[index - 1 ]
        stringList[index] = u"self.controlMove(casterID, "+ isdef(trgt) +u", "+ isdef(mve) +u", "
        
        if u'DELAY' not in stringList:
            stringList.append(u"-1")
        else:
            stringList[stringList.index(u'DELAY')] = u''
        stringList.append(u', '+ unicode(multi) + u")")
        stringList[index-1] = stringList[index + 1] = u""
        
    #controlList
    def GETS(stringList, index):
        trgt = stringList[index -1]
        stat = stringList[index +1]
        string = stringList[index +2]
        stringList[index] = u"self.controlList("+isdef(trgt)+u", '"+stat+u"', "+isdef(string)+u", 'add')" 
        stringList[index -1] = stringList[index +1] = stringList[index +2] = u''
    
    def LOSES(stringList, index):
        trgt = stringList[index -1]
        stat = stringList[index +1]
        string = stringList[index +2]
        stringList[index] = u"self.controlList("+isdef(trgt)+u", '"+stat+u"', "+isdef(string)+u", 'remove')"
        stringList[index -1] = stringList[index +1] = stringList[index +2] = u''
    
    #controlStat
    def CHANGE(stringList, index):
        trgt = stringList[index - 1]
        stat = stringList[index + 1]
        amount = stringList[index + 2]
        stringList[index] = u"self.controlStat( "+isdef(trgt)+u", '"+ stat +u"', "+amount+u")"
        stringList[index - 1] = stringList[index + 1] = stringList[index +2] = u""
        
    #controlString
    def REPLACE(stringList, index):
        trgt = stringList[index -1]
        stat = stringList[index +1]
        change = stringList[index +2]
        stringList[index] = u"self.controlString(" + isdef(trgt) + u", '" + stat + u"', '" + change + u"')"
        stringList[index +1] = stringList[index -1] = stringList[index +2] = u''
    
    #control Recruit
    def RECRUIT(stringList, index):
        trgt = stringList[index - 1]
        loc = stringList[index + 1]
        stringList[index] = u"self.controlRecruit(" + isdef(trgt) +u", "+loc+u")"
        stringList[index-1] = stringList[index +1] = u'' 
        
    #control Travel
    def TRAVEL(stringList, index):
        stringList[index] = u"self.controlTravel( casterID, targetLocation )"
        
    def MOVE(stringList, index):
        trgt = stringList[index -1]
        loc = stringList[index +2]
        command = stringList[index +1]
        stringList[index] = u"self.controlTravel("+ isdef(trgt) +u", "+ loc + u", '" + command +u"')"
        stringList[index -1] = stringList[index +1] = stringList[index +2] = u""
        
    def BUMP(stringList, index):
        trgt = stringList[index -1]
        stringList[index] = u"self.controlTravel( 'empty', self.getLocation("+ isdef(trgt) +u") )"
        stringList[index -1] = u''
    
    #instant requires
    def BLOCK(stringList, index):
        command = stringList[index + 1]
        stringList[index] = u"self.testBlock( casterLocation, targetLocation, '"+ command +u"')"
        stringList[index + 1] = u""
        
    def ONBOARD(stringList, index):
        stringList[index] = u"self.getLocation(targetID)"
    
    #numerical values
    def POSITION(stringList, index):
        if stringList[index -1] == u"casterID":
            trgt = u"casterLocation"
        elif stringList[index - 1] in [u"targetID", u'target']:
            trgt = u"targetLocation"
        
        if stringList[index + 1] == u"x":
            command = u"0"
        elif stringList[index + 1] == u'y':
            command = u"1"
        else:
            command = u''
        stringList[index] = trgt+u'.__getitem__('+ command +u')'
        stringList[index - 1] = u""
        if command != u'':
            stringList[index + 1] = u''
    
    def DISTANCE(stringList, index):
        dtype = stringList[index + 1]
        stringList[index] = u"self.getDistance(casterID, targetLocation, '" + dtype + u"')"
        stringList[index +1] = u""
        
    def DICE(stringList, index):
        value = stringList[index +1]
        stringList[index] = u"random.randint(1," + value + u")"
        stringList[index +1] = u""
    
    #getStat
    def STAT(stringList, index):
        trgt = stringList[index - 1]
        stat = stringList[index + 1]
        stringList[index] = u"self.getStat(" + isdef(trgt) + u", '" + stat + u"')"
        stringList[index-1] = stringList[index +1] = u""
    
    def LISTSTAT(stringList, index):
        trgt = stringList[index - 1]
        lst = stringList[index + 1]
        stat = stringList[index + 2]
        stringList[index] = u"self.getListStat(" + isdef(trgt) + u", '" + lst + u"', '" + stat + u"')"
        stringList[index-1] = stringList[index +1] = stringList[index + 2] = u""
        
    keyword = {
        u'ONBOARD': ONBOARD,
        u'ALL': ALL,
        u'LISTSTAT': LISTSTAT,
        u'STAT': STAT,
        u'S': STAT,
        u'MOVE': MOVE,
        u'CLASS': CLASS,
        u'ACTIVATE': ACTIVATE,
        u'GETS': GETS,
        u'LOSES': LOSES,
        u'CAST': CAST,
        u'CHANGE': CHANGE,
        u'TRAVEL': TRAVEL,
        u'BUMP': BUMP,
        u'RECRUIT': RECRUIT,
        u'BLOCK': BLOCK,
        u'DISTANCE': DISTANCE,
        u'POSITION': POSITION,
        u'DICE': DICE,
        u"REPLACE": REPLACE,
        u"SUB": SUB,
    }
    
    if debug:
        print string
    
    #Deal with Square brackets
    while u"[" in string:
        start = string.find(u"[")
        end = string.find(u"]")
        substr = string[start:end + 1]
        while substr.count(u"[") != substr.count(u"]"):
            end = string[end +1:].find(u"]") + end+1 
            substr = string[start:end+1]
        
        formula = string[start+1:end]
        if debug:
            print u"entering subshell"
        formula = interpret(formula, env, debug)
        if debug:
            print u"exiting subshell"
        formula = u"("+formula+u")"
        formula = formula.replace(u" ", u"")
        string = string[:start] + formula + string[end+1:]
        
    #parse remaining strings.
    stringList = re.split(u" ", string)
    
    #quotize
    for index in xrange(len(stringList)):
        if stringList[index] in [u"CASTER", u"C"]:
            stringList[index] = u"casterID"
        elif stringList[index] in [u"TARGET", u"T"]:
            stringList[index] = u"target"
        elif stringList[index] == u"SELF":
            stringList[index] = u"moveID"
    
    #compute remaining values
    for index in xrange(len(stringList)):
        if debug:
            print stringList
        check = stringList[index]
        try:
            keyword[check](stringList, index)
            continue
        except KeyError:
            pass
        if env:
            if stringList[index] in env.object.keys():
                stringList[index] = u"'"+stringList[index]+u"'"
                continue

    #prevents indentation errors
    while u"" in stringList:
        stringList.remove(u"")
    return u" ".join(stringList)

