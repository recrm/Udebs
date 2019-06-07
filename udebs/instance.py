import random
import copy
import itertools
import collections
import logging

from udebs import interpret, board, entity
from  udebs.utilities import dispatchmethod, norecurse, lookup

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

    Other functions are convinience wrappers for public use.
    """
    def __init__(self):
        #definitions
        self.lists = {'group', 'effect', 'require'}
        self.stats = {'increment'}
        self.strings = set()
        #rlist and rmap are flags that indicate objects entities should inherit from.
        self.rlist = {'group'}
        self.rmap = set()

        #config
        self.name = 'Unknown'
        self.logging = True
        self.revert = 0
        self.version = 1
        self.seed = None

        #time
        self.time = 0
        self.increment = 1
        self.cont = True
        self.next = None

        #internal
        self.map = {}
        self._data = {}
        self.delay = []
        self.rand = random.Random()

        #Used by players #not implemented in save.
        self.movestore = {}

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

    def __deepcopy__(self, memo):
        new = Instance()

        #Prevent state from being copied.
        for k, v in self.__dict__.items():
            if k in {"delay", "map", "_data"}:
                setattr(new, k, copy.deepcopy(v, memo))
            elif k != "state":
                setattr(new, k, v)

        #Set all saved Entities to this field.
        for e in new.values():
            e.field = new

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
    #               Selector Function                  -
    #---------------------------------------------------

    @dispatchmethod
    def getEntity(self, target, multi=False):
        """Returns entity object based on given selector.

        target - Any entity selector.
        multi - Boolean, allows lists of targets.

        """
        raise UndefinedSelectorError(target, "entity")

    @getEntity.register(entity.Entity)
    def _(self, target, multi=False):
        return target

    @getEntity.register(bool)
    def _(self, target, multi=False):
        # False is an allowable selector for empty.
        if target is False:
            return self['empty']
        raise UndefinedSelectorError(target, "entity")

    @getEntity.register(str)
    def _(self, target, multi=False):
        #If string, return associated entity.
        if target == "bump":
            return self["empty"]

        try:
            return self[target]
        except KeyError:
            raise UndefinedSelectorError(target, "entity")

    @getEntity.register(interpret.UdebsStr)
    def _(self, target, multi=False):
        #Interpretted callback
        # Nameless has already been processed.
        if target in self:
            return self[target]

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
                    scripts.append(interpret.Script(interpret.UdebsStr(buf), self.version))
                    buf = ''
                    continue

                buf += char

            raw = interpret.UdebsStr(buf)
            scripts.append(interpret.Script(raw, self.version))

        else:
            scripts.append(interpret.Script(target, self.version))

        self[target] = entity.Entity(self, {"require": scripts, "name": target})
        return self[target]

    @getEntity.register(tuple)
    def _(self, target, multi=False):
        #If tuple, this is a location.
        try:
            map_ = self.getMap(target)
        except KeyError:
            raise UndefinedSelectorError(target, "entity")

        try:
            unit = self[map_[target]]
        except IndexError:
            unit = self[map_.empty]

        if unit.immutable:
            if len(target) < 3:
                target = (target[0], target[1], "map")

            unit = copy.deepcopy(unit)
            unit.loc = target

        return unit

    @getEntity.register(list)
    def _(self, target, multi=False):
        #If type is a list individually check each element.
        value = map(self.getEntity, target)
        if multi:
            return list(value)
        return next(value)

    def getMap(self, target="map"):
        """Gets a map by name or object on it."""
        if not target:
            return False

        elif isinstance(target, str):
            try:
                return self.map[target]
            except KeyError:
                raise UndefinedSelectorError(target, "map")

        elif isinstance(target, board.Board):
            return target

        elif isinstance(target, entity.Entity):
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
            again = True
            while again:
                again = False
                for delay in self.delay[:]:
                    if delay['ticks'] <= 0:
                        self.delay.remove(delay)
                        delay['script'](delay['env'])
                        again = True

        checkdelay()
        for i in range(time):
            logging.info("")

            self.time +=1

            logging.info('Env time is now {}'.format(self.time))
            if script in self:
                self.controlMove(self["empty"], self["empty"], self[script])
                checkdelay()

            for delay in self.delay:
                delay['ticks'] -=1
            checkdelay()

            #Append new version to state.
            if self.revert:
                self.state.append(copy.deepcopy(self))

        if self.revert:
            self.state = self.state[-self.revert:]

        return self.cont

    def getRevert(self, value=0):
        index = -(value +1)
        try:
            new = copy.deepcopy(self.state[index])
        except IndexError:
            return False

        del self.state[index+1:]
        new.state = self.state
        return new

    def controlDelay(self, callback, delay, storage):
        """
        Creates a new delay object.

        """
        env = interpret._getEnv(storage, {"self": self})

        new_delay = {
            "env": env,
            "script": self.getEntity(callback),
            "ticks": delay
        }

        self.delay.append(new_delay)
        logging.info("effect added to delay for {}".format(delay))
        return True

    @norecurse
    def testFuture(self, caster, target, move, string, time=0):
        """
        Experimental function. Checks if condition is true in the future.
        (Works for chess, I doubt I will touch it.)

        caster, target, move - event to triger.
        time - how much time to pass after event.
        """

        logging.info("Testing future condition.")

        caster = self.getEntity(caster)
        target = self.getEntity(target)
        move = self.getEntity(move)

        #create test instance
        clone = copy.deepcopy(self)

        #convert instance targets into clone targets.
        caster = clone.getEntity(caster.loc)
        target = clone.getEntity(target.loc)
        move = clone.getEntity(move.name)

        #Send clone into the future.
        move.controlEffect(caster, target)
        clone.controlTime(time)

        effects = clone.getEntity(string)
        test = clone.testMove(caster, target, effects)

        logging.info("Done testing future condition.")
        logging.info("")
        return test

    #---------------------------------------------------
    #           Coorporate get functions               -
    #---------------------------------------------------

    def getStat(self, target, stat, maps=True):
        """General getter for all attributes.

        target - Entity selector.
        stat - Stat defined in env.lists, env.stats, or env.strings.
        maps - Boolean turns on and off inheritance from other maps.

        """
        #self and grouped objects
        def iterValues(target):
            if target[stat]:
                yield target[stat]

            #class and rlist
            for lst in self.rlist:
                for unit in target[lst]:
                    try:
                        group = self[unit]
                    except KeyError:
                        raise UndefinedSelectorError(unit, "group")

                    value = self.getStat(group, stat)
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

        if not isinstance(target, entity.Entity):
            target = self.getEntity(target)

        if stat in {'group', 'increment'}:
            return target[stat]
        elif stat in self.stats:
            return sum(iterValues(target))
        elif stat in self.lists:
            return list(itertools.chain(*iterValues(target)))
        elif stat in self.strings:
            try:
                return next(iterValues(target))
            except StopIteration:
                return ""

        # Temporary until I can figure out a better way to do this.
        elif stat == "envtime":
            return self.time
        else:
            raise UndefinedSelectorError(stat, "stat")

    def getGroup(self, group):
        """Return all objects belonging to group."""
        group = self.getEntity(group)
        values = [unit for unit in self if group.name in self.getStat(unit, "group")]
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
            return list(itertools.chain(*found))
        elif stat in self.strings:
            return next(found)
        else:
            raise UndefinedSelectorError(stat, "stat")

    def getListGroup(self, target, lst, group):
        """Returns first element in list that is a member of group.

        target - Entity selector.
        lst - String representing list to check.
        group - Entity selector representing group.

        """
        group = self.getEntity(group)

        start = self.getStat(target, lst)
        for item in start:
            if group.name in self.getStat(item, 'group'):
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

    def controlMove(self, casters, targets, moves):
        """Main function to trigger an event."""
        casters = self.getEntity(casters, multi=True)
        targets = self.getEntity(targets, multi=True)
        moves = self.getEntity(moves, multi=True)

        value = False

        for caster, target, move in itertools.product(casters, targets, moves):
            # Logging
            cname = caster
            if caster.immutable and caster.loc:
                cname = caster.loc

            tname = target
            if target.immutable and target.loc:
                tname = target.loc

            if target.name == caster.name == "empty":
                logging.info("init {}".format(move))
            elif target.name == "empty":
                logging.info("{} uses {}".format(cname, move))
            else:
                logging.info("{} uses {} on {}".format(cname, move, tname))

            # Cast the move
            test = move(caster, target)
            if test != True:
                logging.info("failed because {}".format(test))
            else:
                value = True

        return value

    def testMove(self, caster, target, move):
        """Gutted controlMove, returns if event would have activated."""
        move = self.getEntity(move)
        return move.testRequire(caster, target) == True

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
        code = interpret.Script(string, version=self.version)
        env = interpret._getEnv({}, {"self": self})
        return code(env)

    #---------------------------------------------------
    #               Entity control wrappers            -
    #---------------------------------------------------

    def controlListAdd(self, targets, lst, entries):
        targets = self.getEntity(targets, multi=True)
        if not isinstance(entries, list):
            entries = [entries]

        for target, entry in itertools.product(targets, entries):
            target.controlListAdd(lst, entry)
            logging.info("{} added to {} {}".format(entry, target, lst))

    def controlListRemove(self, targets, lst, entries):
        targets = self.getEntity(targets, multi=True)
        if not isinstance(entries, list):
            entries = [entries]

        for target, entry in itertools.product(targets, entries):
            target.controlListRemove(lst, entry)
            logging.info("{} removed from {} {}".format(entry, target, lst))

    def controlClear(self, targets, lst):
        targets = self.getEntity(targets, multi=True)
        for target in targets:
            target.controlListClear(lst)
            logging.info("{} {} has been cleared.".format(target, lst))

    def controlShuffle(self, target, stat):
        target = self.getEntity(target)
        self.rand.shuffle(target[stat])
        logging.info("{} {} has been shuffled".format(target, stat))

    def controlIncrement(self, targets, stat, increment, multi=1):
        if increment == 0:
            return

        targets = self.getEntity(targets, multi=True)
        for target in targets:
            target.controlIncrement(stat, increment, multi)
            logging.info("{} {} changed by {} is now {}".format(target, stat, increment*multi, self.getStat(target, stat)))

    def controlString(self, targets, stat, value):
        targets = self.getEntity(targets, multi=True)
        for target in targets:
            target[stat] = value
            logging.info("{} {} changed to {}".format(target, stat, value))

    def controlRecruit(self, target, positions):
        target = self.getEntity(target)
        if not isinstance(positions, list):
            positions = [positions]

        new = "empty"
        for position in positions:
            new = target.controlClone()
            logging.info("{} has been recruited".format(new))
            self.controlTravel(new, position)

        return new

    #---------------------------------------------------
    #                 Entity get wrappers              -
    #---------------------------------------------------

    def getX(self, target, value=0):
        unit = self.getEntity(target)
        if unit.loc:
            return unit.loc[value]
        return False

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
        if caster == False or target == False:
            return []

        callback = self.getEntity(callback)
        return self.getMap(caster).getPath(caster, target, callback)

    def getDistance(self, caster, target, method):
        caster = self.getEntity(caster).loc
        target = self.getEntity(target).loc
        if caster == False or target == False:
            return float("inf")

        if method in self:
            method = self.getEntity(method)

        return self.getMap(caster).getDistance(caster, target, method)

    def testBlock(self, caster, target, callback):
        caster = self.getEntity(caster).loc
        target = self.getEntity(target).loc
        if caster == False or target == False:
            return False

        callback = self.getEntity(callback)
        return self.getMap(caster).testBlock(caster, target, callback)

    def testValid(self, caster):
        caster = self.getEntity(caster).loc
        map_ = self.getMap(loc[2])
        return map_.testLoc(caster)

    def getFill(self, center, callback=False, include_center=True, distance=float("inf")):
        if distance is None:
            distance = float("inf")

        center = self.getEntity(center).loc
        if center == False:
            return []

        callback = self.getEntity(callback)
        return self.getMap(center).getFill(center, callback, distance, self.rand, include_center=include_center)

    #---------------------------------------------------
    #              Board control wrappers              -
    #---------------------------------------------------
    def controlTravel(self, caster, targets=False):
        caster = self.getEntity(caster)
        targets = self.getEntity(targets, multi=True)

        for target in targets:
            if not caster.immutable and caster.loc:
                self.getMap(caster.loc).controlBump(caster.loc)

            loc = target.loc
            if loc:
                if self.getMap(target).controlMove(caster.name, loc):
                    logging.info("{} has moved to {}".format(caster, loc))
                    target.controlLoc(False)
                else:
                    logging.info("{} is an invalid location. {} spawned off the board".format(loc, caster))

            caster.controlLoc(loc)

    #---------------------------------------------------
    #                 Game Loop Helpers                -
    #---------------------------------------------------

    def gameLoop(self, time=1, script="tick"):
        """Automatically increments in game timer over every iteration."""
        self.increment = time
        while True:
            yield self

            if self.next is not None:
                yield self.next
                self = self.next

            if not self.cont:
                return

            self.controlTime(self.increment, script=script)

    def exit(self):
        """Ends game if gameLoop is in use."""
        self.cont = False

    def resetState(self):
        """Resets game metadata to default."""
        self.state.clear()
        self.state.append(copy.deepcopy(self))
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
