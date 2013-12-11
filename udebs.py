
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
        self.django = False
        self.compile = True
        self.hex = False
        self.name = 'Unknown'
        self.logging = True
        self.lists = ['group', 'effect', 'require']
        self.stats = ['increment']
        self.strings = []
        self.slist = {}
        self.rlist = []
        
        self.time = 0
        self.delay = []
        self.map = []
        self.log = []
        
        #only used for custom effects.
        self.data = {}
        self.variables = {}
                
        #revert function broken
#        self.state = []        
#        self.revert = 0

        super(instance, self).__init__(*args, **kwargs)
        
    #---------------------------------------------------
    #                 Get Functions                    -
    #---------------------------------------------------
    
    def getObject(self, string='', lst=False):
        if string:
            return self.data[string]
        else:
            return self.data
            
    def getStat(self, target, stat):
        #This function is a bottleneck
        
        target = self.testTarget(target)
        if stat == 'group':
            return getattr(target, stat)
        
        classes = target.group
        
        def recursive_list(classes):
            for lst in self.rlist:
                for cls in classes:
                    yield getattr(self.getObject(cls), lst)
        
        if stat in self.strings:
            for cls in itertools.chain(classes, recursive_list(classes)):
                base = getattr(self.getObject(cls), stat)
                if base != "":
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
            raise Exception("Unknown Stat in GetStat")
    
    def getLog(self):
        test = copy.deepcopy(self.log)
        self.controlLog(clear=True)
        return test
        
    def getMap(self, target):
        if target[0] < 0 or target[1] < 0:
            return False
        try:
            return self.map[target[1]][target[0]]   
        except IndexError:
            return False
    
    def getDistance(self, one1, two1, method):
        
        one1 = self.testTarget(one1)
        two1 = self.testTarget(two1)
        
        if False in [one1.loc, two1.loc]:
            return float("inf")  
        
        one = (one1.loc[0], one1.loc[1], -(one1.loc[0] + one1.loc[1]))
        two = (two1.loc[0], two1.loc[1], -(two1.loc[0] + two1.loc[1]))
  
        if method == 'x':
            return abs(one[0] - two[0])
        elif method == 'y':
            return abs(one[1] - two[1])
        elif method == 'z':
            return abs(one[2] - two[2])
        elif method == 'hex':
            return (abs(one[0] - two[0]) + abs(one[1] - two[1]) + abs(one[2] - two[2]))/2
        elif method == 'p1':
            return abs(one[0] - two[0]) + abs(one[1] - two[1])
        elif method == 'p2':
            return math.sqrt(math.pow(one[0] - two[0], 2) + math.pow(one[1] - two[1], 2))
        elif method == 'pinf':
          return max(abs(one[0] - two[0]), abs(one[1] - two[1]))
        else:
            if method in self.getObject():
                return self.getFill(one1, method, two1, True)
            else:
                print("Unknown distance metric")
                raise TypeError             
            
        #starting at center gets all attached nodes that move can cast on.
    def getFill(self, center, move='empty', target=float("inf"), returnd=False):        
        
        hexmap = self.hex
        center = self.testTarget(center)
        if type(target) in [int, float]:
            distance = target
            target = False
        else:
            target = self.testTarget(target).loc
            distance = float('inf')
        
        if distance == 0 or center.loc == False:
            return []
        
        def adjacent(location, hexmap):
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
            
        def recursive(future, past, yes, counter):
            new = []
            for node in future:
                if node in past:
                    continue
                elif not self.getMap(node):
                    past.append(node)
                    continue
                else:
                    past.append(node)
                    env = self.createTarget(center, node, move)
                    if self.testRequire(env) == True:
                        new.append(node)
            
            yes.extend(new)
            counter +=1
            if len(new) == 0 or counter >= distance or target in yes:
                if returnd:
                    return counter
                else:
                    return yes
            else:
                search = []
                for node in new:
                    search.append(adjacent(node, hexmap))
                return recursive(itertools.chain.from_iterable(search), past, yes, counter)
        
        test = recursive(adjacent(center.loc, hexmap), [], [], 0)
        if type(test) is not int:
            random.shuffle(test)
        return test
    
    #returns all objects belonging to group.
    def getGroup(self, group):
        found = []
        for unit in self.getObject():
            if group in self.getStat(unit, 'group'):
                found.append(unit)
        return found
        
    #returns combined stat for all elements in a list
    def getListStat(self, target, lst, stat):
        target = self.testTarget(target)
        start = self.getStat(target.name, lst)
        
        found = []
        for element in start:
            item = self.getStat(element, stat)
            if type(item) is list:
                for entry in item:
                    found.append(entry)
            else:
                found.append(item)
        return sum(found)
        
    #returns first element in list contained in group    
    def getListGroup(self, target, lst, group):
        target = self.testTarget(target)
        group = self.testTarget(group)
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
        
        def checkdelay():
            while True:
                check = True
                for delay in copy.copy(self.delay):
                    if delay["DELAY"] <= 0:
                        check = False
                        env = createTarget(delay["CASTER"], 
                                           delay["target"],
                                           delay["MOVE"])
                        controlEffect(env, delay['STRING'])
                        self.delay.remove(delay)
                if check:
                    self.controlLog()
                    return
        
        if time != 0:
            for i in range(time):
                self.time +=1
                self.controlLog('Env time is now', self.time)
                if 'tick' in self.getObject():
                    tick = self.getObject('tick')
                    env = self.createTarget("empty", 'empty', "tick")
                    if self.testRequire(env) == True:
                        self.controlEffect(env)
                for delay in self.delay:
                    delay["DELAY"] -=1
                checkdelay()
        else:
            checkdelay()
            
        
#        if time != 0:
#            #Broken, make sure STATE isn't longer then revert.
#            #while len(STATE) >= self.env["REVERT"]:
#            #    STATE.pop(0)
#            self.state.append(copy.deepcopy(self.object))
        if self.django:
          self.save()
        return True

    #not maintained, and probobly broken.
#    def controlRevert(self, state=1):
#        if type(state) is not int or state <= 0:
#            raise Exception("controlRevert only accepts int > 0 as argument")
#        if len(self.state) < state:
#            self.controlLog("Revert failed. Choosen state not available.")
#            return
#    
#        index = len(self.state) - state
#        self.getObject().update(copy.deepcopy(self.state[index]))
#        for count in range(index+1, index):
#            del self.state[count]
#        self.controlLog("revert successful")
#        return
    
    def controlLog(self, *args, clear=False):
        
        
        if not self.logging:
            return True
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
        if isinstance(target, list):
            for trgt in target:
                self.controlStat(trgt, stat, increment)
            return True

        target = self.testTarget(target)
        increment = int(increment)
        if target.name == 'empty' or increment ==0:
            return False
        
        newValue = getattr(target, stat) + increment
        setattr(target, stat, newValue)
        self.controlLog(target.name, stat, "changed by", increment, "is now", self.getStat(target, stat))
        if self.django:
            target.save()
        return True

    def controlString(self, target, strg, new):
        if isinstance(target, list):
            for trgt in target:
                self.controlString(trgt, strg, new)
            return True
        
        target = self.testTarget(target)
        if target == 'empty' or strg == "ID":
            self.controlLog("String update failed")
            return False
        if new == 'False':
            new = ''    
        
        setattr(target, strg, new)
        
        self.controlLog(target.name, strg, "is now", new)
        if self.django:
            target.save()
        return True
        
    def controlList(self, target, lst, entry, method='add'):
        if isinstance(target, list):
            for trgt in target:
                self.controlList(trgt, lst, entry, method)
            return True
        
        target = self.testTarget(target)
        
        if target.name == 'empty' or entry == 'empty':
            return False
        
        if method == 'remove':
            if entry in getattr(target, lst):
                getattr(target, lst).remove(entry)
                self.controlLog(entry, "removed from", target.name, lst)
                return True
            return False
        
        if lst in self.slist.keys():
            if self.slist[lst] in self.getStat(entry, "group"):
                env = self.createTarget('empty', target, entry)
                check = self.testRequire(env)
                if check != True:  
                    self.controlLog(target.name, "special list", lst, entry, 
                                    "failed because", check)
                    return False
            else:
                self.controlLog(target.name, "special list", lst, entry, 
                                "failed because invalid type")
                return False

        getattr(target, lst).append(entry)
        
        self.controlLog(entry, "added to", target.name, lst)
        if self.django:
            target.save()
        return True
    
    def controlRecruit(self, clone, position=None, tick=False):
        if isinstance(clone, list):
            for element in position:
                self.controlRecruit(clone, element)
            return
        
        clone = self.testTarget(clone)
        if clone.name == 'empty':
            self.controlLog("can't clone empty.")
            return False
       
        new_unit =copy.deepcopy(clone)
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
        
        caster = self.testTarget(caster)
        target = self.testTarget(target)    
        
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
         
    def controlDelay(caster, target, move, call_string, delay):
        if int(delay) < 0:
            raise
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

    def controlMove(self, caster, target , move):
        if isinstance(move, list):
            if len(move) == 0:
                print("empty list in controlMove")
            for entry in move:
                self.controlMove(caster,target, entry, delay)
            return True
        
        if isinstance(target, list):
            if len(target) == 0:
                print("empty list in controlMove")
            for entry in target:
                self.controlMove(caster, entry, move, delay)
            return True
        
        env = self.createTarget(caster, target, move)
        check = self.testRequire(env)
        
        if check != True:
            self.controlLog(env['caster'].name, "cast", 
                            env['move'].name,"on", 
                            env['target'].name, "failed because", 
                            check)
            return False
        self.controlLog(env['caster'].name, "uses", env['move'].name,
                        "on", env['target'].name)
        self.controlEffect(env)
        return True
        
    def controlEffect(self, env, single=False):
        
        def decode(effect, env):
            if type(effect) is script:
                raw = effect.raw
                inter = effect.interpret
                scode = effect.code
            else:
                raw = effect
                inter = interpret(effect)
                scode = inter
            try:
                exec(scode, env)
            except:
                print("invalid (", raw, ") interpreted as (", inter,
                      ")")
                raise  
        
        if single:
            decode(single, env)
        else:
            for effect in self.getStat(env['move'], 'effect'):
                decode(single, env)
        return True

    #---------------------------------------------------
    #                 Other Functions                  -
    #---------------------------------------------------
    
    def testTarget(self, target):
        #This function is a bottleneck
        if isinstance(target):
            return target
        elif isinstance(target, basestring):
            return self.getObject(target)
        elif isinstance(target, tuple):
            name = self.getMap(target)
            if name:
                if name == 'empty':
                    target_entity = entity(self)
                    target_entity.loc = target
                    return target_entity
                else:
                    return self.getObject(name)
            raise KeyError
        else:
            print(target)
            raise TypeError
                
    #Make this similar to getFill, not just empty, arbitrary requires.
    def testBlock(self, start, finish, path ):
        check = []
        
        #accepted paths (x, y, diag)
        
        start = self.testTarget(start).loc
        finish = self.testTarget(finish).loc
 
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
            recent = changeX( start)
            changeY( recent )
                
        elif path == "y":
            recent = changeY( start)
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

    def testRequire(self, env):
        for require in self.getStat(env['move'], 'require'):
            if type(require) is script:
                raw = require.raw
                inter = require.interpret
                scode = require.code
            else:
                raw = effect
                inter = interpret(effect)
                scode = inter
            try:
                if not eval(scode, env):
                    return raw
            except:
                print("invalid (", raw, ") interpreted as (", inter, ")")
                raise
        return True
    
    def createTarget(self, caster, target, move, add={}):
        
        caster = self.testTarget(caster)
        target = self.testTarget(target)
        move = self.testTarget(move)
        
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
        return "entity: "+self.name
            
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
    def __init__(self, effect, env=instance(), require=False):
        if require:
            command = 'eval'
        else:
            command = 'exec'
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
def battleStart(xml_file, field=instance(), obj=entity()):
    
    try:
        tree = ElementTree.parse(xml_file)
    except IOError as inst:
        print( "battleStart Error:", inst)
        sys.exit()
    
    #ENV
    root = tree.getroot()
    
    config = root.find("config")
    if config is not None:
        
        out = config.findtext("name")
        if out is not None:
            print("INITIALIZING", out, "\n")
            field.name = out
        
        django = config.findtext('django')
        if django is not None:
            field.django = eval(django)
        
        comp = config.findtext("compile")
        if comp is not None:
            field.compile = eval(comp)
        
        logichex = config.findtext("hex")
        if logichex is not None:
            field.hex = eval(logichex)
        
#        revert = config.findtext("revert")
#        if revert is not None:
#            field.revert = int(revert)
            
        logging = config.findtext('logging')
        if logging is not None:
            field.logging = eval(logging)
    
    #fix due to bug with django
    field.strings = []
    field.stats = [u'increment']
    field.lists = [u'group', u'effect', u'require']
    field.rlist = []
    field.slist = {}
    field.delay = []
    
    defs = root.find("definitions")    
    def_stats = defs.find("stats")
    if def_stats is not None:
        for stat in def_stats:
            field.stats.append(stat.tag)
            
    def_lists = defs.find("lists")
    if def_lists is not None:
        for stat in def_lists:
            field.lists.append(stat.tag)
            if stat.get('rlist') == "rlist":
                field.rlist.append(stat.tag)
            if stat.get('slist') is not None:
                field.slist[stat.tag] = stat.get('slist')
                          
    def_strings = defs.find("strings")
    if def_strings is not None:
        for stat in def_strings:
            field.strings.append(stat.tag)
        
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
            if elem is not None:
                setattr(new_entity, stat, int(elem.text))
            else:
                setattr(new_entity, stat, 0)
                
        for string in field.strings:
            value = item.findtext(string)
            if value is not None:
                setattr(new_entity, string, value)
            else:
                setattr(new_entity, string, '')
                
        for lst in field.lists:
            new_list = []
            if lst == 'group':
                new_list.append(new_entity.name)
            find_list = item.find(lst)
            if find_list is not None:
                for value in find_list:
                    if field.compile:
                        if lst == 'require':
                            new_list.append(script(value.text, field, True))
                            continue
                        elif lst == 'effect':
                            new_list.append(script(value.text, field))
                            continue
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
    if string == None:
        return ''
    
    #utility
    def erase(list_, index, range_):
        for i in range_:
            list_[i+index] = ""
        return list_
    
    def call(function, *args, env=True):
        if env:
            value = "self."+function+"{"
        else:
            value = function+"{"
        for arg in args:
            if arg[0] == "'":
                if arg[-1] != "'":
                    arg = arg + "'"  
            value = value+arg+","
        value = value + ")"
        return value
    
    #keywords
    def DELAY(list_, i):
        string = list_[i+1]
        delay = list_[i+2]
        list_[i] = call("controlDelay", 'caster', 'target', 'move', "'"+string, delay)
        erase(list_, i, (1,2))
    
    #targeting
    def CLASS(list_, i):
        target = list_[i + 2]
        grtype = list_[i + 1]
        list_[i] = call('getListGroup', target, 'group', grtype)
        erase(list_, i, (1,2))
        
    def ALL(list_, i):
        group = list_[i +1]
        list_[i] = call('getGroup', group)
        erase(list_, i, (1,))
        
    def FILL(list_, i):
        target = list_[i + 1]
        move = list_[i + 2]
        list_[i] = call('getFill', target, move)
        erase(list_, i, (1,2))
        
    #controlMove
    def ACTIVATE(list_, i):
        target = list_[i +1]
        slist_ = list_[i +2]
        group = list_[i +3]
        
        if i == 0:
            caster = "caster" 
        else:
            caster= list_[i-1]
            list_[i-1] = ""
            
        move = call('getListGroup', caster, slist_, group)
        list_[i] = call('controlMove', caster, target, move)
        erase(list_, i, (1,2,3))
        
    def CAST(list_, i):
        target = list_[i + 1]
        move = list_[i + 2]
        
        if i == 0:
            caster = "caster"
        else:
            caster = list_[i-1]
            list_[i-1] = ""
            
        list_[i] = call('controlMove', caster, target, move)
        erase(list_, i, (1,2))
        
    #controlList
    def GETS(list_, i):
        target = list_[i +1]
        slist = list_[i +2]
        move = list_[i +3]
        list_[i] = call('controlList', target, slist, move, 'add')
        erase(list_, i, (1,2,3))
    
    def LOSES(list_, i):
        target = list_[i +1]
        slist = list_[i +2]
        move = list_[i +3]
        list_[i] = call('controlList', target, slist, move, 'remove')
        erase(list_, i, (1,2,3))
    
    #controlStat
    def CHANGE(list_, i):
        target = list_[i +1]
        stat = list_[i +2]
        amount = list_[i +3]
        list_[i] = call('controlStat', target, stat, amount)
        erase(list_, i, (1,2,3))
        
    #controlString
    def REPLACE(list_, i):
        target = list_[i +1]
        stat = list_[i +2]
        change = list_[i +3]
        list_[i] = call('controlString', target, stat, change)
        erase(list_, i, (1,2,3))
    
    #control Recruit
    def RECRUIT(list_, i):
        target = list_[i +1]
        location = list_[i +2]
        list_[i] = call('controlRecruit', target, location)
        erase(list_, i, (1,2))
        
    #control Travel
    def TRAVEL(list_, i):
        location = list_[i +1]
        if i == 0:
            caster = "caster"
        else:
            caster = list_[i-1]
            list_[i-1] = ""
        list_[i] = call('controlTravel', caster, location)
        erase(list_, i, (1,))
    
    #instant requires
    def BLOCK(list_, i):
        command = list_[i + 1]
        list_[i] = call('testBlock', 'caster', 'target', command)
        erase(list_, i, (1,))
    
    #might change for arbitrary target
    def ONBOARD(list_, i):
        list_[i] = call('getLocation', 'target.loc')
        
    def ISUNIT(list_, i):
        list_[i] = call('getMap', 'target.name')
        
    #this one feels like arbitray target distance might be nice
    def DISTANCE(list_, i):
        dtype = list_[i + 1]
        list_[i] = call('getDistance', 'target', dtype)
        erase(list_, i, (1,))
        
    def DICE(list_, i):
        value = list_[i +1]
        list_[i] = call('randint', "0", value, env=False)
        erase(list_, i, (1,))
    
    #getStat
    def STAT(list_, i):
        target = list_[i +1]
        stat = list_[i +2]
        list_[i] = call("getStat", target, stat)
        erase(list_, i, (1,2))
    
    def LISTSTAT(list_, i):
        target = list_[i +1]
        slist = list_[i +2]
        stat = list_[i +3]
        list_[i] = call('getListStat', target, slist, stat)
        erase(list_, i, (1,2,3))
    
    #shortcuts
    
    keyword = {
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
    }
    
    if debug:
        print(string)
    
    def recursive(string, debug=False):
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
                print("exiting subshell")
            formula = "{"+formula+"}"
            formula = formula.replace(" ", "")
            string = string[:start] + formula + string[end+1:]
            
        #parse remaining strings.
        list_ = re.split(" ", string)
        for index in range(len(list_)):
            check = list_[index]
            try:
                keyword[check](list_, index)
                continue
            except KeyError:
                if len(check) > 0:
                    if check[0] == "'":
                        if check[-1] != "'":
                            list_[index] = check + "'"  
                continue
            except IndexError:
                print("Keyword error, can't parse", string)
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

