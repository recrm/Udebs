from udebs import interpret
import random
import sys
import math 
import copy
import itertools
import re
import json

with open("udebs/keywords.json") as fp:
    interpret.importModule(json.load(fp), {'self': None})
    
#---------------------------------------------------
#                 Main Class                       -
#---------------------------------------------------

class instance:
    
    def __init__(self, *args, **kwargs):
        #config
        self.django = False
        self.compile = True
        self.hex = False
        self.name = 'Unknown'
        self.logging = True
        self.revert = 1
        
        #definitions
        self.lists = {'group', 'effect', 'require'}
        self.stats = {'increment'}
        self.strings = set()
        self.slist = {}
        self.rlist = set()
        self.rmap = set()
        
        #var
        self.time = 0
        self.delay = []
        self.map = {}
        self.log = []
        self.state = []
        
        #internal use only.
        self.data = {}
        self.variables = {}
        self.rand = random.Random()
        
        super(instance, self).__init__(*args, **kwargs)
        
    def __copy__(self):
        new = instance()
        new.__dict__.update(self.__dict__)
        new.delay = copy.deepcopy(self.delay)
        new.map = copy.deepcopy(self.map)
        new.data = copy.deepcopy(self.data)
        new.state = None
        
        return new
        
    #---------------------------------------------------
    #                 Get Functions                    -
    #---------------------------------------------------
    
    def getObject(self, string=False):
        """Returns object associated with string selector. Error if undefined"""
        if not string:
            return self.data.keys()
        try:
            return self.data[string]
        except KeyError:
            print(string)
            print(type(string))
            print(self.data[string])
            raise UndefinedEntityError(string)
    
    def getTarget(self, *targets, multi=False):
        """Returns entity object based on given selector.
        
        target - Any entity selector.
        multi - Boolean, allows lists of targets.
        
        """
        value = []
        for target in targets:
            ttype = type(target)
            if ttype is entity:
                value.append(target)
                
            elif ttype is bool:
                value.append(self.getObject('empty'))
            
            elif ttype is str:
                if target == "bump":
                    value.append(self.getObject('empty'))
                else:
                    value.append(self.getObject(target))
                
            elif ttype is list:
                if multi:
                    value.append(self.getTarget(*target))
                else:
                    value.append(self.getTarget(target[0]))

            elif ttype is tuple:
                if len(target) < 3:
                    target = (target[0], target[1], "map")
                name = self.getMap(target)
                if not name:
                    raise UndefinedSelectorError(target)
                    continue
                unit = self.getObject(name)
                if not unit.immutable:
                    value.append(unit)
                    continue
                loc_entity = copy.copy(unit)
                loc_entity.loc = target
                loc_entity.x = target[0]
                loc_entity.y = target[1]
                value.append(loc_entity)
            
            else:
                raise UndefinedSelectorError(target)
        
        if len(value) == 1:
            return value[0]
        return value
    
    
    def getStat(self, target, stat, maps=True):
        """Returns stat of entity object plus linked group objects.
        
        target - Entity selector.
        stat - Stat defined in env.lists, env.stats, or env.strings
        
        """ 
        #This function is a bottleneck
        target = self.getTarget(target)
        
        if stat == 'group':
            return target.group
        
        def classes(target):
            for item in target.group:
                yield self.getObject(item)
        
        def rlist(target):
            for lst in self.rlist:
                for cls in target.group:
                    for item in getattr(self.getObject(cls), lst):
                        yield self.getObject(item)
        
        def rmap(target):
            if target.loc:
                try:
                    current = target.loc[2]
                except IndexError:
                    current = "map"
                for map_ in self.rmap:
                    if map_ != current:
                        unit = self.getMap(map_).get(target.loc)
                        yield self.getObject(unit)
        
        if stat in self.strings:
            for item in itertools.chain(classes(target), rlist(target)):
                base = getattr(item, stat)
                if base:
                    return base
            if maps:
                for item in rmap(target):
                    base = self.getStat(item, stat, False)
                    if base:
                        return base
            return ""
        
        elif stat in self.stats:
            count = 0
            for item in classes(target):    
                count +=getattr(item, stat)
            for item in rlist(target):
                count +=self.getStat(item, stat)
            if maps:
                for item in rmap(target):
                    count +=self.getStat(item, stat, False)
            return count
        
        elif stat in self.lists:    
            lst = []
            for item in classes(target):
                lst.extend(getattr(item, stat))     
            for item in rlist(target):
                lst.extend(self.getStat(item, stat))
            if maps:
                for item in rmap(target):
                    lst.extend(self.getStat(item, stat, False))
            return lst
        else:
            raise UndefinedStatError(stat)
    
    def getDistance(self, one, two, method):
        """Returns distance between two entity selectors.
        
        one - Entity selector
        two - Entity selector
        method - Distance metric to used
        
        """
        #Note: Dictonary switch method doubles this functions run time.
        one, two = self.getTarget(one, two)
        one, two = one.loc, two.loc
        
        if False in {one, two}:
            return float("inf")  
        elif method == 'y':
            return int( abs( one[1] - two[1] ) )
        elif method == 'x':
            return int( abs( one[0] - two[0] ) )
        elif method == 'z':
            return abs(two[0] + two[1]) - (one[0] + one[1])
        elif method == 'hex':
            return (abs(one[0] - two[0]) + abs(one[1] - two[1]) + abs((two[0] + two[1]) - (one[0] + one[1])))/2
        elif method == "p1":
            return int(abs(one[0] - two[0]) + abs(one[1] - two[1]))
        elif method == "p2":
            return int(math.sqrt(math.pow(one[0] - two[0], 2) + math.pow(one[1] - two[1], 2)))
        elif method == "pinf":
            return max(abs(one[0] - two[0]), abs(one[1] - two[1]))
        elif method in self.getObject():
            count = 0
            for i in self.pathAdjacent(one, method):
                if two in i:
                    return count
                count +=1
            else:
                return float("inf")            
            
        else:
            print("Unknown distance metric")
            raise TypeError             
    
    def getLog(self):
        """Returns list of log entries made since last call."""
        test = copy.copy(self.log)
        self.controlLog(clear=True)
        return test
        
    def getMap(self, target="map"):
        """Returns first location for string in env.map."""
        ttype = type(target)
        if ttype is board:
            return target
        elif ttype is str:
            try:
                return self.map[target]
            except:
                raise UndefinedSelectorError(target)
        
        #down here kept for compatability reasons.
        elif ttype is tuple:
            try:
                map_ = target[2]
            except:
                map_ = "map"
            return self.getMap(map_).get(target)
            
        elif ttype is False:
            return False
        else:
            raise UndefinedSelectorError(target)
        
    def getLocation(self, target):
        """Returns location of entity selector."""
        return self.getTarget(target).loc
    
    def getRevert(self, value=0):
        storage = self.state
        index = -(value +1)
        try:
            new = copy.copy(self.state[index])
        except IndexError:
            return False
        new.state = self.state[:index+1]
        return new
    
    
    def getGroup(self, group, inc_self=False):
        """Return all objects belonging to group."""
        group = self.getTarget(group)
        
        found = []
        for unit in self.getObject():
            if group.name in self.getStat(unit, 'group'):
                found.append(unit)
        if not inc_self:
            found.remove(group.name)
        return found
    
    #returns combined stat for all elements in a list
    def getListStat(self, target, lst, stat):
        """Returns combination of all stats for objects in a units list.
        
        target - Entity selector
        lst - String representing list to check.
        stat - String representing defined stat.
        
        """
        target = self.getTarget(target)
        start = self.getStat(target.name, lst)
        
        if stat in self.stats:
            total = 0
            for element in start:
                inc = self.getStat(element, stat)
                total +=inc
            return total
        
        elif stat in self.lists:
            found = []
            for element in start:
                item = self.getStat(element, stat)
                found.extend(item)
            return found
        
        elif stat in self.stats:
            return start
        
        else:
            raise UndefinedStatError(stat)
        
    #returns first element in list contained in group
    def getListGroup(self, target, lst, group):
        """Returns first element in list that is a member of group.
        
        target - Entity selector.
        lst - String representing list to check.
        group - Entity selector representing group.
        
        """
        target, group = self.getTarget(target, group)
        start = self.getStat(target, lst)
        for item in start:
            if group.name in self.getStat(item, 'group'):
                return item
        return False
    
    def getSearch(self, *args):
        """Returns a list of objects contained in all groups.
        *args - lists of groups.
        ind - bool, only return first result if true."""
        foundIter = iter(args)
        first = foundIter.__next__()
        found = set(self.getGroup(first))
        for arg in args:
            found = found.intersection(self.getGroup(arg))
        return sorted(list(found))
        
    def getFill(self, center, move='empty', distance=float("inf")):        
        center, move = self.getTarget(center, move)
        
        found = []
        count = 0
        for i in self.pathAdjacent(center, move):
            found.extend(i)
            if count >= distance:
                break
            count +=1
        self.rand.shuffle(found)
        return found
    
    #Entity helper get functions.
    def getX(self, entity):
        entity = self.getTarget(entity)
        return entity.x
        
    def getY(self, entity):
        entity = self.getTarget(entity)
        return entity.y
    
    def getLoc(self, entity):
        entity = self.getTarget(entity)
        return entity.loc
        
    def getName(self, entity):
        entity = self.getTarget(entity)
        return entity.name
        
    #---------------------------------------------------
    #               Control Functions                  -
    #---------------------------------------------------
    
    #change so controlTime is pulling from scripts
    def controlTime(self, time=1):   
        """Changes internal time, runs tick script, and updates any delayed effects.
        
        time - Integer representing number of updates.
        
        """
        def checkdelay():
            while True:
                check = True
                for delay in copy.copy(self.delay):
                    if delay["DELAY"] <= 0:
                        check = False
                        env = self.createTarget(delay["CASTER"], 
                                                delay["TARGET"],
                                                delay["MOVE"])
                        self.controlEffect(env, delay['STRING'])
                        self.delay.remove(delay)
                if check:
                    self.controlRevert()
                    self.controlLog()
                    return
        
        if time != 0:
            for i in range(time):
                self.time +=1
                self.variables = {}
                self.controlLog('Env time is now', self.time)
                if 'tick' in self.getObject():
                    env = self.createTarget("empty", 'empty', "tick")
                    if self.testRequire(env) == True:
                        self.controlEffect(env)
                for delay in self.delay:
                    delay["DELAY"] -=1
                checkdelay()
        else:
            checkdelay()
            self.variables = {}
            
        if self.django:
            self.save()
        return True
    
    def controlRevert(self):
        if self.revert > 1 and self.state:
            clone = copy.copy(self) 
            self.state.append(clone)
            if len(self.state) > self.revert:
                self.state = self.state[1:]

    def controlLog(self, *args, clear=False):
        """Adds entry to log.
        
        *args - Similar to print command.
        clear - Boolean, clears log entries if true.
        
        """
        if not self.logging:
            return False
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
    
    def controlStat(self, targets, stat, increment ):
        """Changes stored stat of target by increment.
        
        targets - Multiple Entity selector
        stat - Defined statistic to change
        increment - integer to change stat by.
        
        """
        targets = self.getTarget(targets, multi=True)
        increment = int(increment)
        flag = False
        if increment == 0:
            return False
        
        for target in targets:
            if target.immutable:
                continue
            
            newValue = getattr(target, stat) + increment
            setattr(target, stat, newValue)
            if stat is not 'increment':
                self.controlLog(target.name, stat, "changed by", increment, "is now", self.getStat(target, stat))
            if self.django:
                target.save()
            flag = True
        
        return flag
    
    def controlString(self, targets, strg, new):
        """Changes stored stat of target by increment.
        
        targets - Multiple Entity selector
        stat - Defined statistic to change
        increment - String to change stat to.
        
        """
        targets = self.getTarget(targets, multi=True)
        flag = False
        
        for target in targets:
            if target.immutable:
                continue
            
            setattr(target, strg, new)
            self.controlLog(target.name, strg, "is now", new)
            if self.django:
                target.save()
            flag = True
        
        return flag
        
    def controlList(self, targets, lst, entries, method='add'):
        """Adds or removes items in Entity list.
        
        targets - Multiple Entity selector
        lst - Defined list to change.
        entry - String to add or remove.
        increment - String to add to or remove from list.
        
        """
        flag = False
        targets = self.getTarget(targets, multi=True)
        if not isinstance(entries, list):
            entries = [entries]
        
        for target in targets:
            for entry in entries:
                if isinstance(entry, entity):
                    entry = entry.name
        
                if target.immutable:
                    continue
                
                list_ = getattr(target, lst)
                if method == 'remove':
                    if entry in list_:
                        list_.remove(entry)
                        self.controlLog(entry, "removed from", target.name, lst)
                        flag = True
                        if self.django:
                            target.save()
                    continue
                
                elif lst in self.slist:
                    if not self.slist[lst] in self.getStat(entry, "group"):
                        self.controlLog("Can't special add", entry, "to", lst, "because invalid type.")
                        continue

                    env = self.createTarget('empty', target, entry)
                    check = self.testRequire(env)
                    if check != True:
                        self.controlLog("Can't special add", entry, "to", lst, "because", check)
                        continue
                        
                list_.append(entry)
                self.controlLog(entry, "added to", target.name, lst)
                flag = True
                if self.django:
                    target.save()
            
        return flag
            
    
    def controlRecruit(self, clone, positions=[None], tick=False):
        positions = self.getTarget(positions, multi=True)
        clone = self.getTarget(clone)
        new_unit = None
        
        if clone.immutable:
            self.controlLog("can't clone immutable entity.")
            return False
        
        for position in positions:
           
            new_unit = copy.copy(clone)
            if self.django:
                new_unit.id = None
            
            #change name
            self.controlStat(clone, 'increment', 1)
            new_unit.name = clone.name + str(clone.increment)
            
            #change group
            new_unit.group.remove(clone.name)
            new_unit.group = [new_unit.name] + new_unit.group
            
            #add object to env
            new_unit.record(self)
            self.controlLog(new_unit.name, "has been recruited")
            
            #travel object to location
            if position is not None:
                self.controlTravel(new_unit, position)
        
        return new_unit
    
    def controlTravel(self, caster, targets=False):
        
        caster = self.getTarget(caster)
        targets = self.getTarget(targets, multi=True)
        
        for target in targets:

            #check if targetLoc is valid
            map_caster = self.getMap(caster.loc[2]) if caster.loc else False
            map_target = self.getMap(target.loc[2]) if target.loc else False
            
            if not caster.loc and not target.loc:
                self.controlLog("Warning: tried to move offboard to offboard")
                return False
            
            #move units
            if target.loc:
                map_target.insert(caster.name, target.loc)
            if caster.loc:
                map_caster.insert(map_caster.empty, caster.loc)
            
            #update units
            target.update(self)
            caster.update(self)
            
            #control Logs
            if not caster.immutable:
                self.controlLog(caster.name, "has moved to", caster.loc)
                if self.django:
                    caster.save()
            if not target.immutable and target.name != caster.name: 
                self.controlLog(target.name, "has been bumped")
                if self.django:
                    target.save()
            
        return True
         
    def controlDelay(self, caster, target, move, call_string, delay):
        new_delay = {
            "DELAY": delay,
            "STRING": call_string,
            "CASTER": caster,
            "TARGET": target,
            "MOVE": move,
        }
        self.controlLog("effect added to delay for", delay)
        self.delay.append(new_delay)
        if self.django:
            self.save()
        return True
    
    def controlMove(self, caster, targets , moves, force=False):
        caster = self.getTarget(caster)
        targets, moves = self.getTarget(targets, moves, multi=True)
        flag = False
        self.controlLog(caster.name, "uses", [move.name for move in moves], "on", [target.name for target in targets])
        for target in targets:
            for move in moves:
                env = self.createTarget(caster, target, move)
                check = True if force else self.testRequire(env)
                
                if check != True:
                    self.controlLog(caster.name, "cast", move.name, "on", 
                                    target.name, "failed because", check)
                    continue
                 
                self.controlLog(caster.name, "uses", move.name, "on", target.name)
                self.controlEffect(env)
                flag = True
        
        return flag
        
    def controlEffect(self, env, single=False, require=False):
        command = "require" if require else "effect"
        effects = [single] if single else self.getStat(env['storage']['move'], command)
        
        for effect in effects:
            if isinstance(effect, script):
                value = effect.code
                raw = effect.raw
                trans = effect.interpret
            else:
                value = raw = trans = effect
            try:
                if not eval(value, env):
                    if require:
                        return raw
                        
            except:
                print("invalid\n\n", raw, "\n\ninterpreted as\n\n", trans)
                raise
        
        return True
    
    #---------------------------------------------------
    #                 User only wrappers               -
    #---------------------------------------------------
    def castMove(self, caster, target , move, force=False):
        self.controlMove(caster, target, move, force)
        self.controlTime(0)
        
    def controlInit(self, move):
        self.controlMove("empty", "empty", move)
        self.controlTime(0)
    
    #---------------------------------------------------
    #                 Pathing Functions                -
    #---------------------------------------------------
    
    def adjacent(self, location, pointer=None):
        """Iterates of adjacent tiles"""
        x = location[0]
        y = location[1]
        map_ = location[2]
        found = {
            (x -1, y, map_), 
            (x, y +1, map_),
            (x +1, y, map_),
            (x, y -1, map_),
        }
        if self.hex:
            found.add((x -1, y +1, map_))
            found.add((x +1, y -1, map_))
        if self.hex == "diag":
            found.add((x +1, y +1, map_))
            found.add((x -1, y -1, map_))
        if isinstance(pointer, dict):
            for item in found:
                if item not in pointer:
                    pointer[item] = location
        return found
        
    def pathAdjacent(self, center, move="empty", pointer=None):
        """Iterates over concentric circles of adjacent tiles"""
        center, move = self.getTarget(center, move)
        
        if not center.loc:
            yield list()
            return
        
        new = {center.loc}
        searched = {center.loc}
        next = set(self.adjacent(center.loc, pointer))          
        
        next.difference_update(searched)
        
        while len(new) > 0:
            #Sorted is needed to force program to be deterministic.
            yield sorted(list(new))
            new = set()
            for node in next:        
                if not self.getMap(node):
                    continue
                if self.testMove(center, node, move):
                    new.add(node)
            
            searched.update(next)
            next = set().union(*[self.adjacent(node, pointer) for node in new])
            next.difference_update(searched)
            
    def pathTowards(self, start, finish, move):
        start, finish, move = self.getTarget(start, finish, move)
        pointer = {}
        
        for i in self.pathAdjacent(start, move, pointer):
            if finish.loc in i:
                break
        else:
            return False

        found = [finish.loc]
        while True:
            new = pointer[found[-1]]
            found.append(new)
            if new == start.loc:
                found.reverse()
                return found
          
    #---------------------------------------------------
    #                 Test Functions                   -
    #---------------------------------------------------
    
    def testMove(self, unit, target, move, single=False):
        env = self.createTarget(unit, target, move)
        test = self.testRequire(env, single=single)
        return True if test == True else False
        
    def testRequire(self, env, single=False):
        return self.controlEffect(env, single, True)
    
    def testBlock(self, start, finish, move):
        start, finish, move = self.getTarget(start, finish, move)

        for i in self.pathAdjacent(start, move):
            for q in i:
                if finish.loc in self.adjacent(q):
                    return True
        return False
        
    def testFuture(self, caster, target, move, string, time=0):
        
        caster, target, move = self.getTarget(caster, target, move)
        
        #create test instance
        clone = copy.copy(self)
        clone.logging = False
        
        #convert instance targets into clone targets.
        caster, target, move = clone.getTarget(caster.loc, target.loc, move.name)
        
        #test situation
        clone.controlMove(caster, target, move, force=True)
        clone.controlTime(time)
        return clone.testMove(caster, target, move, single=string) 
        
    def createTarget(self, caster, target, move):
        
        caster, target, move = self.getTarget(caster, target, move)
        
        var_local = {
            "caster": caster,
            "target": target,
            "move": move,
            "C": caster,
            "T": target,
            "M": move,
        }
        
        var_glob = {"self": self}
        return interpret.getEnv(var_local, var_glob)

#---------------------------------------------------
#                 Other Objects                    -
#---------------------------------------------------

class UndefinedEntityError(Exception):
    def __init__(self, entity):
        self.entity = entity
        
    def __str__(self):
        return repr(self.entity)+" is not a defined entity."

class UndefinedStatError(Exception):
    def __init__(self, stat):
        self.stat = stat
        
    def __str__(self):
        return repr(self.stat)+" is not a defined stat."

class UndefinedSelectorError(Exception):
    def __init__(self, target):
        self.selector = target

    def __str__(self):
        return repr(self.selector)+" is not a valid target selector"

class entity:
    def __init__(self, field=instance(), name="empty", *args, **kwargs):
        self.name = name
        self.loc = False
        self.x = False
        self.y = False
        self.immutable = False
        for stat in field.stats:
            setattr(self, stat, 0)
        for lists in field.lists:
            setattr(self, lists, [])
        for string in field.strings:
            setattr(self, string, '')
        self.group.append(self.name)
        
        super(entity, self).__init__(*args, **kwargs)
        
    def __repr__(self):
        return "<entity: "+self.name+">"
    
    def __iter__(self):
        yield self
    
    def __copy__(self):
        new = entity()
        for k, v in self.__dict__.items():
            if isinstance(v, list):
                setattr(new, k, copy.copy(v))
            else:
                setattr(new, k, v)
        
        return new
    
    def __add__(self, other):
        new = entity()
        for stat in field.stats:
            setattr(new, stat, getattr(self, stat) + getattr(other, stat))
        for lists in field.lists:
            setattr(new, lists, getattr(self, stat) + getattr(other, stat))
        for string in field.strings:
            setattr(new, string, getattr(self, stat))
        return new
            
    def update(self, env=instance()):
        if not self.immutable:      
            for map_ in env.map.values():
                test = map_.find(self.name)
                if test:
                    self.loc = test
                    self.x = test[0]
                    self.y = test[1]
                    return
        self.loc = False
        self.x = False
        self.y = False
        
    def record(self, field, name=False):
        if not name:
            name = self.name
        field.data[name] = self
        
class script:
    def __init__(self, effect, require=False):
        
        command = 'eval' if require else 'exec'
        
        self.raw = effect
        self.interpret = interpret.interpret(effect)
        try:
            self.code = compile(self.interpret, '<string>', command)
        except SyntaxError:
            print(effect)
            raise
            
    def __repr__(self):
        return self.raw
        
class board:
    def __init__(self):
        self.map = []
        self.name = "unknown"
        self.empty = "empty"
    
    def x(self):
        return len(self.map)
        
    def y(self):
        try:
            return max([len(x) for x in self.map])
        except:
            return 0
        
    def size(self):
        return self.x() * self.y()
        
    def insert(self, string, location):
        x = location[0]
        y = location[1]
        
        if x < 0 or y < 0:
            raise Exception
        self.map[x][y] = string
    
    def get(self, loc):
        if not loc:
            return False
        x = loc[0]
        y = loc[1]
        if x < 0 or y < 0:
            return False
        try:
            return self.map[x][y]
        except IndexError:
            return False
    
    def find(self, string):
        x = 0
        for column in self.map:
            try:
                y = column.index(string)
                return (x, y, self.name)
            except ValueError:
                x +=1
                continue
        else:
            return False
        
    def __repr__(self):
        return "<board: "+self.name+">"
    

