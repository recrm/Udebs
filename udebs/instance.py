from copy import copy
from itertools import product, chain
from logging import info
from random import Random

from .board import Board
from .entity import Entity
from .errors import UndefinedSelectorError, UdebsExecutionError
from .interpret import Script, UdebsStr, _getEnv
from .utilities import no_recurse


# ---------------------------------------------------
#                 Main Class                        -
# ---------------------------------------------------

class Instance(dict):
    """
    Main instance class that represents the state space of the entire game.

    Note on naming convention:

    All methods beginning with 'get' return information about the game's state
    space and are not allowed to change the state itself.

    All methods beginning with 'control' or 'cast' manage some aspect of the state space
    and return true if changes were (probably) made and false otherwise.

    Other functions are convenience wrappers for public use.
    """

    def __init__(self, is_copy=False):
        if is_copy:
            return

        # definitions
        self.lists = {'group', 'effect', 'require'}
        self.stats = set()
        self.strings = set()
        # rlist and rmap are flags that indicate objects entities should inherit from.
        self.rlist = ['group']
        self.rmap = []

        # config
        self.name = 'Unknown'  # only effects what is printed when initialized
        self.logging = True  # Turns logging on and off
        self.revert = 0  # Determines how many steps should be saved in revert
        self.version = 1  # What version of Udebs syntax is used.
        self.seed = None  # Random seed for processing.
        self.immutable = False  # Determines default setting for entities immutability.
        self.auto_entity = True

        # time
        self.time = 0  # In game counter
        self.increment = 1  # how much time passes between game_loop iterations. Useful for pausing.
        self.cont = True  # Flag to determine if game_loop should continue
        self.next = None  # The next state a game_loop will return. Useful for resets and reverts in game_loop
        self.value = None  # Value of the game.

        # internal
        self.map = {}
        self.delay = []
        self.rand = Random()

        # Do not copy
        self.state = None

        super().__init__()

    def __bool__(self):
        return self.cont

    @no_recurse
    def __eq__(self, other):
        if not isinstance(other, Instance):
            return False

        for k, v in self.__dict__.items():
            if k not in ("state", "rand") and v != getattr(other, k):
                return False

        for k, v in self.items():
            if other[k] != v:
                return False

        if len(self) != len(other):
            return False

        return True

    def __ne__(self, other):
        return not self == other

    def __copy__(self):
        return self.copy()

    def copy(self, new=None) -> "Instance":
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
            env["storage"] = {k: new[v.name] for k, v in delay["env"]["storage"].items()}

            new.delay.append({
                "env": env,
                "ticks": delay["ticks"],
                "script": delay["script"],
            })

        new.state = None

        return new

    # ---------------------------------------------------
    #               Selector Function                  -
    # ---------------------------------------------------

    def getEntity(self, target):
        """
        Fetches the udebs entity object given a selector.

        Udebs selectors can take all of the following forms.

        * string - The name of the object we are looking for.
        * tuple - A tuple of the form (x, y, name) representing a location on a map.
        * list - A list containing other selectors.
        * None - Returns the default empty selector.

        .. code-block:: xml

            <i># identifier</i>

        """
        if isinstance(target, Entity):
            return target
        elif target is False or target is None or target == "bump":
            return self['empty']
        elif isinstance(target, str) and target in self:
            return self[target]
        elif isinstance(target, tuple):
            return self._getEntityTuple(target)
        elif isinstance(target, list):
            return [self.getEntity(i) for i in target]
        elif isinstance(target, UdebsStr):
            return self._getEntityUdebsStr(target)

        raise UndefinedSelectorError(target, "entity")

    def _getEntityUdebsStr(self, target):
        # Process new nameless.
        scripts = []
        if target[0] == "(":
            while target[0] == "(":
                target = target[1:-1]

            bracket = 0
            buf = []
            for char in target:
                if char == "(":
                    bracket += 1

                if char == ")":
                    bracket -= 1

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
        if len(target) < 3:
            map_name = "map"
        else:
            map_name = target[2]

        try:
            name = self.map[map_name][target]
        except (IndexError, TypeError, KeyError):
            raise UndefinedSelectorError(target, "entity")

        unit = self[name]

        if not unit.loc:
            if len(target) < 3:
                target = (*target, map_name)
            unit = unit.copy(loc=target)

        return unit

    def getLocObject(self, target):
        if isinstance(target, tuple):
            if len(target) < 3:
                target = (*target, "map")
            return target
        return self.getEntity(target).loc

    def getMap(self, target="map"):
        """
        Fetches the map object caster currently resides on.

        .. code-block:: xml

            <i>caster [$caster] MAP</i>
        """
        if isinstance(target, tuple):
            target = target[2] if len(target) == 3 else "map"
        if not target:
            return None
        elif isinstance(target, str) and target in self.map:
            return self.map[target]
        elif isinstance(target, Board):
            return target
        elif isinstance(target, Entity):
            return self.map[target.loc[2]]
        else:
            raise UndefinedSelectorError(target, "map")

    # ---------------------------------------------------
    #                 Time Management                  -
    # ---------------------------------------------------

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
        if time is None:
            time = self.increment

        for i in range(time):
            # Increment time
            self.time += 1
            if self.logging:
                info(f'Env time is now {self.time}')

            # Process tick script
            if script in self:
                self.castMove(self["empty"], self["empty"], self[script])

            if self.delay:
                for delay in self.delay:
                    delay['ticks'] -= 1

                if self.logging:
                    info("Processing delayed effects")
                self._checkDelay()

            # Append new version to state.
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

        if self.state:
            new_states = self.state.copy()
            new = self
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
        Note: Notice the back tick.

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

    @no_recurse
    def testFuture(self, caster, target, move, callback, time=0):
        """
        Experimental function. Checks if condition is true in the future.
        (Works for chess, I doubt I will touch it.)

        caster, target, move - Event to trigger.
        callback - Condition to check in the future.
        time - how much time to travel into the future.
        """
        if self.auto_entity:
            caster = self.getEntity(caster)
            target = self.getEntity(target)
            move = self.getEntity(move)

        # create test instance
        clone = self.copy()
        clone.revert = 0
        clone.logging = False

        # convert instance targets into clone targets.
        caster = clone.getEntity(caster.loc)
        target = clone.getEntity(target.loc)
        move = clone.getEntity(move.name)

        # Send clone into the future.
        env = clone.getEnv(caster, target, move)
        move.controlEffect(env)
        clone.controlTime(time)

        effects = clone.getEntity(callback)
        test = clone.testMove(caster, target, effects)

        return test

    # ---------------------------------------------------
    #           Corporate get functions                 -
    # ---------------------------------------------------

    def getStat(self, target, stat):
        """
        General getter for all attributes.

        Note: Attributes will include values inherited from their group.

        .. code-block:: xml

            <i>target [$caster] STAT stat</i>
        """
        if self.auto_entity:
            target = self.getEntity(target)
        if stat in {"increment", "group"}:
            return getattr(target, stat)
        elif stat == "envtime":
            return self.time
        elif stat not in self.lists.union(self.stats).union(self.strings):
            raise UndefinedSelectorError(stat, "stat")

        values = self._getStatHelper(target, stat)

        # rmap only apply to current object not rlist.
        if target.loc:
            for map_ in self.rmap:
                if map_ != target.loc[2]:
                    child = self[self.map[map_][target.loc]]
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

    def getGroup(self, group: str):
        """Return all objects belonging to group.

         .. code-block:: xml

            <i>ALL group</i>
        """
        if self.auto_entity < 3:
            group = self.getEntity(group)

        return [unit for unit in self.values() if group.name in unit.group]

    def getListStat(self, target, lst, stat):
        """
        Returns sum of all object stats in a list.

        .. code-block:: xml

            <i>target [$caster] lst LISTSTAT stat</i>
        """
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
        if self.auto_entity:
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
        found = []
        for arg in args:
            for new in self.getGroup(arg):
                if new not in found:
                    found.append(new)

        return found

    # ---------------------------------------------------
    #                 Call wrappers                    -
    # ---------------------------------------------------

    def getEnv(self, caster, target, move):
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
        Function to trigger an event. Returns True if an action triggers successfully.

        Note: If a list of entity selectors is received for any argument, all actions in the product will trigger.
        """
        if self.auto_entity:
            casters = self.getEntity(casters)
            targets = self.getEntity(targets)
            moves = self.getEntity(moves)

        value = False

        for caster, target, move in product(casters, targets, moves):
            if self.logging:
                # Logging
                caster_name = caster
                if caster.immutable and caster.loc:
                    caster_name = caster.loc

                target_name = target
                if target.immutable and target.loc:
                    target_name = target.loc

                if target == caster == self["empty"]:
                    info(f"init {move}")
                elif target == self["empty"]:
                    info(f"{caster_name} uses {move}")
                else:
                    info(f"{caster_name} uses {move} on {target_name}")

            # Cast the move
            env = self.getEnv(caster, target, move)
            for require in self.getStat(move, 'require'):
                try:
                    if not eval(require.code, env):
                        if self.logging:
                            info(f"failed because {require}")
                        break
                except Exception:
                    raise UdebsExecutionError(require)
            else:
                for effect in self.getStat(move, 'effect'):
                    try:
                        eval(effect.code, env)
                    except Exception:
                        raise UdebsExecutionError(effect)

                value = True

        return value

    def testMove(self, caster, target, move):
        """
        Simulates an action. Returns true if require passes successfully, False otherwise.

        .. code-block:: python

            main_map.testMove(caster, target, move)

        """
        if self.auto_entity:
            move = self.getEntity(move)
        env = self.getEnv(caster, target, move)
        return move.testRequire(env) is True

    def castInit(self, moves, times=1):
        """Cast an action without variables.

        .. code-block:: xml

            <i>INIT move</i>
        """
        for i in range(times):
            if not self.castMove(self["empty"], self["empty"], moves):
                return False

        return True


    def castAction(self, caster, move):
        """Cast an action with only a caster.

        .. code-block:: xml

            <i>caster [$caster] ACTION move</i>
        """
        return self.castMove(caster, self["empty"], move)

    def castMove(self, caster, target, move):
        """Cast an action including both a caster and an action.

        .. code-block:: xml

            <i>caster [$caster] CAST target move</i>
        """
        caster = self.getEntity(caster)
        target = self.getEntity(target)
        move = self.getEntity(move)

        value = self._controlMove(caster, target, move)
        if value:
            self._checkDelay()

        return value

    def castSingle(self, string):
        """
        Call a function directly from a user input effect String.

        .. code-block:: python

            main_map.castSingle("caster CAST target move")
        """
        code = Script(string, version=self.version)
        env = _getEnv({}, {"self": self})
        return code(env)

    # ---------------------------------------------------
    #               Entity control                     -
    # ---------------------------------------------------
    def controlListAdd(self, targets, lst, entries):
        """
        Adds an element to a list.

        .. code-block:: xml

            <i>caster [$caster] lst GETS entries</i>
        """
        if self.auto_entity:
            targets = self.getEntity(targets)

        if not isinstance(entries, list):
            entries = [entries]

        changed = False
        for target, entry in product(targets, entries):
            if not target.immutable:
                getattr(target, lst).append(entry)
                changed = True
                if self.logging:
                    info(f"{entry} added to {target} {lst}")

        return changed

    def controlListRemove(self, targets, lst, entries):
        """
        Removes an element from a list.

        .. code-block:: xml

            <i>caster [$caster] lst LOSES entries</i>
        """
        if self.auto_entity:
            targets = self.getEntity(targets)

        if not isinstance(entries, list):
            entries = [entries]

        changed = False
        for target, entry in product(targets, entries):
            if not target.immutable:
                value = getattr(target, lst)
                if entry in value:
                    changed = True
                    value.remove(entry)
                    if self.logging:
                        info(f"{entry} removed from {target} {lst}")

        return changed

    def controlClear(self, targets, lst):
        """
        Removes all from a targets list attribute.

        .. code-block:: xml

            <i>target [$caster] CLEAR lst</i>
        """
        if self.auto_entity:
            targets = self.getEntity(targets)

        changed = False
        for target in targets:
            if not target.immutable:
                getattr(target, lst).clear()
                changed = True
                if self.logging:
                    info(f"{target} {lst} has been cleared")

        return changed

    def controlShuffle(self, targets, lst):
        """
        Randomize order of a list.

        .. code-block:: xml

            <i>target SHUFFLE lst</i>
        """
        if self.auto_entity:
            targets = self.getEntity(targets)

        changed = False
        for target in targets:
            if not target.immutable:
                self.rand.shuffle(getattr(target, lst))
                changed = True
                if self.logging:
                    info(f"{target} {lst} has been shuffled")

        return changed

    def controlIncrement(self, targets, stat, increment, multi=1):
        """
        Increment a statistic by a static value.

        Note: Final value will be modified as follows (Stat = Stat + (increment * multi))

        .. code-block:: xml

            <i>target stat += increment</i>
            <i>target stat -= increment</i>
            <i>target [$caster] stat CHANGE increment</i>
        """
        if self.auto_entity:
            targets = self.getEntity(targets)

        changed = False
        total = int(increment * multi)
        for target in targets:
            if not target.immutable:
                setattr(target, stat, getattr(target, stat) + total)
                changed = True
                if self.logging:
                    info(f"{target} {stat} changed by {total} is now {self.getStat(target, stat)}")

        return changed

    def controlString(self, targets, stat, value):
        """
        Replace a value with another value.

        Note: This function also works on all attributes.

        .. code-block:: xml

            <i>caster [$caster] stat REPLACE value</i>
        """
        if self.auto_entity:
            targets = self.getEntity(targets)

        changed = False
        for target in targets:
            if not target.immutable:
                setattr(target, stat, value)
                changed = True
                if self.logging:
                    info(f"{target} {stat} changed to {value}")

        return changed

    def controlRecruit(self, target, positions):
        """
        Create a new entity by copying another then move it to a position.

        Note: If position is set to False copy will be made but not moved into a location.
        Note: One new entity will be created for each position given.

        .. code-block:: xml

            <i>caster [$caster] RECRUIT position</i>
        """
        if self.auto_entity:
            target = self.getEntity(target)

        new = target
        if not isinstance(positions, list):
            positions = [positions]

        for position in positions:
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
        if self.auto_entity:
            target = self.getEntity(target)

        if not target.immutable:
            del self[target.name]
            if target.loc:
                del self.map[target.loc[2]][target.loc]
            if self.logging:
                info(f"{target} has been deleted")
            return True
        return False

    # ---------------------------------------------------
    #                 Entity get wrappers              -
    # ---------------------------------------------------

    def getX(self, target, value=0):
        """
        Gets the x coordinate of target, False if target not on a map.

        .. code-block:: xml

            <i>target [$caster] XLOC</i>
        """
        loc = self.getLocObject(target)
        return loc[value] if loc else None

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
        return self.getLocObject(target)

    def getName(self, target):
        """
        Gets the name of a target.

        .. code-block:: xml

            <i>target [$caster] NAME</i>
        """
        if self.auto_entity:
            target = self.getEntity(target)

        names = []
        for i in target:
            names.append(i.name)

        return names if len(names) > 1 else names[0]

    def getShift(self, target, x, y, name=None):
        """
        Returns a new loc shifted x and y units from an old one

        .. code-block:: xml

            <i>target [$caster] SHIFT x y</i>
        """
        loc = self.getLocObject(target)
        if loc is not None:
            new_name = name if name else loc[2]
            new_loc = loc[0] + x, loc[1] + y, new_name
            if self.map[new_name].testLoc(new_loc):
                return new_loc

        return self['empty']

    # ---------------------------------------------------
    #                 Board get wrappers               -
    # ---------------------------------------------------

    def mapIter(self, name="map"):
        """Iterate over all cells in a map."""
        map_ = self.map[name]
        for loc in map_:
            yield self[map_[loc]]

    def getPath(self, caster, target, callback):
        """
        Finds a path between caster and target using callback as filter for valid space.

        .. code-block:: xml

            <i>PATH callback caster [$caster] target [$target]</i>
        """
        caster = self.getLocObject(caster)
        if caster:
            target = self.getLocObject(target)
            callback = self.getEntity(callback)
            map_ = self.map[caster[2]]
            if map_.testLoc(target):
                return map_.getPath(caster, target, callback=callback, state=self)

        return []

    def getDistance(self, caster, target, method):
        """
        Returns distance between caster and target using method as a metric.

        .. code-block:: xml

            <i>PATH method caster [$caster] target [$target]</i>
        """

        caster = self.getLocObject(caster)
        if caster:
            target = self.getLocObject(target)
            if method in self:
                method = self.getEntity(method)

            map_ = self.map[caster[2]]
            if map_.testLoc(target):
                return map_.getDistance(caster, target, method, state=self)

        return float("inf")

    def testBlock(self, caster, target, callback, max_dist=None):
        """
        Test to see if path exists between caster and target using callback as filter for valid space.

        .. code-block:: xml

            <i>BLOCK callback caster [$caster] target [$target]</i>
        """
        caster = self.getLocObject(caster)
        if caster:
            target = self.getLocObject(target)
            callback = self.getEntity(callback)

            map_ = self.map[caster[2]]
            if map_.testLoc(target):
                return map_.testBlock(caster, target, callback=callback, state=self, max_dist=max_dist)

        return False

    def getFill(self, center, callback=False, include_center=True, distance=float("inf")):
        """
        Gets all squares in a pattern starting at center, using callback as filter for valid space.

        .. code-block:: xml

            <i>FILL center callback include_center [true] distance [null]</i>
        """
        if distance is None:
            distance = float("inf")

        center = self.getLocObject(center)
        if center:
            callback = self.getEntity(callback)
            map_ = self.map[center[2]]
            fill = sorted(map_.getFill(center, distance, include_center,
                                       callback=callback, state=self))
            self.rand.shuffle(fill)
            return fill

        return []

    def printMap(self, board="map"):
        """Print a map."""
        self.map[board].show()

    # ---------------------------------------------------
    #              Board control wrappers              -
    # ---------------------------------------------------
    def controlTravel(self, caster, targets=None):
        """Move one object to a new location.

        .. code-block:: xml

            <i>caster [$caster] MOVE target</i>
        """
        if self.auto_entity:
            caster = self.getEntity(caster)

        if not isinstance(targets, list):
            targets = [targets]

        if len(targets) > 1 and not caster.immutable:
            raise Exception("Non immutable entities cannot be moved to multiple locations.")

        for target in targets:
            # First remove caster from it's current location
            if not caster.immutable and caster.loc:
                del self.map[caster.loc[2]][caster.loc]

            # Then move caster to target location.
            target = self.getLocObject(target)
            if target:
                map_ = self.map[target[2]]
                unit_name = map_[target]
                unit_self = self[unit_name]

                map_[target] = caster.name
                if not unit_self.immutable:
                    unit_self.loc = None

                if self.logging:
                    info(f"{caster} has moved to {target}")

            # Update the entity itself.
            if not caster.immutable:
                caster.loc = target

    # ---------------------------------------------------
    #                 Game Loop Helpers                -
    # ---------------------------------------------------

    def gameLoop(self, time=1, script="tick"):
        """Iterate over in game time.

        .. code-block:: python

            for state in main_map.gameLoop():
                state.castMove(caster, target, move)
        """
        current = self

        current.increment = time
        while current.cont:
            yield current

            if current.next is not None:
                yield current.next
                current = current.next

            current.controlTime(current.increment, script=script)

        if current.logging:
            info(f"EXITING {current.name}\n")

    def exit(self, value=1):
        """Requests the end of the game by setting Instance.cont to False, and exiting out of the game_loop.

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
