from udebs import interpret
import random
import math
import copy
import itertools
import collections
import sys

#Loads functions from keywords.json into the interpreter.
interpret.importSystemModule("udebs", {"self": None})

#---------------------------------------------------
#                 Main Class                       -
#---------------------------------------------------

class Instance(collections.MutableMapping):
    """
    Main instance class that represents the state space of the entire game.

    Note on naming convention:

    All methods begining with 'get' return information about the game's state
    space and are not allowed to change the state itself.

    All methods beggining with 'control' manage some aspect of the state space
    and return true if changes were (probobaly) made and false otherwise.

    Functions marked below as public are simply function recomended for use by
    users. All other functions are fair game, but their usage is either tailored
    to the Udebs scripting language or likely to change in the future.

    Public Functions.

    getState( target, string ) Gets the associated stat from target.
    getDistance( target, target, string ) Gets distance between two targets.
    getLog() Gets all currently saved log entries.
    getRevert( int ) Gets previous recorded game states.




    """
    def __init__(self):
        #config
        self.compile = True
        self.hex = False
        self.name = 'Unknown'
        self.logging = True
        self.revert = 1
        self.version = 1
        self.inheritance = True

        #definitions
        self.lists = {'group', 'effect', 'require'}
        self.stats = {'increment'}
        self.strings = set()
        #rlist and rmap are flags that indicate objects entities should inherit from.
        self.rlist = set()
        self.rmap = set()

        #var
        self.time = 0
        self.delay = []
        self.map = {}
        self.log = []
        self.state = []

        #Other
        self.rand = random.Random()

        #internal use only.
        self._data = {}

    def __eq__(self, other):
        if not isinstance(other, Instance):
            return False

        check = [
            self.compile == other.compile,
            self.hex == other.hex,
            self.name == other.name,
            self.logging == other.logging,
            self.revert == other.revert,
            self.version == other.version,
            self.inheritance == other.inheritance,

            #definitions
            self.lists == other.lists,
            self.stats == other.stats,
            self.strings == other.strings,
            self.rlist == other.rlist,
            self.rmap == other.rmap,

            #var
            self.time == other.time,
            self.delay == other.delay,
            self.map == other.map,
            self.log == other.log,
            len(self) == len(other),
        ]
        #Note: self.state is specifically ignored.
        check.extend(self[entity] == other[entity] for entity in self)
        return all(check)

    def __deepcopy__(self, memo):
        new = type(self)()
        for k,v in self.__dict__.items():
            if k == "state":
                setattr(new, k, [])
            else:
                setattr(new, k, copy.deepcopy(v, memo))

        for entity in new:
            new[entity].field = new

        for map_ in new.map:
            new.map[map_].field = new

        return new

    def __getitem__(self, key):
        if key == "bump":
            return self._data["empty"]
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value

    def __delitem__(self, key):
        del self._data[key]

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        return iter(self._data)

    def __contains__(self, item):
        return item in self._data

    #---------------------------------------------------
    #                 Get Functions                    -
    #---------------------------------------------------
    #Primary get functions.
    def getTarget(self, target, multi=False):
        """Returns entity object based on given selector.

        target - Any entity selector.
        multi - Boolean, allows lists of targets.

        """
        if target == False:
            return self['empty']

        ttype = type(target)

        #Already entity return self.
        if ttype is Entity:
            return target

        #If string, return associated entity.
        elif ttype is str:
            try:
                return self[target]
            except KeyError:
                raise UndefinedSelectorError(target, "entity")

        #If tuple, this is a location.
        elif ttype is tuple:
            map_ = self.getMap(target)
            try:
                unit = self[map_[target]]
            except IndexError:
                unit = self[map_.empty]

            if unit.immutable:
                unit = copy.deepcopy(unit)
                unit.update(target)

            return unit

        #If type is a list individually check each element.
        elif ttype is list:
            value = map(self.getTarget, target)
            if multi:
                return list(value)
            return next(value)

        raise UndefinedSelectorError(target, "entity")

    def getStat(self, target, stat, maps=True):
        """Returns stat of entity object plus linked group objects.

        target - Entity selector.
        stat - Stat defined in env.lists, env.stats, or env.strings.
        maps - Boolean turns on and off inheritance from other maps.

        """

        if not isinstance(target, Entity):
            target = self.getTarget(target)

        if not self.inheritance:
            return getattr(target, stat)

        #self and grouped objects
        def iterValues(target):
            #classes
            for item in target.group:
                value = getattr(self[item], stat)
                if value:
                    yield value

                #special lists
                for lst in self.rlist:
                    for unit in getattr(self[item], lst):
                        value = self.getStat(self[unit], stat)
                        if value:
                            yield value

            #map locations
            if maps and target.loc:
                current = self.getMap(target.loc)
                for map_ in self.rmap:
                    if map_ != current:
                        new_loc = (target.loc[0], target.loc[1], map_)
                        value = self.getStat(new_loc, stat, False)
                        if value:
                            yield value

        if stat == 'group':
            return target.group
        elif stat in self.strings:
            try:
                return next(iterValues(target))
            except StopIteration:
                return ""
        elif stat in self.stats:
            return sum(iterValues(target))
        elif stat in self.lists:
            return list(itertools.chain(*iterValues(target)))
        else:
            raise UndefinedStatError(stat)

    def getDistance(self, one, two, method):
        """Returns distance between two entity selectors.

        one - Entity selector
        two - Entity selector
        method - Distance metric to used

        """
        #Note: Dictonary switch method doubles this functions run time.
        if not isinstance(one, Entity):
            one = self.getTarget(one)
        if not isinstance(two, Entity):
            two = self.getTarget(two)

        one = one.loc
        two = two.loc

        if not one or not two:
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
        elif method in self:
            count = 0
            for i in self.getAdjacent(one, method):
                if two in i:
                    return count
                count +=1
            else:
                return float("inf")
        else:
            raise UndefinedMetricError(method)

    def getEnv(self, caster, target, move):
        """
        Creates an environment object. From three entity targets.
        """
        if not isinstance(caster, Entity):
            caster = self.getTarget(caster)
        if not isinstance(target, Entity):
            target = self.getTarget(target)
        if not isinstance(move, Entity):
            move = self.getTarget(move)

        var_local = {
            "caster": caster,
            "target": target,
            "move": move,
            "C": caster,
            "T": target,
            "M": move,
        }
        return interpret._getEnv(var_local, {"self": self})

    #Pathing get functions.
    def getAdjacent(self, center, move="empty", pointer=None):
        """
        Iterates over concentric circles of adjacent tiles
        """
        if not isinstance(center, Entity):
            center = self.getTarget(center)
        if not isinstance(move, Entity):
            move = self.getTarget(move)

        if not center.loc:
            yield list()
            return

        new = {center.loc}
        searched = {center.loc}
        next = self.adjacent(center.loc, pointer)

        next.difference_update(searched)

        while len(new) > 0:
            #Sorted is needed to force program to be deterministic.
            yield sorted(list(new))
            new = set()
            for node in next:
                if not self.testValidLoc(node):
                    continue
                if self.testMove(center, node, move):
                    new.add(node)

            searched.update(next)
            next = set().union(*[self.adjacent(node, pointer) for node in new])
            next.difference_update(searched)

    def getPath(self, start, finish, move):
        """
        Algorithm to find a path between start and finish assuming move.

        start, finish - Target objects of start and finish locations.
        move - Entity that decides if a spot can be moved onto.

        Returns empty list if there is no path.
        """
        if not isinstance(start, Entity):
            start = self.getTarget(start)
        if not isinstance(finish, Entity):
            finish = self.getTarget(finish)
        pointer = {}

        if start == finish:
            return []

        for i in self.getAdjacent(start, move, pointer):
            if finish.loc in i:
                break
        else:
            return []

        found = [finish.loc]
        while True:
            new = pointer[found[-1]]
            found.append(new)
            if new == start.loc:
                found.reverse()
                return found

    def getFill(self, center, move='empty', distance=float("inf")):
        """
        Returns a list of map spaces that center fills into.

        center - Target object representing starting location of fill.
        move - Target object representing move that defines fill success.
        distance - Maximum fill distance from target.
        """
        found = []
        count = 0
        for i in self.getAdjacent(center, move):
            found.extend(i)
            if count >= distance:
                break
            count +=1
        self.rand.shuffle(found)
        return found

    #Random other get functions.
    def getLog(self):
        """Returns list of log entries made since last call."""
#        test = copy.copy(self.log)
#        self.controlLog(clear=True)
#        return test
        return self.log

    def getMap(self, target="map"):
        """Returns first location for string in env.map."""
        if not target:
            return False

        ttype = type(target)
        if ttype is Board:
            return target
        elif ttype is tuple:
            return self.getMap("map" if len(target) < 3 else target[2])
        elif ttype is str:
            try:
                return self.map[target]
            except KeyError:
                raise UndefinedSelectorError(target, "map")
        else:
            raise UndefinedSelectorError(target, "map")

    def getRevert(self, value=0):
        index = -(value +1)
        try:
            new = copy.deepcopy(self.state[index])
        except IndexError:
            return False

        new.state = self.state[:index+1]
        return new

    #Simple get functions.
    def getGroup(self, group, inc_self=False):
        """Return all objects belonging to group."""
        if not isinstance(group, Entity):
            group = self.getTarget(group)

        found = []
        for unit in self:
            if group.name in self.getStat(unit, 'group'):
                found.append(unit)
        if not inc_self:
            found.remove(group.name)
        return found

    def getListStat(self, lst, stat):
        """Returns combination of all stats for objects in a units list.

        lst - String representing list to check.
        stat - String representing defined stat.

        """
        found = (self.getStat(element, stat) for element in lst)

        if stat in self.stats:
            return sum(found)
        elif stat in self.lists:
            return list(itertools.chain(*found))
        elif stat in self.strings:
            return next(found)
        else:
            raise UndefinedStatError(stat)

    def getListGroup(self, target, lst, group):
        """Returns first element in list that is a member of group.

        target - Entity selector.
        lst - String representing list to check.
        group - Entity selector representing group.

        """
        if not isinstance(group, Entity):
            group = self.getTarget(group)

        start = self.getStat(target, lst)
        for item in start:
            if group.name in self.getStat(item, 'group'):
                return item
        return False

    def getFilter(self, iterable, caster, move):
        """Return all elements of list where move suceeds."""
        return [i for i in iterable if self.testMove(caster, i, move)]

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

    #Entity helper get functions.
    def getX(self, entity):
        if not isinstance(entity, Entity):
            entity = self.getTarget(entity)

        if entity.loc:
            return entity.loc[0]
        return False

    def getY(self, entity):
        if not isinstance(entity, Entity):
            entity = self.getTarget(entity)

        if entity.loc:
            return entity.loc[1]
        return False

    def getLoc(self, entity):
        if not isinstance(entity, Entity):
            entity = self.getTarget(entity)
        return entity.loc

    def getName(self, entity):
        if not isinstance(entity, Entity):
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
            again = True
            while again:
                again = False
                for delay in self.delay[:]:
                    if delay['ticks'] <= 0:
                        self.delay.remove(delay)
                        env = self.getEnv(delay['caster'], delay['target'], delay['move'])
                        self.controlEffect(env, delay['script'])
                        again = True

            self.controlRevert()
            self.controlLog()

        checkdelay()
        for i in range(time):
            self.time +=1
            self.controlLog('Env time is now', self.time)
            if 'tick' in self:
                env = self.getEnv("empty", 'empty', "tick")
                if self.testRequire(env) == True:
                    self.controlEffect(env)
            for delay in self.delay:
                delay['ticks'] -=1
            checkdelay()

        return True

    def controlRevert(self):
        """Controls saving of new states."""
        if self.revert > 1 and self.state:
            clone = copy.deepcopy(self)
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

    def controlStat(self, targets, stat, increment, multiplyer=1):
        """Changes stored stat of target by increment.

        targets - Multiple Entity selector
        stat - Defined statistic to change
        increment - integer to change stat by.

        """
        if not isinstance(targets, Entity):
            targets = self.getTarget(targets, multi=True)

        increment = int(increment * multiplyer)
        if increment == 0:
            return False

        flag = False
        for target in targets:
            if target.immutable:
                continue

            newValue = getattr(target, stat) + increment
            setattr(target, stat, newValue)
            self.controlLog(target.name, stat, "changed by", increment, "is now", self.getStat(target, stat))
            flag = True

        return flag

    def controlString(self, targets, strg, new):
        """Changes stored stat of target by increment.

        targets - Multiple Entity selector
        str - String stat to change.
        new - New value of string.

        """
        if not isinstance(targets, Entity):
            targets = self.getTarget(targets, multi=True)

        flag = False
        for target in targets:
            if target.immutable:
                continue

            setattr(target, strg, new)
            self.controlLog(target.name, strg, "is now", new)
            flag = True

        return flag

    def controlList(self, targets, lst, entries, method='add'):
        """Adds or removes items in Entity list.

        targets - Multiple Entity selector
        lst - Defined list to change.
        entry - String to add or remove.
        increment - String to add to or remove from list.

        """
        if not isinstance(targets, Entity):
            targets = self.getTarget(targets, multi=True)

        if isinstance(entries, str):
            entries = [entries]

        flag = False
        for target in targets:
            if target.immutable:
                continue

            list_ = getattr(target, lst)
            if method == "clear":
                del list_[:]
                if lst == "group":
                    list_.append(target.name)
                self.controlLog(target.name, lst, "has been cleared.")
                flag = True
                continue

            for entry in entries:
                if isinstance(entry, Entity):
                    if entry.immutable:
                        continue
                    entry = entry.name

                if method == 'remove':
                    if entry in list_:
                        list_.remove(entry)
                        self.controlLog(entry, "removed from", target.name, lst)
                        flag = True
                    continue

                list_.append(entry)
                self.controlLog(entry, "added to", target.name, lst)
                flag = True

        return flag

    def controlDelete(self, targets):
        """
        Controls the delete of unused entities.
        Warning. Experimental, not recomended.
        """
        if not isinstance(targets, Entity):
            targets = self.getTarget(targets, multi=True)

        for target in targets:
            if not target.immutable:
                self.controlLog(target.name, "has been removed from the game.")
                del self[target.name]
                del target

        return True

    def controlRecruit(self, clone, positions=[]):
        """
        Recruits a clone of entity to an instance.

        clone - Target object to clone.
        positions - List of locations to clone the object to. (None creates an offboard unit.)
        """
        if not isinstance(positions, Entity):
            positions = self.getTarget(positions, multi=True)
        if not isinstance(clone, Entity):
            clone = self.getTarget(clone)

        new_unit = None

        if clone.immutable:
            self.controlLog("can't clone immutable entity.")
            return False

        for position in positions:
            #Get name of new unit
            new_unit = clone.clone()

            #travel object to location
            self.controlLog(new_unit.name, "has been recruited")
            if position is not None:
                self.controlTravel(new_unit, position)

        return new_unit

    def controlTravel(self, caster, targets=False):
        """
        Changes a units board locations.

        caster - Target object to move.
        targets - Location to move object to. (Multiple only for immutable. Otherwise caster is moved multiple times.)
        """
        if not isinstance(caster, Entity):
            caster = self.getTarget(caster)
        if not isinstance(targets, Entity):
            targets = self.getTarget(targets, multi=True)

        for target in targets:

            #Check for some common case warnings.
            if caster.loc == target.loc:
                self.controlLog("Warning: tried to move unit to itself.")
                return False

            #move units
            if target.loc:
                self.getMap(target.loc)[target.loc] = caster.name
            if caster.loc and not caster.immutable:
                del self.getMap(caster.loc)[caster.loc]

            #update units
            target.update()
            caster.update()

            #control Logs
            if not caster.immutable:
                self.controlLog(caster.name, "has moved to", caster.loc)
            if not target.immutable and target.name != caster.name:
                self.controlLog(target.name, "has been bumped")

        return True

    def controlDelay(self, caster, target, move, string, delay):
        """
        Creates a new delay object.

        """
        new_delay = {
            "caster": caster,
            "target": target,
            "move": move,
            "script": Script(string, raw=False, require=False, version=self.version),
            "ticks": delay
        }

        self.delay.append(new_delay)
        self.controlLog("effect added to delay for", delay)
        return True

    def controlMove(self, caster, targets , moves, force=False):
        """
        Main function to trigger an event.

        caster - Target object of caster
        targets - Target objects of recipient.
        moves - Target objects of events to trigger.
        force - Boolean to trigger skipping of require check. (Rarely used)
        """
        if not isinstance(caster, Entity):
            caster = self.getTarget(caster)
        if not isinstance(targets, Entity):
            targets = self.getTarget(targets, multi=True)
        if not isinstance(moves, Entity):
            moves = self.getTarget(moves, multi=True)

        flag = False
        for target in targets:
            for move in moves:
                env = self.getEnv(caster, target, move)

                check = True if force else self.testRequire(env)
                if check != True:
                    self.controlLog(caster.name, "cast", move.name, "on",
                                    target.name, "failed because", check)
                    continue

                if caster == target == 'empty':
                    self.controlLog(move, "has been triggered.")
                else:
                    self.controlLog(caster.name, "uses", move.name, "on", target.name)
                self.controlEffect(env)
                flag = True

        return flag

    def controlInit(self, move, time=0, force=False):
        """Wrapper of controlMove where caster and target are unimportant."""
        if not isinstance(move, Entity):
            try:
                move = self.getTarget(move)
            except UndefinedSelectorError:
                new = Entity(self, "__string__")
                new.effect.append(Script(move, version=self.version))
                move = new

        if self.controlMove("empty", "empty", move, force):
            self.controlTime(time)
            return True

        return False

    def controlEffect(self, env, effects=False, command="effect"):
        """
        Controls actual execution of events.

        env - environment object to trigger.
        single - specific effect to trigger in env (Not neccessary derived from env.)
        command - "effect" or "require" which one is triggered.
        """
        if not effects:
            effects = self.getStat(env['storage']['move'], command)

        for effect in effects:
            try:
                if not eval(effect.code, env):
                    if command == "require":
                        return effect.raw

            except Exception:
                print("invalid '{}' \ninterpreted as '{}'".format(effect.raw, effect.interpret))
                print()
                raise

        return True

    #---------------------------------------------------
    #              Testing Functions                   -
    #---------------------------------------------------

    def testFuture(self, caster, target, move, string, time=0):
        """
        Experimental function. Checks if condition is true in the future.
        (Works for chess, I doubt I will touch it.)

        caster, target, move - event to triger.
        time - how much time to pass after event.
        """
        if not isinstance(caster, Entity):
            caster = self.getTarget(caster)
        if not isinstance(target, Entity):
            target = self.getTarget(target)
        if not isinstance(move, Entity):
            move = self.getTarget(move)

        #create test instance
        clone = copy.deepcopy(self)
        clone.logging = False

        #convert instance targets into clone targets.
        caster = clone.getTarget(caster.loc)
        target = clone.getTarget(target.loc)
        move = clone.getTarget(move.name)

        #Send clone into the future.
        clone.controlMove(caster, target, move, force=True)
        clone.controlTime(time)

        #Test for condition
        effects = [Script(string, raw=False, require=True, version=self.version)]
        return clone.testMove(caster, target, move, effects)

    def testBlock(self, start, finish, move):
        """Tests to see if there exists a path from start to finish."""

        if not isinstance(finish, Entity):
            finish = self.getTarget(finish)

        for i in self.getAdjacent(start, move):
            for q in i:
                if finish.loc in self.adjacent(q):
                    return True
        return False

    def testMove(self, caster, target, move, effects=False):
        """Gutted controlMove, returns if event would have activated."""
        env = self.getEnv(caster, target, move)
        result = self.testRequire(env, effects)
        "testRequire returns a string if test failed indicating why test failed."
        return True if result == True else False

    def testRequire(self, env, effects=False):
        """Require wrapper for controlEffect."""
        return self.controlEffect(env, effects, "require")

    def testValidLoc(self, loc):
        map_ = self.getMap(loc)
        try:
            unit = map_[loc]
            return True
        except Exception:
            return False

    #---------------------------------------------------
    #                   Other Functions                -
    #---------------------------------------------------
    def castMove(self, caster, target , move, time=0, force=False):
        """Wrapper of controlMove that appends a tick."""
        if self.controlMove(caster, target, move, force):
            self.controlTime(time)
            return True
        return False

    def adjacent(self, location, pointer=None):
        """
        Returns rough index of tiles adjacent to given tile.
        location - Any tuple location.
        pointer - optional pointer dict to keep track of path.
        """
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

#---------------------------------------------------
#                 Other Objects                    -
#---------------------------------------------------

class UndefinedStatError(Exception):
    def __init__(self, stat):
        self.stat = stat
    def __str__(self):
        return repr(self.stat)+" is not a defined stat."

class UndefinedSelectorError(Exception):
    def __init__(self, target, _type):
        self.selector = target
        self.type = _type
    def __str__(self):
        return "{} is not a valid {} selector.".format(repr(self.selector), self.type)

class UndefinedMetricError(Exception):
    def __init__(self, metric):
        self.metric = metric
    def __str__(self):
        return repr(self.metric)+" is not a valid distance metric."

class Entity:
    def __init__(self, field, name=False, immutable=False):
        self.name = name
        self.field = field
        self.immutable = immutable

        self.loc = False
        for stat in field.stats:
            setattr(self, stat, 0)
        for lists in field.lists:
            setattr(self, lists, [])
        for string in field.strings:
            setattr(self, string, '')

        self.group = [self.name]

        if name:
            self.field[self.name] = self
            self.update()


    def __eq__(self, other):
        try:
            other = self.field.getTarget(other)
        except Exception:
            return False

        values = [
            self.name == other.name,
            self.loc == other.loc,
            self.immutable == other.immutable,
        ]
        for stat in itertools.chain(self.field.stats, self.field.lists, self.field.strings):
            values.append(getattr(self, stat) == getattr(other, stat))
        return all(values)

    def __str__(self):
        return self.name

    def __repr__(self):
        return "<entity: "+self.name+">"

    def __iter__(self):
        yield self

    def __deepcopy__(self, memo):
        "Prevents field attribute from being copied."
        new = Entity(self.field)
        for k, v in self.__dict__.items():
            if k == "field":
                setattr(new, k, v)
            else:
                setattr(new, k, copy.deepcopy(v, memo))

        return new

    def clone(self):
        "Makes a new Entity from old entity."
        if self.immutable:
            return self

        #Create new
        new = copy.deepcopy(self)

        #Set name of new
        self.increment +=1
        name = self.name + str(self.increment)
        new.name = name

        #Setup new group and inc
        new.group.remove(self.name)
        new.group = [name] + new.group
        new.increment = 0

        #Add new to field.
        new.field[name] = new
        new.update()

        return new

    def update(self, target=False):
        "Updates stored location with system location."
        if target:
            if len(target) < 3:
                target = (target[0], target[1], "map")

            if self.field.testValidLoc(target):
                self.loc = target
                return self.loc

        elif not self.immutable:
            for map_ in self.field.map.values():
                test = map_.find(self.name)
                if test:
                    self.loc = test
                    return self.loc

        self.loc = False
        return self.loc

class Script:
    def __init__(self, effect, require=False, debug=False, raw=True, version=1):
        command = 'eval' if require else 'exec'
        self.raw = effect
        if raw:
            self.interpret = interpret.interpret(effect, version, debug)
        else:
            self.interpret = effect
        self.code = compile(self.interpret, '<string>', command)

    def __iter__(self):
        yield self

    def __eq__(self, other):
        return isinstance(other, Script) and self.raw == other.raw

    def __repr__(self):
        return self.raw

class Board(collections.MutableMapping):
    def __init__(self, name=False, dim=[1,1], empty="empty"):
        self.name = name
        self.empty = empty

        #Set up maps.
        if isinstance(dim, tuple):
            self._map = []
            for e in range(dim[0]):
                self._map.append([empty for i in range(dim[1])])

        elif isinstance(dim, list):
            new_map._map = dim

    def __eq__(self, other):
        if not isinstance(other, Board):
            return False

        values = [
            self._map == other._map,
            self.name == other.name,
            self.empty == other.empty,
        ]
        return all(values)

    def __getitem__(self, key):
        "Get object at location."
        x = key[0]
        y = key[1]
        if x < 0 or y < 0:
            raise IndexError
        return self._map[x][y]

    def __setitem__(self, key, value):
        """Insert string at location."""
        x = key[0]
        y = key[1]
        if x < 0 or y < 0:
            raise IndexError
        self._map[x][y] = value

    def __delitem__(self, key):
        x = key[0]
        y = key[1]
        self._map[x][y] = self.empty

    def __len__(self):
        return self.x * self.y

    def __iter__(self):
        for x in range(self.x):
            for y in range(self.y):
                yield (x, y, self.name)

    def __repr__(self):
        return "<board: "+self.name+">"

    @property
    def x(self):
        return len(self._map)

    @property
    def y(self):
        try:
            return max([len(x) for x in self._map])
        except ValueError:
            return 0

    def find(self, string):
        "Get location of object."
        for loc in self:
            if self[loc] == string:
                return (loc[0], loc[1], self.name)
        return False
