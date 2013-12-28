
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
        
        #var
        self.time = 0
        self.delay = []
        self.map = []
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
            
    def getStat(self, target, stat):
        """Returns stat of entity object plus linked group objects.
        
        target - Entity selector.
        stat - Stat defined in env.lists, env.stats, or env.strings
        
        """ 
        #This function is a bottleneck
        target = self.testTarget(target, True)
        
        if stat == 'group':
            return target.group
        
        classes = target.group
        
        def recursive_list(classes):
            for lst in self.rlist:
                for cls in classes:
                    for item in getattr(self.getObject(cls), lst):
                        yield item
                    
        if stat in self.strings:
            for cls in itertools.chain(classes, recursive_list(classes)):
                base = getattr(self.getObject(cls), stat)
                if base:
                    return base
            return ""
        
        elif stat in self.stats:
            count = 0
            for cls in classes:    
                count +=getattr(self.getObject(cls), stat)
            for item in recursive_list(classes):
                count +=self.getStat(item, stat)
            return count
            
        elif stat in self.lists:    
            lst = []
            for cls in classes:
                lst.extend(getattr(self.getObject(cls), stat))     
            for item in recursive_list(classes):
                lst.extend(self.getStat(item, stat))
            return lst
        else:
            raise UndefinedStatError(stat)
    
    def getLog(self):
        """Returns list of log entries made since last call."""
        test = copy.deepcopy(self.log)
        self.controlLog(clear=True)
        return test
        
    def getMap(self, target):
        """Returns first location for string in env.map."""
        if target[0] < 0 or target[1] < 0:
            return False
        try:
            return self.map[target[1]][target[0]]   
        except IndexError:
            return False
            
    def getLocation(self, target):
        """Returns location of entity selector."""
        return self.testTarget(target, True).loc
    
    def getDistance(self, one, two, method):
        """Returns distance between two entity selectors.
        
        one - Entity selector
        two - Entity selector
        method - Distance metric to used
        
        """
        #Note: Dictonary switch method doubles this functions run time.
        
        one = self.testTarget(one, True).loc
        two = self.testTarget(two, True).loc
        
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
            return self.getFill(one, method, two, True)
        else:
            print("Unknown distance metric")
            raise TypeError             
            
        #starting at center gets all attached nodes that move can cast on.
    def getFill(self, center, move='empty', target=float("inf"), returnd=False):        
        """Returns list of locations castable by move and connected to center.
        
        Note: target and returnd wrapped by getDistance. Internal use only.
        
        center - Entity selector (Begining of search.)
        move - Entity selector (Move to use in testRequire.)
        target - Entity selector (Stop when selector is reached.)
        returnd - Boolean (return number of iterations instead of list of locations)
        
        """
        
        hexmap = self.hex
        center = self.testTarget(center, True)
        if isinstance(target, (int, float)):
            distance = target
            target = False
        else:
            target = self.testTarget(target, True).loc
            distance = float('inf')
        
        if distance == 0 or center.loc == False:
            return []
        
        def adjacent(location):
            x = location[0]
            y = location[1]
            yield (x -1, y)
            yield (x, y +1)
            yield (x +1, y)
            yield (x, y -1)
            if hexmap:
                yield (x -1, y +1)
                yield (x +1, y -1)
            if hexmap == "diag":
                yield (x +1, y +1)
                yield (x -1, y -1)
            return
            
        def recursive(check, searched, found, counter):
            new = set()
            for node in check:
                if not self.getMap(node):
                    continue
                env = self.createTarget(center, node, move)
                if self.testRequire(env) == True:
                    new.add(node)
                    
            found.update(new)
            searched.update(check)
            counter +=1
            if len(new) == 0 or counter >= distance or target in found:
                if returnd:
                    return counter
                return found
            
            next = set().union(*[adjacent(node) for node in new])
            next.difference_update(searched)
            return recursive(next, searched, found, counter)
        
        test = recursive(adjacent(center.loc), set(), set(), 0)
        if isinstance(test, set):
            test = list(test)
            random.shuffle(test)
        return test
    
    def getGroup(self, group, inc_self=True):
        """Return all objects belonging to group."""
        group = self.testTarget(group, True).name
        
        found = []
        for unit in self.getObject():
            if group in self.getStat(unit, 'group'):
                found.append(unit)
        if not inc_self:
            found.remove(group)
        return found
        
    #returns combined stat for all elements in a list
    def getListStat(self, target, lst, stat):
        """Returns combination of all stats for objects in a units list.
        
        target - Entity selector
        lst - String representing list to check.
        stat - String representing defined stat.
        
        """
        target = self.testTarget(target, True)
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
        target = self.testTarget(target, True)
        group = self.testTarget(group, True)
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
        targets = self.testTarget(targets)
        increment = int(increment)
        if increment == 0:
            return False
        
        for target in targets:
            if target.name == 'empty':
                continue
            
            newValue = getattr(target, stat) + increment
            setattr(target, stat, newValue)
            if stat is not 'increment':
                self.controlLog(target.name, stat, "changed by", increment, "is now", self.getStat(target, stat))
            if self.django:
                target.save()
        
        return True

    def controlString(self, targets, strg, new):
        """Changes stored stat of target by increment.
        
        targets - Multiple Entity selector
        stat - Defined statistic to change
        increment - String to change stat to.
        
        """
        targets = self.testTarget(targets)   
        
        for target in targets:
            if target.name == 'empty':
                continue
            
            setattr(target, strg, new)
            self.controlLog(target.name, strg, "is now", new)
            if self.django:
                target.save()
        
        return True
        
    def controlList(self, targets, lst, entry, method='add'):
        """Adds or removes items in Entity list.
        
        targets - Multiple Entity selector
        lst - Defined list to change.
        entry - String to add or remove.
        increment - String to add to or remove from list.
        
        """
        flag = False
        targets = self.testTarget(targets)
        if isinstance(entry, entity):
            entry = entry.name
        
        for target in targets:
            if target.name == 'empty':
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
        positions=self.testTarget(positions)
        clone = self.testTarget(clone, True)
        new_unit = None
        
        if clone.name == 'empty':
            self.controlLog("can't clone empty.")
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
        
        caster = self.testTarget(caster, True)
        target = self.testTarget(target, True)    
        
        #check if targetLoc is valid
        if not target.loc:
            self.controlLog("Warning", caster.name, "trying to move off the stage.")
            return False
        
        #move caster
        if caster.loc:
            self.map[caster.loc[1]][caster.loc[0]] = 'empty'
        self.map[target.loc[1]][target.loc[0]] = caster.name
        
        if target.name != 'empty':
            target.update(self)
        caster.update(self)
   
        #control Logs
        if caster.name != 'empty':
            self.controlLog(caster.name, "has moved to", caster.loc)
            if self.django:
                caster.save()
        if target.name != 'empty' and target.name != caster.name:
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
        caster = self.testTarget(caster, True)
        targets = self.testTarget(targets)
        moves = self.testTarget(moves)
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
    #                 Other Functions                  -
    #---------------------------------------------------
    
    def testTarget(self, target, single=False):
        """Returns entity object based on given selector.
        
        target - Any entity selector.
        single - Boolean, guerenteed to only return one object if true.
        
        """
        ttype = type(target)
        if ttype is entity:
            return target
        elif ttype is str:
            return self.getObject(target)
        elif ttype is tuple:
            name = self.getMap(target)
            if name not in {'empty', False}:
                return self.getObject(name)
            target_entity = entity(self)
            if name:
                target_entity.loc = target
            return target_entity
        elif ttype is list:
            if single:
                return self.testTarget(target[0], True)
            else:
                return [self.testTarget(unit, True) for unit in target]
        elif ttype is bool:
            return self.getObject('empty')
        else:
            raise UndefinedSelectorError(target)
                
    #Make this similar to getFill, not just empty, arbitrary requires.
    def testBlock(self, start, finish, path ):
        check = []
        
        #accepted paths (x, y, diag)
        
        start = self.testTarget(start, True).loc
        finish = self.testTarget(finish, True).loc
 
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
        
        caster = self.testTarget(caster, True)
        target = self.testTarget(target, True)
        move = self.testTarget(move, True)
        
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
    def __init__(self, field=instance(), *args, **kwargs):
        self.name = 'empty'
        self.loc = False
        if issubclass(type(field), instance):
            for stat in field.stats:
                setattr(self, stat, 0)
            for lists in field.lists:
                setattr(self, lists, [])
            for string in field.strings:
                setattr(self, string, u'')
            super(entity, self).__init__(*args, **kwargs)
        else:
            super(entity, self).__init__(field, *args, **kwargs)
    
    def __repr__(self):
        return "<entity: "+self.name+">"
    
    def __iter__(self):
        yield self
            
    def update(self, env=instance()):
        if self.name == "empty":
            self.loc = False     
        
        y = 0
        for column in env.map:
            try:
                x = column.index(self.name)
                self.loc = (x,y)
                return
            except ValueError:
                y +=1
                continue
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

    
#---------------------------------------------------
#                      XML parser                  -
#---------------------------------------------------

##creates an xml file from instance object.
##This code is untested
#def battleWrite(env, location):
#    e = ElementTree
#    root = e.Element('udebs')
#    
#    #ENVdef battleWrite
#    definitions = e.SubElement(root, 'definitions')
#    for dtype in [STATS, LISTS, STRINGS]:
#        middle = e.SubElement(definitions, dtype)
#        for item in env.env[dtype]:
#            if item in [GROUP, EFFECT, REQUIRE, TYPE, ID]:
#                continue
#            final = e.SubElement(middle, item)
#            if item in env.env['rlist']:
#                final.attrib['rlist'] = 'rlist'
#            if item in env.env['slist']:
#                final.attrib['slist'] = env.env['slist'][item]
#    
#    config = e.SubElement(root, 'config')
#    if env.env[NAME] != 'Unknown':
#        name = e.SubElement(config, 'name')
#        name.text = env.env[NAME]
#    if env.env[HEX] != False:
#        hexmap = e.SubElement(config, 'hex')
#        hexmap.text = env.env[HEX]
#    if env.env[REVERT] != 0:
#        revert = e.SubElement(config, 'revert')
#        revert.text = str(env.env[REVERT])
#    
#    #VAR
#    #map
#    mapt = e.SubElement(root, 'map')
#    for row in env.var[MAP]:
#        middle = e.SubElement(mapt, 'row')
#        text = ''
#        for item in row:
#            text = text + ', ' + item
#        middle.text = text[2:]
#    #needs saving (time, delay)    
#    
#    var = e.SubElement(root, 'var')
#    if env.var[TIME] != 0:
#        time = e.SubElement(var, 'time')
#        time.text = str(env.var[TIME])
#    if env.var[DELAY] != []:
#        delay = e.SubElement(var, 'delay')
#        for item in env.var[DELAY]:
#            node = e.SubElement(delay, 'item')
#            node.attrib.update(item)
#            for key, value in node.attrib.items():
#                if type(value) is targetting:
#                    if value.loc:
#                        node.attrib[key] = str(value.loc)
#                    else:
#                        node.attrib[key] = str(value.name)
#                else:
#                    node.attrib[key] = str(value)
#            
#    #scripts
#    scripts = e.SubElement(root, 'scripts')
#    for script in env.scripts:
#        middle = e.SubElement(scripts, script)
#        for item in env.scripts[script]:
#            final = e.SubElement(middle, 'item')
#            final.text = item.raw
#    
#    #entities
#    entities = e.SubElement(root, 'entities')
#    units = e.SubElement(root, 'units')
#    for entry, value in env.object.items():
#        if entry in env.var[UNITS]:
#            entity = e.SubElement(units, value[ID])
#        else:    
#            entity = e.SubElement(entities, value[ID])
#        
#        for label, value1 in value.items():
#            if value1 in [0, '', list()]:
#                continue
#            elif label in env.env[LISTS]:
#                slist = e.SubElement(entity, label)
#                for item in value1:
#                    temp = e.SubElement(slist, 'item')
#                    if label in [EFFECT, REQUIRE]:
#                        temp.text = item.raw
#                    else:
#                        temp.text = item
#            elif label in env.env[STRINGS] + env.env[STATS]:
#                item = e.SubElement(entity, label)
#                item.text = str(value1)
#            
#    #pretty print this thing
#    def indent(elem, level=0):
#        i = "\n" + level*"  "
#        if len(elem):
#            if not elem.text or not elem.text.strip():
#                elem.text = i + "  "
#            if not elem.tail or not elem.tail.strip():
#                elem.tail = i
#            for elem in elem:
#                indent(elem, level+1)
#            if not elem.tail or not elem.tail.strip():
#                elem.tail = i
#        else:
#            if level and (not elem.tail or not elem.tail.strip()):
#                elem.tail = i    
#    
#    indent(root)
#    tree = e.ElementTree(root)
#    tree.write(location)
#    
#    return True

#Creates and instance object from xml file.
def battleStart(xml_file, env=instance, ind=entity):
    
    try:
        tree = ElementTree.parse(xml_file)
    except IOError as inst:
        print("battleStart Error:", inst)
        sys.exit()
    
    #ENV
    field = env()
    root = tree.getroot()
    
    config = root.find("config")
    if config is not None:
        
        name = config.findtext("name")
        if name is not None:
            print("INITIALIZING", name, "\n")
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
    
    #fix due to bug with django
    field.strings = set()
    field.stats = {'increment'}
    field.lists = {'group', 'effect', 'require'}
    field.rlist = set()
    field.slist = {}
    field.delay = []
    
    defs = root.find("definitions")    
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
        
    #VAR
    field_map = root.find("map")
    if field_map is not None:
        dim_map = field_map.find("dim")
        if dim_map is not None:
            x = int(dim_map.find('x').text)
            y = int(dim_map.find('y').text)
            for element in range(y):
                field.map.append(['empty' for i in range(x)])
        else:
            for row in field_map:
                field.map.append(re.split("\W*,\W*", row.text))
    
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
                    if key in ['CASTER', 'TARGET']:
                        try:
                            index = item.attrib[key].index(',')
                            x = int(item.attrib[key][1:index])
                            y = int(item.attrib[key][index+2:-1])
                            item.attrib[key] = (x,y)
                        except ValueError:
                            pass    
                field.delay.append(item.attrib)
    
    if field.django:
        field.save()
    
    obj = ind(field)
    
    #Set empty 
    empty = copy.deepcopy(obj)
    empty.group.append('empty')
    empty.record(field)
    
    #Create all entity type objects.
    def addObject(item):
        new_entity = copy.deepcopy(obj)
        new_entity.name = item.tag
        
        for stat in field.stats:
            elem = item.find(stat)
            add_attr = int(elem.text) if elem is not None else 0
            setattr(new_entity, stat, add_attr)
                
        for string in field.strings:
            value = item.findtext(string)
            add_attr = value if value is not None else ""
            setattr(new_entity, string, add_attr)
            
        for lst in field.lists:
            new_list = []
            if lst == 'group':
                new_list.append(new_entity.name)
            
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
        
        new_entity.update()
        new_entity.record(field)
        
        return new_entity
                        
    entities = root.find("entities")
    if entities is not None:
        for item in entities:
            new_entity = addObject(item)
    
    if 'tick' not in field.getObject():
        print("warning, no tick is defined.")             
    
    #VAR[STATE].append(copy.deepcopy(OBJECT))
     
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

