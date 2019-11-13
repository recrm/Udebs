from random import Random
from copy import copy
from itertools import product
from collections.abc import MutableMapping
from logging import info
from functools import singledispatchmethod

from udebs.interpret import Script, UdebsStr, _getEnv
from udebs.board import Board
from udebs.entity import Entity
from udebs.utilities import norecurse

#---------------------------------------------------
#                 Main Class                       -
#---------------------------------------------------

class Instance(MutableMapping):
    """
    Main instance class that represents the state space of the entire game.

    Note on naming convention:

    All methods begining with 'get' return information about the game's state
    space and are not allowed to change the state itself.

    All methods beggining with 'control' manage some aspect of the state space
    and return true if changes were (probobaly) made and false otherwise.

    Other functions are convinience wrappers for public use.
    """
    def __init__(self, copy=False):
        if copy:
            return

        #definitions
        self.lists = {'group', 'effect', 'require'}
        self.stats = {'increment'}
        self.strings = set()
        #rlist and rmap are flags that indicate objects entities should inherit from.
        self.rlist = {'group'}
        self.rmap = set()

        #config
        self.name = 'Unknown' # only effects what is printed when initialized
        self.logging = True # Turns logging on and off
        self.revert = 0 # Determins how many steps should be saved in revert
        self.version = 1 # What version of Udebs syntax is used.
        self.seed = None # Random seed for processing.
        self.immutable = False # Determines default setting for entities immutability.

        #time
        self.time = 0 # In game counter
        self.increment = 1 # how much time passes between gameloop iterations. Useful for pausing.
        self.cont = True # Flag to determine if gameloop should continue
        self.next = None # The next state a gameloop will return. Useful for resets and reverts in gameloop

        #internal
        self.map = {}
        self._data = {}
        self.delay = []
        self.rand = Random()

        #Do not copy
        self.state = []

    @norecurse
    def __eq__(self, other):
        if not isinstance(other, Instance):
            return False

        for k,v in self.__dict__.items():
            if k not in ("state", "rand") and v != getattr(other, k):
                return False

        return True

    def __copy__(self):
        new = Instance(True)

        for k, v in self.__dict__.items():
            if k not in {"delay", "map", "_data", "state"}:
                setattr(new, k, v)

        new._data = {}
        for name, entity in self._data.items():
            if entity.immutable:
                new[name] = entity
            else:
                new[name] = entity.copy(new)

        new.map = {}
        for name, map_ in self.map.items():
            new.map[name] = map_.copy(new)

        new.delay = []
        for delay in self.delay:
            new.delay.append({
                "env": delay["env"], # This is likely broken. Environment must be updated.
                "ticks": delay["ticks"],
                "script": delay["script"],
            })

        new.state = []

        return new

    def __getitem__(self, key):
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
    #               Selector Function                  -
    #---------------------------------------------------

    def getEntity(self, target, multi=False):
        """Returns entity object based on given selector.
        Note: This function previously used singledispatch. However, it
        is a ton slower and no more readable than an if stack.

        target - Any entity selector.
        multi - Boolean, allows lists of targets.

        """
        if isinstance(target, Entity):
            return target
        elif target is False or target == "bump":
            return self['empty']
        elif isinstance(target, str) and target in self:
            return self[target]
        elif isinstance(target, tuple):
            return self.getEntityTuple(target)
        elif isinstance(target, list) and len(target) > 0:
            if multi:
                return [self.getEntity(i) for i in target]
            return self.getEntity(value[0])
        elif isinstance(target, UdebsStr):
            return self.getEntityUdebsStr(target)

        raise UndefinedSelectorError(target, "entity")

    def getEntityUdebsStr(self, target):
        #Process new nameless.
        scripts = []
        if target[0] == "(":
            buf = ''
            bracket = 0

            for char in target[1:-1]:
                if char == "(":
                    bracket +=1

                if char == ")":
                    bracket -=1

                if not bracket and char == ",":
                    scripts.append(Script(UdebsStr(buf), self.version))
                    buf = ''
                    continue

                buf += char

            raw = UdebsStr(buf)
            scripts.append(Script(raw, self.version))

        else:
            scripts.append(Script(target, self.version))

        self[target] = Entity(self, require=scripts, name=target, immutable=True)
        return self[target]

    def getEntityTuple(self, target):
        #If tuple, this is a location.
        try:
            map_ = self.getMap(target)
        except KeyError:
            raise UndefinedSelectorError(target, "entity")

        # entity stored in the map
        try:
            name = map_[target]
        except IndexError:
            raise UndefinedSelectorError(target, "entity")

        unit = self[name]

        if not unit.loc:
            if len(target) < 3:
                target = (*target, map_.name)
            unit = unit.copy(self, loc=target)

        return unit

    def getMap(self, target="map"):
        """Gets a map by name or object on it."""
        if not target:
            return False
        elif isinstance(target, str):
            try:
                return self.map[target]
            except KeyError:
                raise UndefinedSelectorError(target, "map")
        elif isinstance(target, Board):
            return target
        elif isinstance(target, Entity):
            return self.map[target.loc[2] if len(target.loc) == 3 else "map"]
        elif isinstance(target, tuple):
            return self.map[target[2] if len(target) == 3 else "map"]
        else:
            raise UndefinedSelectorError(target, "map")

    #---------------------------------------------------
    #                 Time Management                  -
    #---------------------------------------------------

    def controlTime(self, time=1, script="tick"):
        """Changes internal time, runs tick script, and updates any delayed effects.

        time - Integer representing number of updates.

        """
        def checkdelay():
            while True:
                again = False
                for delay in self.delay[:]:
                    if delay['ticks'] <= 0:
                        self.delay.remove(delay)
                        delay['script'](delay['env'])
                        again = True

                if not again:
                    break

        checkdelay()
        for i in range(time):
            self.time +=1

            if self.logging:
                info(f'\nEnv time is now {self.time}')
            if script in self:
                self.controlMove(self["empty"], self["empty"], self[script])
                checkdelay()

            for delay in self.delay:
                delay['ticks'] -=1
            checkdelay()

            #Append new version to state.
            if self.revert:
                self.state.append(copy(self))

        if self.revert:
            self.state = self.state[-self.revert:]

        return self.cont

    def getRevert(self, value=0):
        index = -(value +1)
        try:
            new = copy(self.state[index])
        except IndexError:
            return False

        del self.state[index+1:]
        new.state = self.state
        return new

    def controlDelay(self, callback, delay, storage):
        """
        Creates a new delay object.

        """
        env = _getEnv(storage, {"self": self})

        new_delay = {
            "env": env,
            "script": self.getEntity(callback),
            "ticks": delay
        }

        self.delay.append(new_delay)
        if self.logging:
            info(f"effect added to delay for {delay}")
        return True

    @norecurse
    def testFuture(self, caster, target, move, string, time=0):
        """
        Experimental function. Checks if condition is true in the future.
        (Works for chess, I doubt I will touch it.)

        caster, target, move - event to triger.
        time - how much time to pass after event.
        """

        if self.logging:
            info("Testing future condition.")

        caster = self.getEntity(caster)
        target = self.getEntity(target)
        move = self.getEntity(move)

        #create test instance
        clone = copy(self)
        clone.revert = 0

        #convert instance targets into clone targets.
        caster = clone.getEntity(caster.loc)
        target = clone.getEntity(target.loc)
        move = clone.getEntity(move.name)

        #Send clone into the future.
        env = clone.getEnv(caster, target, move)
        move.controlEffect(env)
        clone.controlTime(time)

        effects = clone.getEntity(string)
        test = clone.testMove(caster, target, effects)

        if self.logging:
            info("Done testing future condition.\n")
        return test

    #---------------------------------------------------
    #           Coorporate get functions               -
    #---------------------------------------------------

    def getStat(self, target, stat):
        """General getter for all attributes.

        target - Entity selector.
        stat - Stat defined in env.lists, env.stats, or env.strings.
        maps - Boolean turns on and off inheritance from other maps.

        """
        current = self.getEntity(target)
        if stat in {"increment", "group"}:
            return current[stat]
        elif stat in self.stats:
            total = 0
        elif stat in self.lists:
            total = []
        elif stat in self.strings:
            total = ""
        elif stat == "envtime":
            return self.time
        else:
            raise UndefinedSelectorError(stat, "stat")

        stack=[]

        # rmaps only apply to current object not rlists.
        if current.loc:
            for map_ in self.rmap:
                if map_ != current.loc[2]:
                    new_loc = (current.loc[0], current.loc[1], map_)
                    stack.append(self.getEntity(new_loc))

        while True:
            if (value := getattr(current, stat)):
                if isinstance(total, int):
                    total += value
                elif isinstance(total, list):
                    total.extend(value)
                else:
                    return value

            for lst in self.rlist:
                for unit in getattr(current, lst):
                    stack.append(self[unit])

            if len(stack) == 0:
                break

            current = stack.pop()

        return total

    def getGroup(self, group):
        """Return all objects belonging to group."""
        groupname = self.getEntity(group).name
        values = [unit for unit in self if groupname in self[unit]["group"]]
        return sorted(values)

    def getListStat(self, lst, stat):
        """Returns combination of all stats for objects in a units list.

        lst - String representing list to check.
        stat - String representing defined stat.

        """
        found = (self.getStat(element, stat) for element in lst)

        if stat in self.stats:
            return sum(found)
        elif stat in self.lists:
            return list(i for j in found for i in j)
        elif stat in self.strings:
            return next(found)

    def getListGroup(self, target, lst, group):
        """Returns first element in list that is a member of group.

        target - Entity selector.
        lst - String representing list to check.
        group - Entity selector representing group.

        """
        group = self.getEntity(group)

        start = self.getStat(target, lst)
        for item in start:
            if group.name in self[item]['group']:
                return item
        return False

    def getFilter(self, iterable, caster, callback):
        """Return all elements of list where move suceeds."""
        return [i for i in iterable if self.testMove(caster, i, callback)]

    def getSearch(self, *args):
        """Returns a list of objects contained in all groups.
        *args - lists of groups.
        """
        foundIter = iter(args)
        first = foundIter.__next__()
        found = set(self.getGroup(first))
        for arg in args:
            found = found.intersection(self.getGroup(arg))
        return sorted(list(found))

    #---------------------------------------------------
    #                 Call wrappers                    -
    #---------------------------------------------------

    def getEnv(self, caster, target, move):
        var_local = {
            "caster": caster,
            "target": target,
            "move": move,
            "C": caster,
            "T": target,
            "M": move,
        }
        return _getEnv(var_local, {"self": self})

    def controlMove(self, casters, targets, moves):
        """Main function to trigger an event."""
        casters = self.getEntity(casters, multi=True)
        targets = self.getEntity(targets, multi=True)
        moves = self.getEntity(moves, multi=True)

        value = False

        for caster, target, move in product(casters, targets, moves):
            if self.logging:
                # Logging
                cname = caster
                if caster.immutable and caster.loc:
                    cname = caster.loc

                tname = target
                if target.immutable and target.loc:
                    tname = target.loc

                if target.name == caster.name == "empty":
                    info(f"init {move}")
                elif target.name == "empty":
                    info(f"{cname} uses {move}")
                else:
                    info(f"{cname} uses {move} on {tname}")

            # Cast the move
            test = move(self.getEnv(caster, target, move))
            if test == True:
                value = True
            elif self.logging:
                info(f"failed because {test}")

        return value

    def testMove(self, caster, target, move):
        """Gutted controlMove, returns if event would have activated."""
        move = self.getEntity(move)
        env = self.getEnv(caster, target, move)
        return move.testRequire(env) == True

    def castInit(self, moves, time=0):
        """Wrapper of controlMove where caster and target are unimportant."""
        return self.castMove(self["empty"], self["empty"], moves, time)

    def castAction(self, caster, move, time=0):
        """Wrapper of controlMove where target is unimportant."""
        return self.castMove(caster, self["empty"], move, time)

    def castMove(self, caster, target , move, time=0):
        """Wrapper of controlMove that appends a tick."""
        value = self.controlMove(caster, target, move)
        if value:
            self.controlTime(time)
        return value

    def castSingle(self, string):
        """Call a function directly from a user inputed Udebs String."""
        code = Script(string, version=self.version)
        env = _getEnv({}, {"self": self})
        return code(env)

    #---------------------------------------------------
    #               Entity control                     -
    #---------------------------------------------------
    def controlListAdd(self, targets, lst, entries):
        targets = self.getEntity(targets, multi=True)
        if not isinstance(entries, list):
            entries = [entries]

        for target, entry in product(targets, entries):
            if not target.immutable:
                getattr(target, lst).append(entry)
                if self.logging:
                    info(f"{entry} added to {target} {lst}")

    def controlListRemove(self, targets, lst, entries):
        targets = self.getEntity(targets, multi=True)
        if not isinstance(entries, list):
            entries = [entries]

        for target, entry in product(targets, entries):
            if not target.immutable:
                value = getattr(target, lst)
                if entry in value:
                    value.remove(entry)
                    if self.logging:
                        info(f"{entry} removed from {target} {lst}")

    def controlClear(self, targets, lst):
        for target in self.getEntity(targets, multi=True):
            if not target.immutable:
                getattr(target, lst).clear()
                if self.logging:
                    info(f"{target} {lst} has been cleared")

    def controlShuffle(self, target, stat):
        for target in self.getEntity(target, multi=True):
            if not target.immutable:
                self.rand.shuffle(getattr(target, key))
                if self.logging:
                    info(f"{target} {stat} has been shuffled")

    def controlIncrement(self, targets, stat, increment, multi=1):
        total = int(increment * multi)
        for target in self.getEntity(targets, multi=True):
            if not target.immutable:
                setattr(target, stat, getattr(target, stat) + total)
                if self.logging:
                    info(f"{target} {stat} changed by {total}")

    def controlString(self, targets, stat, value):
        for target in self.getEntity(targets, multi=True):
            if not target.immutable:
                setattr(target, stat, value)
                if self.logging:
                    info(f"{target} {stat} changed to {value}")

    def controlRecruit(self, target, positions):
        target = self.getEntity(target)
        new = target
        for position in positions if isinstance(positions, list) else [positions]:
            if not target.immutable:
                new = target.controlClone(self)
                self[new.name] = new
                if self.logging:
                    info(f"{new} has been recruited")
            self.controlTravel(new, position)

        return new

    #---------------------------------------------------
    #                 Entity get wrappers              -
    #---------------------------------------------------

    def getX(self, target, value=0):
        unit = self.getEntity(target)
        return unit.loc[value] if unit.loc else False

    def getY(self, target):
        return self.getX(target, 1)

    def getLoc(self, target):
        return self.getEntity(target).loc

    def getName(self, target):
        return self.getEntity(target).name

    #---------------------------------------------------
    #                 Board get wrappers               -
    #---------------------------------------------------

    def getPath(self, caster, target, callback):
        caster = self.getEntity(caster).loc
        target = self.getEntity(target).loc
        callback = self.getEntity(callback)
        return self.getMap(caster).getPath(caster, target, callback)

    def getDistance(self, caster, target, method):
        caster = self.getEntity(caster).loc
        target = self.getEntity(target).loc
        if method in self:
            method = self.getEntity(method)

        return self.getMap(caster).getDistance(caster, target, method)

    def testBlock(self, caster, target, callback):
        caster = self.getEntity(caster).loc
        target = self.getEntity(target).loc
        callback = self.getEntity(callback)
        return self.getMap(caster).testBlock(caster, target, callback)

    def testValid(self, caster):
        caster = self.getEntity(caster).loc
        map_ = self.getMap(caster)
        return map_.testLoc(caster)

    def getFill(self, center, callback=False, include_center=True, distance=float("inf")):
        if distance is None:
            distance = float("inf")

        center = self.getEntity(center).loc
        callback = self.getEntity(callback)
        return self.getMap(center).getFill(center, callback, distance, self.rand, include_center=include_center)

    #---------------------------------------------------
    #              Board control wrappers              -
    #---------------------------------------------------
    def controlTravel(self, caster, targets=False):
        caster = self.getEntity(caster)
        targets = self.getEntity(targets, multi=True)

        if len(targets) > 1 and not caster.immutable:
            raise Exception("Non immutable entities cannot be moved to multiple locations.")

        for target in targets:
            # First remove caster from it's current location
            if not caster.immutable and caster.loc:
                del self.getMap(caster.loc)[caster.loc]

            # Then move caster to target location.
            loc = target.loc
            if target.loc:
                try:
                    self.getMap(target.loc)[target.loc] = caster.name
                    if not target.immutable:
                        target.loc = None

                    if self.logging:
                        info(f"{caster} has moved to {target.loc}")
                except IndexError:
                    if self.logging:
                        info(f"{loc} is an invalid location. {caster} moving off the board")
                    loc = None

            # Update the entity itself.
            if not caster.immutable:
                caster.loc = loc

    #---------------------------------------------------
    #                 Game Loop Helpers                -
    #---------------------------------------------------

    def gameLoop(self, time=1, script="tick"):
        """Automatically increments in game timer over every iteration."""
        self.increment = time
        while self.cont:
            yield self

            if self.next is not None:
                yield self.next
                self = self.next

            self.controlTime(time, script=script)

        if self.logging:
            info(f"EXITING {self.name}\n")

    def exit(self):
        """Ends game if gameLoop is in use."""
        if self.logging:
            info("Exit requested")
        self.cont = False

    def resetState(self, script="reset"):
        """Resets game metadata to default."""
        if self.revert:
            self.state.clear()
            self.state.append(copy(self))

        if script in self:
            self.controlMove(self["empty"], self["empty"], self[script])

        self.cont = True
        self.time = 0

    def mapIter(self, mapname="map"):
        map_ = self.getMap(mapname)
        for loc in map_:
            yield self[map_[loc]]

#---------------------------------------------------
#                     Errors                       -
#---------------------------------------------------
class UndefinedSelectorError(Exception):
    def __init__(self, target, _type):
        self.selector = target
        self.type = _type
    def __str__(self):
        return "{} is not a valid {} selector.".format(repr(self.selector), self.type)
