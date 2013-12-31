
import sys
import math 
import copy
import itertools
import re
import random
from xml.etree import ElementTree
      
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
        
        #needs to be adjusted manually.
        self.variables = {}
        
        #internal use only.
        self.data = {}
               
        super(instance, self).__init__(*args, **kwargs)
        
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
    
    def getLog(self):
        """Returns list of log entries made since last call."""
        test = copy.deepcopy(self.log)
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
            for i in pathAdjacent(one, method):
                if two in i:
                    return count
                count +=1
            else:
                return float("inf")            
            
        else:
            print("Unknown distance metric")
            raise TypeError             
        
    def getGroup(self, group, inc_self=True):
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
                    self.controlLog()
                    return
        
        if time != 0:
            for i in range(time):
                self.time +=1
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
        
        if self.django:
            self.save()
        return True

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
        
    def controlList(self, targets, lst, entry, method='add'):
        """Adds or removes items in Entity list.
        
        targets - Multiple Entity selector
        lst - Defined list to change.
        entry - String to add or remove.
        increment - String to add to or remove from list.
        
        """
        flag = False
        targets = self.getTarget(targets, multi=True)
        if isinstance(entry, entity):
            entry = entry.name
        
        for target in targets:
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
           
            new_unit = copy.deepcopy(clone)
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
            
    def controlTravel(self, caster, target=False):    
        
        if not target or target == 'bump':
            target = caster
            caster = 'empty'
        
        caster, target = self.getTarget(caster, target)
        
        #check if targetLoc is valid
        if not target.loc:
            self.controlLog("Warning", caster.name, "trying to move off the stage.")
            return False
        mtarget = self.getMap(target.loc[2])    
        
        if caster.loc:    
            mcaster = self.getMap(caster.loc[2])
        else:
            mcaster = False
        
        #move caster
        if caster.loc:
            mcaster.insert("empty", caster.loc)
        mtarget.insert(caster.name, target.loc)
        
        target.update(self)
        caster.update(self)
   
        #control Logs
        if caster.name != 'empty':
            self.controlLog(
                caster.name, 
                "has moved to", 
                caster.loc
            )
            if self.django:
                caster.save()
        if not target.immutable: 
            if target.name != caster.name:
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

    def controlMove(self, caster, targets , moves):
        caster = self.getTarget(caster)
        targets, moves = self.getTarget(targets, moves, multi=True)
        flag = False
        
        for target in targets:
            for move in moves:
                env = self.createTarget(caster, target, move)
                check = self.testRequire(env)
        
                if check != True:
                    self.controlLog(env['caster'].name, "cast", 
                                    env['move'].name,"on", 
                                    env['target'].name, "failed because", 
                                    check)
                    continue
                        
                self.controlLog(env['caster'].name, "uses", env['move'].name,
                                "on", env['target'].name)
        
                self.controlEffect(env)
                flag = True
                
        return flag
        
    def controlEffect(self, env, single=False):
        
        effects = [single] if single else self.getStat(env['move'], 'effect')
        
        for effect in effects:
            if not isinstance(effect, script):
                effect = script(effect, False)
            try:
                exec(effect.code, env)
            except:
                print("invalid\n\n", effect.raw, "\n\ninterpreted as\n\n", effect.interpret)
                raise  
        
        return True

    
    #---------------------------------------------------
    #                 Pathing Functions                -
    #---------------------------------------------------
    
    def adjacent(self, location):
        x = location[0]
        y = location[1]
        map_ = location[2]
        yield (x -1, y, map_)
        yield (x, y +1, map_)
        yield (x +1, y, map_)
        yield (x, y -1, map_)
        if self.hex:
            yield (x -1, y +1, map_)
            yield (x +1, y -1, map_)
        if self.hex == "diag":
            yield (x +1, y +1, map_)
            yield (x -1, y -1, map_)
        return
        
    def pathAdjacent(center, move="empty"):
        center, move = self.getTarget(center, move)
        
        if not center.loc:
            yield set()
            return
        
        new = {center.loc}
        searched = {center.loc}
        next = set(self.adjacent(center.loc))
        next.difference_update(searched)
        
        while len(new) > 0:
            yield new
            new = set()
            for node in next:        
                if not self.getMap(node):
                    continue
                env = self.createTarget(center, node, move)
                if self.testRequire(env) == True:
                    new.add(node)
            
            searched.update(next)
            next = set().union(*[self.adjacent(node) for node in new])
            next.difference_update(searched)
      
    def getFill(self, center, move='empty', distance=float("inf")):        
        center, move = self.getTarget(center, move)
        
        found = []
        count = 0
        for i in pathAdjacent(center, move):
            found.extend(i)
            if count >= distance:
                break
            count +=1
        random.shuffle(found)
        return found
        
    def testBlock(self, start, finish, move):
        #I'd really like to incorporate this directly into new testBlock.
        if move in {"x", "y", "diag"}:
            return self.testBlockOld(start, finish, move)
        
        start, finish, move = self.getTarget(start, finish, move)
        
        for i in self.pathAdjacent(start, move):
            if finish in i:
                return True
        return False
        
    def pathTowards(self, start, finish, move):
        start, finish, move = self.getTarget(start, finish, move)
        
        end = set()
        for i in pathAdjacent(start, move):
            end = i
        #function not completed.
        
        
        
        
    
    
    
        
    def testBlockOld(self, start, finish, path ):
        check = []
        
        #accepted paths (x, y, diag)
        
        start = self.getTarget(start).loc
        finish = self.getTarget(finish).loc
 
        if start == False or finish == False:
            return False
        
        def changeX(start):
            new = copy.copy(start)
            if start[0] < finish[0]:
                n = 1
            else:
                n = -1
            for i in range(n, finish[0] - start[0] + n, n):
                new = (start[0] + i, start[1])
                check.append(new)
            return new
        
        def changeY( start):
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
            recent = changeX(start)
            changeY(recent)
                
        elif path == "y":
            recent = changeY(start)
            changeX(recent)
            
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

    def testRequire(self, env):
        for require in self.getStat(env['move'], 'require'):
            if not isinstance(require, script):
                require = script(require, True)
            try:
                if not eval(require.code, env):
                    return require.raw
            except:
                print("invalid (", require.raw, ") interpreted as (", require.interpret, ")")
                raise
        return True
    
    def createTarget(self, caster, target, move, add={}):
        
        caster, target, move = self.getTarget(caster, target, move)
        
        environment = {
            "caster": caster,
            "target": target,
            "C": caster,
            "T": target,
            "self": self,
            "randint": random.randint,
            "move": move,
        }
        environment.update(self.variables)
        environment.update(add)
         
        return environment

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
        self.map = False
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
            
    def update(self, env=instance()):
        if not self.immutable:      
            for map_ in env.map.values():
                test = map_.find(self.name)
                if test:
                    self.loc = test
                    return
        self.loc = False
        
    def record(self, field, name=False):
        if not name:
            name = self.name
        field.data[name] = self
        
class script:
    def __init__(self, effect, require=False):
        command = 'eval' if require else 'exec'
        
        self.raw = effect
        self.interpret = interpret(effect)
        self.code = compile(self.interpret, '<string>', command)
        
    def __repr__(self):
        return self.raw
        
class board:
    def __init__(self):
        self.map = []
        self.name = "unknown"

    
    def x(self):
        return len(self.map)
        
    def y(self):
        try:
            return len(self.map[0])
        except IndexError:
            return 0
        
    def size(self):
        return self.x() * self.y()
        
    def insert(self, string, location):
        x = location[0]
        y = location[1]
        
        if x < 0 or y < 0:
            raise Exception
        try:
            self.map[x][y] = string
        except IndexError:
            raise Exception
    
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
    
#---------------------------------------------------
#                      XML parser                  -
#---------------------------------------------------

#creates an xml file from instance object.
def battleWrite(env, location, pretty=False):
    e = ElementTree
    root = e.Element('udebs')
    
    definitions = e.SubElement(root, 'definitions')
    for dtype in ['stats', 'lists', 'strings']:
        middle = e.SubElement(definitions, dtype)
        for item in getattr(env, dtype):
            if item in {'group', 'effect', 'require', 'increment'}:
                continue
            final = e.SubElement(middle, item)
            if item in env.rlist:
                final.attrib['rlist'] = ''
            if item in env.slist:
                final.attrib['slist'] = env.slist[item]
    
    config = e.SubElement(root, 'config')
    if env.name != 'Unknown':
        name = e.SubElement(config, 'name')
        name.text = env.name
    if env.hex != False:
        hexmap = e.SubElement(config, 'hex')
        hexmap.text = str(env.hex)
    if env.logging != True:
        logging = e.SubElement(config, 'logging')
        logging.text = str(env.logging)
    if env.compile != True:
        compile_ = e.SubElement(config, 'compile')
        compile_.text = str(env.compile)
    if env.django != False:
        django = e.SubElement(config, 'django')
        django.text = str(env.django)
    
    #map
    maps = e.SubElement(root, 'maps')
    for map_ in env.map.values():
        node = e.SubElement(maps, map_.name)
        if map_.name in env.rmap:
            node.attrib['rmap'] = ''
        scan = [list(i) for i in zip(*map_.map)]
        for row in scan:
            middle = e.SubElement(node, 'row')
            text = ''
            for item in row:
                text = text + ', ' + item
            middle.text = text[2:]
    
    var = e.SubElement(root, 'var')
    if env.time != 0:
        time = e.SubElement(var, 'time')
        time.text = str(env.time)
    
    if env.delay != []:
        delay = e.SubElement(var, 'delay')
        for item in env.delay:
            node = e.SubElement(delay, 'i')
            node.attrib.update(item)
            for key, value in node.attrib.items():
                if isinstance(value, entity):
                    if not value.immutable:
                        node.attrib[key] = str(value.name)
                    else:
                        node.attrib[key] = str(value.loc)
                else:
                    node.attrib[key] = str(value)
    
    if env.log != []:
        log = e.SubElement(var, 'log')
        for item in env.log:
            node = e.SubElement(log, 'i')
            node.text = item

    #entities
    entities = e.SubElement(root, 'entities')
    for entry in env.getObject():   
        entity = env.getObject(entry)
        stats = env.stats.union(env.strings, env.lists)
        entity_node = e.SubElement(entities, entity.name)
        for stat in stats:
            value = getattr(entity, stat)
            if value in [0, '', list()]:
                continue
            stat_node = e.SubElement(entity_node, stat)
            if stat in env.lists:
                for item in value:
                    entry_node = e.SubElement(stat_node, 'i')
                    entry_node.text = str(item)
            else:
                stat_node.text = str(value)
            
    def indent(elem, level=0):
        i = "\n" + level*"  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                indent(elem, level+1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i    
    
    if pretty:
        indent(root)
    tree = e.ElementTree(root)
    tree.write(location)
    
    return True

#Creates and instance object from xml file.
def battleStart(xml_file):
    
    try:
        tree = ElementTree.parse(xml_file)
        root = tree.getroot()
    except IOError:
        root = ElementTree.fromstring(xml_file)
        
    #ENV
    field = instance()
    
    config = root.find("config")
    if config is not None:
        
        name = config.findtext("name")
        if name is not None:
            field.name = name
        
        django = config.findtext('django')
        if django is not None:
            field.django = eval(django)
        
        comp = config.findtext("compile")
        if comp is not None:
            field.compile = eval(comp)
        
        logichex = config.findtext("hex")
        if logichex is not None:
            field.hex = eval(logichex)
                    
        logging = config.findtext('logging')
        if logging is not None:
            field.logging = eval(logging)
    
    defs = root.find("definitions")    
    if defs is not None:
        def_stats = defs.find("stats")
        if def_stats is not None:
            for stat in def_stats:
                field.stats.add(stat.tag)
                
        def_lists = defs.find("lists")
        if def_lists is not None:
            for stat in def_lists:
                field.lists.add(stat.tag)
                if stat.get('rlist') is not None:
                    field.rlist.add(stat.tag)
                if stat.get('slist') is not None:
                    field.slist[stat.tag] = stat.get('slist')
                              
        def_strings = defs.find("strings")
        if def_strings is not None:
            for stat in def_strings:
                field.strings.add(stat.tag)
        
    def addMap(field_map):
        new_map = board()
        new_map.name = field_map.tag
        dim_map = field_map.find("dim")
        if dim_map is not None:
            x = int(dim_map.find('x').text)
            y = int(dim_map.find('y').text)
            for element in range(y):
                new_map.map.append(['empty' for i in range(x)])
        else:
            temp = []
            for row in field_map:
                temp.append(re.split("\W*,\W*", row.text))
            new_map.map = [list(i) for i in zip(*temp)]
        return new_map
    
    #VAR
    field_maps = root.find("maps")
    if field_maps is not None:
        for map_ in field_maps:
            new_map = addMap(map_)
            field.map[new_map.name] = new_map
            if map_.get('rmap') is not None:
                field.rmap.add(map_.tag)
            
    else:
        field_map = root.find("map")
        if field_map is not None:
            new_map = addMap(field_map)
            field.map[new_map.name] = new_map
            
    var = root.find('var')
    if var is not None:
        time = var.find('time')
        if time is not None:
            field.time = int(time.text)
            
        delay = var.find('delay')
        if delay is not None:
            for item in delay:
                for key in item.attrib:
                    if key == 'DELAY':
                        item.attrib[key] = int(item.attrib[key])
                    if key in {'CASTER', 'TARGET', 'MOVE'}:
                        try:
                            index = item.attrib[key].index(',')
                            x = int(item.attrib[key][1:index])
                            y = int(item.attrib[key][index+2:-1])
                            item.attrib[key] = (x,y)
                        except ValueError:
                            pass    
                field.delay.append(item.attrib)
        
        log = var.find('log')
        if log is not None:
            for item in log:
                field.log.append(item.text)
    
    if field.django:
        field.save()
    
    
    #Set empty 
    empty = entity(field)
    empty.immutable = True
    empty.record(field)
    
    #Create all entity type objects.
    def addObject(item):
        new_entity = entity(field, item.tag)
        new_entity.name = item.tag
        if item.get('immutable') is not None:
            new_entity.immutable = True
        
        for stat in field.stats:
            elem = item.find(stat)
            add_attr = int(elem.text) if elem is not None else 0
            setattr(new_entity, stat, add_attr)
                
        for string in field.strings:
            value = item.findtext(string)
            add_attr = value if value is not None else ""
            setattr(new_entity, string, add_attr)
            
        for lst in field.lists:
            new_list = getattr(new_entity, lst)
            find_list = item.find(lst)
            if find_list is not None:
                if len(find_list) == 0:
                    find_list = [find_list]
                for value in find_list:
                    if field.compile and lst in {"effect", "require"}:
                        require = True if lst == "require" else False
                        value.text = script(value.text, require)
                    new_list.append(value.text)
            setattr(new_entity, lst, new_list)
        
        new_entity.update(field)
        new_entity.record(field)
        
        return new_entity
                        
    entities = root.find("entities")
    if entities is not None:
        for item in entities:
            new_entity = addObject(item)
    
    field.controlLog("INITIALIZING", field.name, "\n")
    if 'tick' not in field.getObject():
        field.controlLog("warning, no tick is defined.")
    
    return field
     
#---------------------------------------------------
#                  Interpreter                     -
#---------------------------------------------------

def interpret(string, debug=False):
    
    #utility
    def s(string):
        if string[0] in {"'", '"', "{"}:
            return string
        if "var." in string:
            return string.replace("var.", "")
        if string in {"caster", "target", "move", "T", "C"}:
            return string
        if "." in string:
            return string
        return "'"+string+"'"
    
    def erase(list_, index, range_):
        for i in range_:
            list_[i+index] = ""
        return list_
    
    def call(function, *args, env=True):
        value = ("self." if env else "")+function+"{"
        first = True
        for arg in args:
            value = value+arg if first else value+","+arg
            first = False
        value = value + "}"
        return value
    
    #keywords
    def DELAY(list_, i):
        f = "controlDelay"
        string = "'"+list_[i+1].replace("'", "\\'")+"'"
        delay = list_[i+2]
        list_[i] = call(f,'caster','target','move',string,delay)
        erase(list_, i, (1,2))
    
    #targeting
    def CLASS(list_, i):
        f = "getListGroup"
        target = list_[i + 1]
        grtype = list_[i + 2]
        list_[i] = call(f, s(target), "'group'", s(grtype))
        erase(list_, i, (1,2))
        
    def ALL(list_, i):
        f = "getGroup"
        group = list_[i +1]
        list_[i] = call(f, s(group))
        erase(list_, i, (1,))
        
    def FILL(list_, i):
        f = "getFill"
        target = list_[i + 1]
        move = list_[i + 2]
        list_[i] = call(f, s(target), s(move))
        erase(list_, i, (1,2))
        
    #controlMove
    def ACTIVATE(list_, i):
        f = "controlMove"
        g = "getListGroup"
        caster = "caster"
        target = list_[i +1]
        slist_ = list_[i +2]
        group = list_[i +3]
        if i != 0:
            caster = list_[i-1]
            list_[i-1] = ""
            
        move = call(g, s(caster), s(slist_), s(group))
        list_[i] = call(f, s(caster), s(target), move)
        erase(list_, i, (1,2,3))
        
    def CAST(list_, i):
        f = "controlMove"
        target = list_[i + 1]
        move = list_[i + 2]
        
        if i == 0:
            caster = "caster"
        else:
            caster = list_[i-1]
            list_[i-1] = ""
            
        list_[i] = call(f, s(caster), s(target), s(move))
        erase(list_, i, (1,2))
        
    #controlList
    def GETS(list_, i):
        f = "controlList"
        target = list_[i +1]
        slist = list_[i +2]
        move = list_[i +3]
        list_[i] = call(f, s(target), s(slist), s(move), s('add'))
        erase(list_, i, (1,2,3))
    
    def LOSES(list_, i):
        f = "controlList"
        target = list_[i +1]
        slist = list_[i +2]
        move = list_[i +3]
        list_[i] = call(f, s(target), s(slist), s(move), s('remove'))
        erase(list_, i, (1,2,3))
    
    #controlStat
    def CHANGE(list_, i):
        f = "controlStat"
        target = list_[i +1]
        stat = list_[i +2]
        amount = list_[i +3]
        list_[i] = call(f, s(target), s(stat), amount)
        erase(list_, i, (1,2,3))
        
    #controlString
    def REPLACE(list_, i):
        f = "controlString"
        target = list_[i +1]
        stat = list_[i +2]
        change = list_[i +3]
        list_[i] = call(f, s(target), s(stat), s(change))
        erase(list_, i, (1,2,3))
    
    #control Recruit
    def RECRUIT(list_, i):
        f = "controlRecruit"
        target = list_[i +1]
        location = list_[i +2]
        list_[i] = call(f, s(target), s(location))
        erase(list_, i, (1,2))
        
    #control Travel
    def TRAVEL(list_, i):
        f = "controlTravel"
        location = list_[i +1]
        if i == 0:
            caster = "caster"
        else:
            caster = list_[i-1]
            list_[i-1] = ""
        list_[i] = call(f, s(caster), s(location))
        erase(list_, i, (1,))
        
    def MOVE(list_, i):
        f = "controlTravel"
        target = list_[i+1]
        location = list_[i+2]
        list_[i] = call(f, s(target), s(location))
        erase(list_, i, (1,2))
    
    #instant requires
    def BLOCK(list_, i):
        f = "testBlock"
        command = list_[i + 1]
        list_[i] = call(f, 'caster', 'target', s(command))
        erase(list_, i, (1,))
    
    #might change for arbitrary target
    def ONBOARD(list_, i):
        f = "getLocation"
        list_[i] = 'target.loc'
        
    def ISUNIT(list_, i):
        f = "getMap"
        list_[i] = call(f, 'target.name')
        
    #this one feels like arbitray target distance might be nice
    def DISTANCE(list_, i):
        f = "getDistance"
        dtype = list_[i + 1]
        list_[i] = call(f, 'caster', 'target', s(dtype))
        erase(list_, i, (1,))
        
    def DICE(list_, i):
        f = "randint"
        value = list_[i +1]
        list_[i] = call(f, "0", value, env=False)
        erase(list_, i, (1,))
    
    #getStat
    def STAT(list_, i):
        f = "getStat"
        target = list_[i +1]
        stat = list_[i +2]
        list_[i] = call(f, s(target), s(stat))
        erase(list_, i, (1,2))
    
    def LISTSTAT(list_, i):
        f = "getListStat"
        target = list_[i +1]
        slist = list_[i +2]
        stat = list_[i +3]
        list_[i] = call(f, s(target), s(slist), s(stat))
        erase(list_, i, (1,2,3))
    
    def LISTGROUP(list_, i):
        f = "getListGroup"
        target = list_[i+1]
        stat = list_[i+2]
        group = list_[i+3]
        list_[i] = call(f, s(target), s(stat), s(group))
        erase(list_, i, (1,2,3))
        
    #shortcuts
    
    keyword = {
        'MOVE': MOVE,
        'DELAY': DELAY,
        'ONBOARD': ONBOARD,
        'ALL': ALL,
        'LISTSTAT': LISTSTAT,
        'STAT': STAT,
        'S': STAT,
        'CLASS': CLASS,
        'ACTIVATE': ACTIVATE,
        'GETS': GETS,
        'LOSES': LOSES,
        'CAST': CAST,
        'CHANGE': CHANGE,
        'TRAVEL': TRAVEL,
        'RECRUIT': RECRUIT,
        'BLOCK': BLOCK,
        'DISTANCE': DISTANCE,
        'DICE': DICE,
        "REPLACE": REPLACE,
        'FILL': FILL,
        'LISTGROUP': LISTGROUP,
    }
    
    def recursive(string, debug=False):
        if debug:
            print(string)
        
        #Deal with Brackets
        while "(" in string:
            start = string.find("(")
            end = string.find(")")
            substr = string[start:end + 1]
            while substr.count("(") != substr.count(")"):
                end = string[end +1:].find(")") + end+1 
                substr = string[start:end+1]
            
            formula = string[start+1:end]
            if debug:
                print("entering subshell")
            formula = recursive(formula, debug)
            if debug:
                print(formula)
                print("exiting subshell")
            formula = "{"+formula+"}"
            formula = formula.replace(" ", "")
            string = string[:start] + formula + string[end+1:]
            
        #parse remaining strings.       
        
        list_ = re.split(" ", string)
        if debug:
            print(list_)
        for index in range(len(list_)):
            check = list_[index]
            try:
                keyword[check](list_, index)
                if debug:
                    print(list_)
                continue    
            except KeyError:
                continue
            except IndexError:
                print("Invalid formula", string)
                raise

        #prevents indentation errors
        while "" in list_:
            list_.remove("")
        
        return " ".join(list_)
    
    final = recursive(string, debug)
    while "{" in final:
        final = final.replace("{", "(")
    while "}" in final:
        final = final.replace("}", ")")
    
    return final

