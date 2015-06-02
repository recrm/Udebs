from udebs import interpret, board, entity
import random
import math
import copy
import itertools
import collections
import sys
import logging

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
        self.name = 'Unknown'
        self.logging = True
        self.revert = 1
        self.version = 1

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
            self.name == other.name,
            self.logging == other.logging,
            self.revert == other.revert,
            self.version == other.version,

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
            len(self) == len(other),
        ]
        #Note: self.state is specifically ignored.
        check.extend(self[e] == other[e] for e in self)
        return all(check)

    def __deepcopy__(self, memo):
        new = Instance()
        for k, v in self.__dict__.items():
            if k != "state":
                setattr(new, k, copy.deepcopy(v, memo))

        for e in new:
            new[e].field = new

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
    def getEntity(self, target, multi=False):
        """Returns entity object based on given selector.

        target - Any entity selector.
        multi - Boolean, allows lists of targets.

        """
        if target == False:
            return self['empty']

        ttype = type(target)

        #Already entity return self.
        if ttype is entity.Entity:
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
                if len(target) < 3:
                    target = (target[0], target[1], "map")

                unit = copy.deepcopy(unit)
                unit.loc = target

            return unit

        #If type is a list individually check each element.
        elif ttype is list:
            value = list(map(self.getEntity, target))
            if multi:
                return value
            return value[0]

        raise UndefinedSelectorError(target, "entity")

    def getMap(self, target="map"):
        """Returns first location for string in env.map."""
        if not target:
            return False

        ttype = type(target)
        if ttype is entity.Entity:
            return self.getMap(target.loc)
        elif ttype is board.Board:
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

    #---------------------------------------------------
    #                 Time Management                  -
    #---------------------------------------------------
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
                        delay['script'].call(delay['env'])
                        again = True

            logging.info('')

        checkdelay()
        for i in range(time):
            self.time +=1
            logging.info('Env time is now {}'.format(self.time))
            if 'tick' in self:
                self.controlInit(self['tick'])
            for delay in self.delay:
                delay['ticks'] -=1
            checkdelay()

            #Append new version to state.
            if self.revert > 1:
                clone = copy.deepcopy(self)
                self.state.append(clone)
                if len(self.state) > self.revert:
                    self.state = self.state[1:]

        return True

    def resetState(self):
        new = copy.deepcopy(self)
        self.state = [new]

    def getRevert(self, value=0):
        index = -(value +1)
        try:
            new = copy.deepcopy(self.state[index])
        except IndexError:
            return False

        new.state = self.state[:index+1]
        return new

    def controlDelay(self, caster, target, move, string, delay):
        """
        Creates a new delay object.

        """
        var_local = {
            "caster": caster,
            "target": target,
            "move": move,
            "C": caster,
            "T": target,
            "M": move,
        }
        env = interpret._getEnv(var_local, {"self": self})

        new_delay = {
            "env": env,
            "script": interpret.Script(string, self.version),
            "ticks": delay
        }

        self.delay.append(new_delay)
        logging.info("effect added to delay for {}".format(delay))
        return True

    def testFuture(self, caster, target, move, string, time=0):
        """
        Experimental function. Checks if condition is true in the future.
        (Works for chess, I doubt I will touch it.)

        caster, target, move - event to triger.
        time - how much time to pass after event.
        """
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

        #Test for condition
#        for effect in effects:
#            if self.asEntity(interpret.Script(effect, raw=False, require=True, version=self.version).testRequire

        effects = [interpret.Script(string, raw=False, require=True, version=self.version)]
        return clone.testMove(caster, target, move, effects)

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
            #classes
            for item in target['group']:
                value = self[item][stat]
                if value:
                    yield value

                #special lists
                for lst in self.rlist:
                    for unit in self[item][lst]:
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
        else:
            raise UndefinedStatError(stat)

    def getGroup(self, group, inc_self=False):
        """Return all objects belonging to group."""
        group = self.getEntity(group)

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
        ind - bool, only return first result if true."""
        foundIter = iter(args)
        first = foundIter.__next__()
        found = set(self.getGroup(first))
        for arg in args:
            found = found.intersection(self.getGroup(arg))
        return sorted(list(found))

    #---------------------------------------------------
    #                 Call wrappers                    -
    #---------------------------------------------------
    def controlMove(self, caster, targets, moves):
        """Main function to trigger an event."""
        targets = self.getEntity(targets, multi=True)
        moves = self.getEntity(moves, multi=True)

        for target in targets:
            for move in moves:
                logging.info("{} uses {} on {}".format(caster, move, target.loc if target.immutable else target))
                test = move.call(caster, target)
                if test != True:
                    logging.info("failed because {}".format(test))

    def controlInit(self, moves, time=0):
        """Wrapper of controlMove where caster and target are unimportant."""
        moves = self.getEntity(moves, multi=True)
        for move in moves:
            logging.info("{} has been triggered.".format(move))
            move.call(self["empty"], self["empty"])

        self.controlTime(time)

    def castMove(self, caster, target , move, time=0):
        """Wrapper of controlMove that appends a tick."""
        self.controlMove(caster, target, move)
        self.controlTime(time)

    def testMove(self, caster, target, move):
        """Gutted controlMove, returns if event would have activated."""
        move = self.getEntity(move)
        return move.testRequire(caster, target) == True

    #---------------------------------------------------
    #               Entity control wrappers            -
    #---------------------------------------------------
    def controlList(self, targets, lst, entries, command):
        targets = self.getEntity(targets, multi=True)
        if not isinstance(entries, list):
            entries = [entries]

        for target in targets:
            for entry in entries:
                if command == "add":
                    self.getEntity(target).controlListAdd(lst, entry)
                    logging.info("{} added to {} {}".format(entry, target, lst))
                elif command == "remove":
                    self.getEntity(target).controlListRemove(lst, entry)
                    logging.info("{} removed from {} {}".format(entry, target, lst))

    def controlClear(self, targets, lst):
        targets = self.getEntity(targets, multi=True)

        for target in targets:
            target.controlListClear(lst)
            logging.info("{} {} has been cleared.".format(target, lst))

    def controlIncrement(self, targets, stat, increment, multi=1):
        targets = self.getEntity(targets, multi=True)

        for target in targets:
            target.controlIncrement(stat, increment, multi)
            logging.info("{} {} changed by {} is now {}".format(target, stat, increment, self.getStat(target, stat)))

    def controlString(self, targets, stat, value):
        targets = self.getEntity(targets, multi=True)
        if value:
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

    def getFill(self, center, callback=False, distance=float("inf")):
        center = self.getEntity(center).loc
        callback = self.getEntity(callback)
        return self.getMap(center).getFill(center, callback, distance)

    #---------------------------------------------------
    #              Board control wrappers              -
    #---------------------------------------------------
    def controlTravel(self, caster, targets=False):
        caster = self.getEntity(caster)
        targets = self.getEntity(targets, multi=True)

        for target in targets:
            if target.loc:
                self.getMap(target).controlMove(caster.name, target.loc)
                logging.info("{} has moved to {}".format(caster, target.loc))
                target.controlLoc()

            if not caster.immutable and caster.loc:
                self.getMap(caster.loc).controlBump(caster.loc)

            caster.controlLoc()

    #---------------------------------------------------
    #                    Other                         -
    #---------------------------------------------------
    def asEntity(self, script, stat_list):
        """Convets individual scripts to callable functions."""
        if isinstance(script, str):
            script = interpret.Script(script, self.version)

        return entity.Entity(self, {stat_list: [script]})

#---------------------------------------------------
#                     Errors                       -
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
