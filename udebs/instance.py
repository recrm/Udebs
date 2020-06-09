from random import Random
from itertools import product, chain
from logging import info
from collections import deque
from copy import copy

from .interpret import Script, UdebsStr, _getEnv
from .board import Board
from .entity import Entity
from .utilities import norecurse
from .errors import UndefinedSelectorError

#---------------------------------------------------
#                 Main Class                       -
#---------------------------------------------------

class Instance(dict):
    """
    Main instance class that represents the state space of the entire game.

    Note on naming convention:

    All methods begining with 'get' return information about the game's state
    space and are not allowed to change the state itself.

    All methods beggining with 'control' or 'cast' manage some aspect of the state space
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
        self.rlist = ['group']
        self.rmap = []

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
        self.value = None # Value of the game.

        #internal
        self.map = {}
        self.delay = []
        self.rand = Random()

        #Do not copy
        self.state = False

    def __bool__(self):
        return self.cont

    @norecurse
    def __eq__(self, other):
        if not isinstance(other, Instance):
            return False

        for k,v in self.__dict__.items():
            if k not in ("state", "rand") and v != getattr(other, k):
                return False

        for k,v in self.items():
            if other[k] != v:
                return False

        if len(self) != len(other):
            return False

        return True

    def __ne__(self, other):
        return not self == other

    def __copy__(self):
        return self.copy()

    def copy(self, new=None):
        if new is None:
            new = type(self)(True)

        for k, v in self.__dict__.items():
            if k not in {"delay", "map", "state"}:
                setattr(new, k, v)

        # Handle entities
        for name, entity in self.items():
            if entity.immutable:
                new[name] = entity
            else:
                new[name] = entity.copy()

        # Handle maps
        new.map = {}
        for name, map_ in self.map.items():
            new.map[name] = map_.copy()

        # Handle delays
        new.delay = []
        for delay in self.delay:
            env = copy(delay["env"])
            env["self"] = new
            env["storage"] = {k: new[v.name] for k,v in delay["env"]["storage"].items()}

            new.delay.append({
                "env": env,
                "ticks": delay["ticks"],
                "script": delay["script"],
            })

        new.state = copy(self.state)

        return new

    #---------------------------------------------------
    #               Selector Function                  -
    #---------------------------------------------------

    def getEntity(self, target, multi=False):
        """
        Fetches the udebs entity object given a selector.

        Udebs selectors can take all of the following forms.

        * string - The name of the object we are looking for.
        * tuple - A tuple of the form (x, y, mapname) representing a location on a map.
        * list - A list containing other selectors.
        * False - Returns the default empty selector.

        .. code-block:: python

            main_map.getEntity("empty")

        """
        if isinstance(target, Entity):
            return target
        elif target is False or target == "bump":
            return self['empty']
        elif isinstance(target, str) and target in self:
            return self[target]
        elif isinstance(target, tuple):
            return self._getEntityTuple(target)
        elif isinstance(target, list):
            if multi:
                return [self.getEntity(i) for i in target]
            elif len(target) > 0:
                return self.getEntity(target[0])
        elif isinstance(target, UdebsStr):
            return self._getEntityUdebsStr(target)

        raise UndefinedSelectorError(target, "entity")

    def _getEntityUdebsStr(self, target):
        #Process new nameless.
        scripts = []
        if target[0] == "(":
            while target[0] == "(":
                target = target[1:-1]

            bracket = 0
            buf = []
            for char in target:
                if char == "(":
                    bracket +=1

                if char == ")":
                    bracket -=1

                if not bracket and char == ",":
                    scripts.append(Script(UdebsStr("".join(buf)), self.version))
                    buf = []
                    continue

                buf.append(char)

            raw = UdebsStr("".join(buf))
            scripts.append(Script(raw, self.version))

        else:
            scripts.append(Script(target, self.version))

        self[target] = Entity(self, require=scripts, name=target, immutable=True)
        return self[target]

    def _getEntityTuple(self, target):
        map_ = self.getMap(target)
        try:
            name = map_[target]
        except (IndexError, TypeError):
            raise UndefinedSelectorError(target, "entity")

        unit = self[name]

        if not unit.loc:
            if len(target) < 3:
                target = (*target, map_.name)
            unit = unit.copy(loc=target)

        return unit

    def getMap(self, target="map"):
        """
        Fetches the map object caster currently resides on.

        .. code-block:: xml

            <i>caster [$caster] MAP</i>
        """
        if isinstance(target, tuple):
            target = target[2] if len(target) == 3 else "map"
        if not target:
            return False
        elif isinstance(target, str) and target in self.map:
            return self.map[target]
        elif isinstance(target, Board):
            return target
        elif isinstance(target, Entity):
            return self.map[target.loc[2]]
        else:
            raise UndefinedSelectorError(target, "map")

    #---------------------------------------------------
    #                 Time Management                  -
    #---------------------------------------------------

    def _checkDelay(self):
        """Checks and runs actions waiting in delay."""
        while True:
            again = False
            for delay in self.delay[:]:
                if delay['ticks'] <= 0:
                    self.delay.remove(delay)
                    delay['script'](delay['env'])
                    again = True

            if not again:
                break

        if self.logging:
            info("")

    def controlTime(self, time=None, script="tick"):
        """
        Increments internal time by 'time' ticks, runs tick script, and activates any delayed effects.

        .. code-block:: xml

            <i>TIME time</i>
        """
        if time == None:
            time = self.increment

        for i in range(time):
            # Increment time
            self.time +=1
            if self.logging:
                info(f'Env time is now {self.time}')

            # Processs tick script
            if script in self:
                self.castMove(self["empty"], self["empty"], self[script])

            if self.delay:
                for delay in self.delay:
                    delay['ticks'] -=1

                if self.logging:
                    info("Processing delayed effects")
                self._checkDelay()

            #Append new version to state.
            if self.state:
                self.state.append(self.copy())

        return self.cont

    def getRevert(self, time=0):
        """
        Returns a previous game state.

        Note: time represents how many ticks to revert.

        .. code-block:: python

            main_map.getRevert(5)
        """

        new_states = self.state.copy()
        if self.state:
            for i in range(time + 1):
                try:
                    new = new_states.pop()
                except IndexError:
                    return False

            new.state = new_states
            new.state.append(new.copy())
            return new

    def controlDelay(self, callback, time, storage):
        """
        Delays an effect a number of ticks.

        Note: A delay of 0 will delay an action until the end of the current action window.
        Note: Notice the backtick.

        .. code-block:: xml

            <i>DELAY `(caster CAST target move) 0</i>
        """
        env = _getEnv(storage, {"self": self})

        new_delay = {
            "env": env,
            "script": self.getEntity(callback),
            "ticks": time
        }

        self.delay.append(new_delay)
        if self.logging:
            info(f"effect added to delay for {time}")
        return True

    @norecurse
    def testFuture(self, caster, target, move, callback, time=0):
        """
        Experimental function. Checks if condition is true in the future.
        (Works for chess, I doubt I will touch it.)

        caster, target, move - Event to trigger.
        callback - Condition to check in the future.
        time - how much time to travel into the future.
        """
        caster = self.getEntity(caster)
        target = self.getEntity(target)
        move = self.getEntity(move)

        #create test instance
        clone = self.copy()
        clone.revert = 0
        clone.logging=False

        #convert instance targets into clone targets.
        caster = clone.getEntity(caster.loc)
        target = clone.getEntity(target.loc)
        move = clone.getEntity(move.name)

        #Send clone into the future.
        env = clone._getEnv(caster, target, move)
        move.controlEffect(env)
        clone.controlTime(time)

        effects = clone.getEntity(callback)
        test = clone.testMove(caster, target, effects)

        return test

    #---------------------------------------------------
    #           Coorporate get functions               -
    #---------------------------------------------------

    def getStat(self, target, stat):
        """
        General getter for all attributes.

        Note: Attributes will include values inherited from their group.

        .. code-block:: xml

            <i>target [$caster] STAT stat</i>
        """
        current = self.getEntity(target)
        if stat in {"increment", "group"}:
            return getattr(current, stat)
        elif stat == "envtime":
            return self.time
        elif stat not in self.lists.union(self.stats).union(self.strings):
            raise UndefinedSelectorError(stat, "stat")

        values = self._getStatHelper(current, stat)

        # rmaps only apply to current object not rlists.
        if current.loc:
            for map_ in self.rmap:
                if map_ != current.loc[2]:
                    child = self.getEntity((current.loc[0], current.loc[1], map_))
                    values = chain(values, self._getStatHelper(child, stat))

        if stat in self.stats:
            return sum(values)
        elif stat in self.lists:
            return [i for j in values for i in j]
        elif stat in self.strings:
            for i in values:
                if i != "":
                    return i
            else:
                return ""

    def _getStatHelper(self, target, stat):
        yield getattr(target, stat)
        for lst in self.rlist:
            for unit in getattr(target, lst):
                if isinstance(unit, str):
                    unit = self[unit]
                yield from self._getStatHelper(unit, stat)

    def getGroup(self, group):
        """Return all objects belonging to group.

         .. code-block:: xml

            <i>ALL group</i>
        """
        groupname = self.getEntity(group).name
        values = [unit for unit in self if groupname in self[unit].group]
        # sorted is required to force algorithm to be deterministic
        return sorted(values)

    def getListStat(self, target, lst, stat):
        """
        Returns sum of all object stats in a list.

        .. code-block:: xml

            <i>target [$caster] lst LISTSTAT stat</i>
        """
        target = self.getEntity(target)
        lst = self.getStat(target, lst)

        found = (self.getStat(element, stat) for element in lst)

        if stat in self.stats:
            return sum(found)
        elif stat in self.lists:
            return list(i for j in found for i in j)
        elif stat in self.strings:
            return next(found)

    def getListGroup(self, target, lst, group):
        """
        Returns first element in list that is a member of group.

        .. code-block:: xml

            <i>target [$caster] lst LISTGROUP group</i>
            <i>target [$caster] CLASS group</i>
        """
        group = self.getEntity(group)

        start = self.getStat(target, lst)
        for item in start:
            if group.name in self[item].group:
                return item
        return False

    def getSearch(self, *args):
        """
        Return objects contained in all given groups.

        .. code-block:: xml

            <i>SEARCH arg1 arg2 ...</i>
        """
        foundIter = iter(args)
        first = foundIter.__next__()
        found = set(self.getGroup(first))
        for arg in args:
            found = found.intersection(self.getGroup(arg))
        # sorted is required to force algorithm to be deterministic
        return sorted(list(found))

    #---------------------------------------------------
    #                 Call wrappers                    -
    #---------------------------------------------------

    def _getEnv(self, caster, target, move):
        """Internal method for creating contexts for calls."""

        var_local = {
            "caster": caster,
            "target": target,
            "move": move,
            "C": caster,
            "T": target,
            "M": move,
        }
        return _getEnv(var_local, {"self": self})

    def _controlMove(self, casters, targets, moves):
        """
        Function to trigger an event. Returns True if an action triggers succesfully.

        Note: If a list of entity selectors is recieved for any argument, all actions in the product will trigger.
        """
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

                if target == caster == self["empty"]:
                    info(f"init {move}")
                elif target == self["empty"]:
                    info(f"{cname} uses {move}")
                else:
                    info(f"{cname} uses {move} on {tname}")

            # Cast the move
            test = move(self._getEnv(caster, target, move))
            if test == True:
                value = True
            elif self.logging:
                info(f"failed because {test}")

        return value

    def testMove(self, caster, target, move):
        """
        Simulates an action. Returns true if require passes succesfully, False otherwise.

        .. code-block:: python

            main_map.testMove(caster, target, move)

        """
        move = self.getEntity(move)
        env = self._getEnv(caster, target, move)
        return move.testRequire(env) == True

    def castInit(self, moves):
        """Cast an action without variables.

        .. code-block:: xml

            <i>INIT move</i>
        """
        return self.castMove(self["empty"], self["empty"], moves)

    def castAction(self, caster, move):
        """Cast an action with only a caster.

        .. code-block:: xml

            <i>caster [$caster] ACTION move</i>
        """
        return self.castMove(caster, self["empty"], move)

    def castMove(self, caster, target , move):
        """Cast an action including both a caster and an action.

        .. code-block:: xml

            <i>caster [$caster] CAST target move</i>
        """
        value = self._controlMove(caster, target, move)
        if value:
            self._checkDelay()

        return value

    def castSingle(self, string):
        """
        Call a function directly from a user inputed effect String.

        .. code-block:: python

            main_map.castSingle("caster CAST target move")
        """
        code = Script(string, version=self.version)
        env = _getEnv({}, {"self": self})
        return code(env)

    #---------------------------------------------------
    #               Entity control                     -
    #---------------------------------------------------
    def controlListAdd(self, targets, lst, entries):
        """
        Adds an element to a list.

        .. code-block:: xml

            <i>caster [$caster] lst GETS entries</i>
        """

        targets = self.getEntity(targets, multi=True)
        if not isinstance(entries, list):
            entries = [entries]

        for target, entry in product(targets, entries):
            if not target.immutable:
                getattr(target, lst).append(entry)
                if self.logging:
                    info(f"{entry} added to {target} {lst}")

    def controlListRemove(self, targets, lst, entries):
        """
        Removes an element from a list.

        .. code-block:: xml

            <i>caster [$caster] lst LOSES entries</i>
        """

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
        """
        Removes all from a targets list attribute.

        .. code-block:: xml

            <i>target [$caster] CLEAR lst</i>
        """

        for target in self.getEntity(targets, multi=True):
            if not target.immutable:
                getattr(target, lst).clear()
                if self.logging:
                    info(f"{target} {lst} has been cleared")

    def controlShuffle(self, target, lst):
        """
        Randomize order of a list.

        .. code-block:: xml

            <i>target SHUFFLE lst</i>
        """

        for target in self.getEntity(target, multi=True):
            if not target.immutable:
                self.rand.shuffle(getattr(target, lst))
                if self.logging:
                    info(f"{target} {lst} has been shuffled")

    def controlIncrement(self, targets, stat, increment, multi=1):
        """
        Increment a statistic by a static value.

        Note: Final value will be modified as follows (Stat = Stat + (increment * multi))

        .. code-block:: xml

            <i>target stat += increment</i>
            <i>target stat -= increment</i>
            <i>target [$caster] stat CHANGE increment</i>
        """

        total = int(increment * multi)
        for target in self.getEntity(targets, multi=True):
            if not target.immutable:
                setattr(target, stat, getattr(target, stat) + total)
                if self.logging:
                    info(f"{target} {stat} changed by {total} is now {self.getStat(target, stat)}")

    def controlString(self, targets, stat, value):
        """
        Replace a value with another value.

        Note: This function also works on all attributes.

        .. code-block:: xml

            <i>caster [$caster] stat REPLACE value</i>
        """

        for target in self.getEntity(targets, multi=True):
            if not target.immutable:
                setattr(target, stat, value)
                if self.logging:
                    info(f"{target} {stat} changed to {value}")

    def controlRecruit(self, target, positions):
        """
        Create a new entity by copying another then move it to a position.

        Note: If position is set to False copy will be made but not moved into a location.
        Note: One new entity will be created for each position given.

        .. code-block:: xml

            <i>caster [$caster] RECRUIT position</i>
        """

        target = self.getEntity(target)
        new = target
        for position in positions if isinstance(positions, list) else [positions]:
            if not target.immutable:
                new = target.clone()
                self[new.name] = new
                if self.logging:
                    info(f"{new} has been recruited")
            self.controlTravel(new, position)

        return new

    def controlDelete(self, target):
        """
        Permanently remove an object from the game.

        .. code-block:: xml

            <i>target DELETE</i>
        """

        target = self.getEntity(target)
        if not target.immutable:
            del self[target.name]
            if target.loc:
                del self.getMap(target)[target.loc]
            if self.logging:
                info(f"{target} has been deleted")
            return True
        return False

    #---------------------------------------------------
    #                 Entity get wrappers              -
    #---------------------------------------------------

    def getX(self, target, value=0):
        """
        Gets the x coordinate of target, False if target not on a map.

        .. code-block:: xml

            <i>target [$caster] XLOC</i>
        """

        unit = self.getEntity(target)
        return unit.loc[value] if unit.loc else False

    def getY(self, target):
        """
        Gets the y coordinate of target, False if target not on a map.

        .. code-block:: xml

            <i>target [$caster] YLOC</i>
        """
        return self.getX(target, 1)

    def getMapName(self, target):
        """
        Gets the y coordinate of target, False if target not on a map.

        .. code-block:: xml

            <i>target [$caster] MAPNAME</i>
        """
        return self.getX(target, 2)

    def getLoc(self, target):
        """
        Gets the location tuple of a target, False if target not on a map.

        .. code-block:: xml

            <i>target [$caster] LOC</i>
        """
        return self.getEntity(target).loc

    def getName(self, target):
        """
        Gets the name of a target.

        .. code-block:: xml

            <i>target [$caster] NAME</i>
        """
        return self.getEntity(target).name

    #---------------------------------------------------
    #                 Board get wrappers               -
    #---------------------------------------------------

    def mapIter(self, mapname="map"):
        """Iterate over all cells in a map."""
        map_ = self.getMap(mapname)
        for loc in map_:
            yield self.getEntity(loc)

    def getPath(self, caster, target, callback):
        """
        Finds a path between caster and target using callback as filter for valid space.

        .. code-block:: xml

            <i>PATH callback caster [$caster] target [$target]</i>
        """
        caster = self.getEntity(caster).loc
        target = self.getEntity(target).loc
        callback = self.getEntity(callback)

        map_ = self.getMap(caster)
        if map_ and map_.testLoc(target):
            return map_.getPath(caster, target, callback=callback, state=self)

        return []

    def getDistance(self, caster, target, method):
        """
        Returns distance between caster and target using method as a metric.

        .. code-block:: xml

            <i>PATH method caster [$caster] target [$target]</i>
        """

        caster = self.getEntity(caster).loc
        target = self.getEntity(target).loc
        if method in self:
            method = self.getEntity(method)

        map_ = self.getMap(caster)
        if map_ and map_.testLoc(target):
            return map_.getDistance(caster, target, method, state=self)

        return float("inf")

    def testBlock(self, caster, target, callback):
        """
        Test to see if path exists between caster and target using callback as filter for valid space.

        .. code-block:: xml

            <i>BLOCK callback caster [$caster] target [$target]</i>
        """
        caster = self.getEntity(caster).loc
        target = self.getEntity(target).loc
        callback = self.getEntity(callback)

        map_ = self.getMap(caster)
        if map_ and map_.testLoc(target):
            return map_.testBlock(caster, target, callback=callback, state=self)

        return False

    def getFill(self, center, callback=False, include_center=True, distance=float("inf")):
        """
        Gets all squares in a pattern starting at center, using callback as filter for valid space.

        .. code-block:: xml

            <i>FILL center callback include_center [true] distance [null]</i>
        """
        if distance is None:
            distance = float("inf")

        center = self.getEntity(center).loc
        callback = self.getEntity(callback)
        map_ = self.getMap(center)
        if map_:
            fill = sorted(map_.getFill(center, distance, include_center,
                                       callback=callback, state=self))
            self.rand.shuffle(fill)
            return fill

        return []

    def printMap(self, board="map"):
        """Print a map."""
        self.getMap(board).show()

    #---------------------------------------------------
    #              Board control wrappers              -
    #---------------------------------------------------
    def controlTravel(self, caster, targets=False):
        """Move one object to a new location.

        .. code-block:: xml

            <i>caster [$caster] MOVE target</i>
        """

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
                self.getMap(target.loc)[target.loc] = caster.name
                if not target.immutable:
                    target.loc = False

                if self.logging:
                    info(f"{caster} has moved to {target.loc}")

            # Update the entity itself.
            if not caster.immutable:
                caster.loc = loc

    #---------------------------------------------------
    #                 Game Loop Helpers                -
    #---------------------------------------------------

    def gameLoop(self, time=1, script="tick"):
        """Iterate over in game time.

        .. code-block:: python

            for state in main_map.gameLoop():
                state.castMove(caster, target, move)
        """
        self.increment = time
        while self.cont:
            yield self

            if self.next is not None:
                yield self.next
                self = self.next

            self.controlTime(self.increment, script=script)

        if self.logging:
            info(f"EXITING {self.name}\n")

    def exit(self, value=1):
        """Requests the end of the game by setting Instance.cont to False, and exiting out of the gameloop.

        .. code-block:: xml

            <i>EXIT</i>
        """
        if self.logging:
            info("Exit requested with value of: {}".format(value))
        self.cont = False
        self.value = value

    def resetState(self, script="reset"):
        """Resets the game metadata to default.

        .. code-block:: python

            main_map.resetState()
        """
        self.cont = True
        self.value = None
        self.time = 0
        self.delay.clear()
        if self.logging:
            info(f"Env time is now {self.time}")

        if script in self:
            self.castMove(self["empty"], self["empty"], self[script])
        elif self.logging:
            info("")

        if self.state:
            self.state.clear()
            self.state.append(self.copy())