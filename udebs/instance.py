import logging
from itertools import product
from random import Random
from typing import Any, Optional, Self
import re

from udebs.board import Board, Location, FullLocation
from udebs.entity import Entity, FullEntity
from udebs.errors import UndefinedSelectorError
from udebs.interpret import Script, register, Variables
from udebs.utilities import no_recurse

info = logging.getLogger().info

Variables.modules.update({
    "DICE": {
        "f": "self.rand.randint",
        "args": [0, "$1"]
    },
    "RAND_CHOICE": {
        "f": "self.rand.choice",
        "args": ["$1"]
    },
    "VAR": {
        "f": "getattr",
        "args": ["self", "$1"]
    }
})


def _getStatRmap(state, target, stat):
    yield from _getStatInheritance(state, target, stat)

    # rmap only apply to the current object not rlist.
    if target.loc:
        for map_ in state.rmap:
            if map_ != target.loc[2]:
                child = state[state.map[map_][target.loc]]
                yield from _getStatInheritance(state, child, stat)


def _getStatInheritance(state, target, stat):
    yield getattr(target, stat)
    for lst in state.rlist:
        for unit in getattr(target, lst):
            yield from _getStatInheritance(state, state[unit], stat)


def board_creator(board_type: str, options: dict[Any]):
    if board_type in {"diag", "hex", "square"}:
        from udebs.modules import flat_map
        if "dim" in options:
            options["dim"] = (int(options["dim"]["x"]), int(options["dim"]["y"]))

        if "row" in options:
            temp = [re.split(r"\W*,\W*", i) for i in options["row"]]
            options["overwrite_map"] = [list(j) for j in zip(*temp)]

        formated_options = {"name": options.get("name"), "empty": options.get("empty", "empty"),
                            "dim": options.get("dim"), "overwrite_map": options.get("overwrite_map")}

        if board_type == "diag":
            return flat_map.DiagMap(**formated_options)
        elif board_type == "hex":
            return flat_map.HexMap(**formated_options)
        else:
            return flat_map.SquareMap(**formated_options)

    elif board_type == "card_stack":
        from udebs.modules import card_stack
        players = list(options["players"].keys())
        spaces = list(options["spaces"].keys())
        return card_stack.CardStack(options["name"], options.get("empty", "empty"), players, spaces)

    else:
        raise UndefinedSelectorError(board_type, "board_type")


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

    def __init__(self, is_copy=False, init="init", **options):
        if is_copy:
            return

        # definitions
        self.lists = {"effect", "require", "group"} | options.get("lists", set())
        self.stats = {"increment"} | options.get("stats", set())
        self.strings = {"name"} | options.get("strings", set())
        # rlist and rmap are flags that indicate objects entities should inherit from.
        self.rlist = ["group"] + options.get("rlist", [])

        # config
        self.name = options.get("name", 'Unknown')  # only effects what is printed when initialized
        self.logging = options.get("logging", True)  # Turns logging on and off
        self.revert = options.get("revert", 0)  # Determines how many steps should be saved in revert
        self.immutable = options.get("immutable", False)  # Determines default setting for entities immutability.

        # time
        self.time = options.get("time", 0)  # In game counter
        # How much time passes between game_loop iterations. Useful for pausing.
        self.increment = options.get("increment", 1)
        self.cont = options.get("cont", True)  # Flag to determine if game_loop should continue
        # The next state a game_loop will return. Useful for resets and reverts in game_loop
        self.next = options.get("next", None)
        self.value = options.get("value", None)  # Value of the game.

        # maps
        self.map = {}
        self.rmap = []

        for map_options in options.get("map", []):
            self.map[map_options["name"]] = board_creator(map_options.get("type", "square"), map_options)
            if "rmap" in map_options:
                self.rmap.append(map_options["name"])

        self._rmap = _getStatRmap if self.rmap else _getStatInheritance

        # Entities
        self["empty"] = Entity(self, name="empty", immutable=True)
        for entity_options in options.get("entities", []):
            self[entity_options["name"]] = Entity(self, **entity_options)

        for special in options.get("special", []):
            self.getQuote(special)

        # Constants
        self.constants = {}

        # Delay
        self.delay = []
        for manual in options.get("delays", []):
            storage = {k: self[v] for k, v in manual["storage"].items()}
            self.controlDelay(self[manual["callback"]], manual["ticks"], storage)

        # Rand
        self.rand = Random()
        self.seed = options.get("seed")
        if options.get("rand", None):
            self.rand.setstate(options["rand"])
        elif self.seed is not None:
            self.rand.seed(options["seed"])

        # Initial logging
        if self.logging:
            info(f"INITIALIZING {self.name}")

        if init in self:
            self._controlMove(self["empty"], self["empty"], self[init])
            self._checkDelay()
        elif self.logging:
            info("")

        # Set up Revert
        self.state = None
        if self.revert:
            self.state = [self.copy()]

        super().__init__()

    def __bool__(self) -> bool:
        return self.cont

    def __str__(self) -> str:
        return f"<Instance: {self.name} {self.time}>"

    def __repr__(self) -> str:
        return f"<Instance: {self.name} {self.time}>"

    @no_recurse
    def __eq__(self, other) -> bool:
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

    def __ne__(self, other) -> bool:
        return not self == other

    def __copy__(self) -> Self:
        return self.copy()

    def copy(self, new=None) -> Self:
        if new is None:
            new = type(self)(is_copy=True)

        for k, v in self.__dict__.items():
            if k not in {"delay", "map", "state", "next"}:
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
            env = {}
            env.update(delay["env"])
            env["self"] = new
            env["storage"] = {k: new[v.name] for k, v in delay["env"]["storage"].items()}

            new.delay.append({
                "env": env,
                "ticks": delay["ticks"],
                "script": delay["script"],
            })

        # Handle state
        new.state = None
        new.next = None

        return new

    # ---------------------------------------------------
    #               Selector Function                  -
    # ---------------------------------------------------
    @register({"args": ["self", "$1"], "string": ["$1"]}, name="`")
    def getQuote(self, target: str, skip_interpret: bool = True) -> Entity:
        """
        Returns a literal script as a new anonymous entity.

        .. code-block:: xml

            <i>`($caster.NAME not-in $card)</i>
        """
        if target not in self:

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
                        scripts.append(Script("".join(buf), skip_interpret=skip_interpret))
                        buf = []
                        continue

                    buf.append(char)

                scripts.append(Script("".join(buf), skip_interpret=skip_interpret))

            else:
                scripts.append(Script(target, skip_interpret=skip_interpret))

            self[target] = Entity(self, require=scripts, name=target, immutable=True)

        return self[target]

    @register({"args": ["self", "storage", "$1"], "string": ["$1"], "all": True}, name="CONSTANT")
    def controlConst(self, storage: dict, code: str, *args) -> Any:
        key = (code, *args)
        if key not in self.constants:
            code = Script(code, skip_interpret=True)
            self.constants[key] = eval(code.code, Variables.env, {"storage": storage, "self": self})

        return self.constants[key]

    @register(["self", "$1"], name="#")
    def getEntity(self, target: Optional[str | Location | list | Entity]) -> Entity | list[Entity]:
        """
        Fetches the udebs entity object given a selector.

        Udebs selectors can take all the following forms.

        * string - The name of the object we are looking for.
        * tuple - A tuple of the form (x, y, name) or (x, y) representing a location on a map.
        * list - A list containing other selectors.
        * None - Returns the default empty selector.

        .. code-block:: xml

            <i># identifier</i>
        """
        if isinstance(target, str) and target in self:
            return self[target]
        elif isinstance(target, Location):
            return self._getEntityTuple(target.loc)
        elif isinstance(target, tuple):
            return self._getEntityTuple(target)
        elif isinstance(target, list):
            return [self.getEntity(i) for i in target]
        elif target is None:
            return self['empty']
        elif isinstance(target, Entity):
            return target
        raise UndefinedSelectorError(target, "entity")

    def _getEntityTuple(self, target: tuple) -> Entity:
        map_ = self.getMap(target)
        try:
            name = map_[target]
        except IndexError:
            raise UndefinedSelectorError(target, "entity")

        unit = self[name]

        if not unit.loc:
            unit = unit.copy(loc=target)

        return unit

    @register({"args": ["self", "-$1"], "default": {"-$1": "$caster"}}, name="MAP")
    def getMap(self, target: str | tuple | Location | Board | Entity = "map") -> Board:
        """
        Fetches the map object caster currently resides on.

        .. code-block:: xml

            <i>caster [$caster] MAP</i>
        """
        if isinstance(target, (Location, Entity)) and target.loc is not None:
            target = target.loc[-1] if target.loc[-1] in self.map else "map"
            return self.map[target]
        elif isinstance(target, tuple):
            if target[-1] in self.map:
                return self.map[target[-1]]
            return self.map["map"]
        elif isinstance(target, str) and target in self.map:
            return self.map[target]
        elif isinstance(target, Board):
            return target
        else:
            raise UndefinedSelectorError(target, "map")

    # ---------------------------------------------------
    #                 Time Management                  -
    # ---------------------------------------------------

    def _checkDelay(self) -> None:
        """Checks and runs actions waiting in delay."""
        if self.logging:
            info("checking delay")

        new = []
        for delay in self.delay:
            if delay['ticks'] <= 0:
                delay['script'](delay['env'])
            else:
                new.append(delay)

        self.delay = new

        if self.logging:
            info("")

    def controlTime(self, time: Optional[int] = None, script: str = "tick") -> bool:
        """
        Increments internal time by 'time' ticks, runs tick script, and activates any delayed effects.

        .. code-block:: xml

            <i>TIME time</i>
        """
        if time is None:
            time = self.increment

        if time == 0:
            self._checkDelay()

        for i in range(time):
            # Increment time
            self.time += 1
            if self.logging:
                info(f'Env time is now {self.time}')

            # Process tick script
            if script in self:
                if self._controlMove(self["empty"], self["empty"], self[script]):
                    self._checkDelay()

            if self.delay:
                for delay in self.delay:
                    delay['ticks'] -= 1

                if self.logging:
                    info("Processing delayed effects")
                self._checkDelay()

            # Append new version to state.
            if self.state:
                test = self.copy()
                self.state.append(test)
                if len(self.state) > self.revert:
                    self.state = self.state[-self.revert:]
                    assert self.state[-1] is test

        return self.cont

    def getRevert(self, time: int = 0) -> Optional[Self]:
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
                    return None

            new.state = new_states
            new.state.append(new.copy())
            return new

    @register(["self", "$1", "$2", "storage"], name="DELAY")
    def controlDelay(self, callback: Entity, time: str, storage: dict) -> bool:
        """
        Delays an effect a number of ticks.

        Note: A delay of 0 will delay an action until the end of the current action window.
        Note: Notice the back tick.

        .. code-block:: xml

            <i>DELAY `(caster CAST target move) 0</i>
        """
        env = {"self": self, "storage": storage}

        new_delay = {
            "env": env,
            "script": callback,
            "ticks": time
        }

        self.delay.append(new_delay)
        if self.logging:
            info(f"effect added to delay for {time}")
        return True

    # ---------------------------------------------------
    #           Corporate get functions                 -
    # ---------------------------------------------------
    @register(["self", "-$1"], name="NAME")
    def getName(self, targets: FullLocation) -> str | list[str]:

        output = []
        for target in targets:
            if not isinstance(target, Entity):
                target = self.getEntity(target)
            output.append(target.name)

        if len(output) == 1:
            return output[0]
        return output

    @register({"args": ["self", "-$1", "$1", "$2"], "default": {"-$1": "$caster", "$2": True}}, name="STAT")
    @register(["self", "-$1", "group", "False"], name="GROUP")
    def getStat(self, target: FullEntity, stat: str, inherit: bool = True) -> list[str] | int | str:
        """
        General getter for all attributes.

        Note: Attributes will include values inherited from their group.

        .. code-block:: xml

            <i>target [$caster] STAT stat</i>
            <i>target [$caster] GROUP</i>
            <i>target [$caster] NAME</i>
        """
        if isinstance(target, list):
            return [self.getStat(i, stat, inherit) for i in target]
        elif not inherit:
            return getattr(target, stat)
        elif stat in self.stats:
            return sum(self._rmap(self, target, stat))
        elif stat in self.lists:
            return [i for j in self._rmap(self, target, stat) for i in j]
        elif stat in self.strings:
            for i in self._rmap(self, target, stat):
                if i is not None:
                    return i
        else:
            raise UndefinedSelectorError(stat, "stat")

    @register({"args": ["self"], "all": True}, name="ALL")
    def getAll(self, *args: str) -> list[Entity]:
        """Return all objects belonging to a group.
        Can take multiple arguments and return all objects belonging to any group.

         .. code-block:: xml

            <i>ALL group</i>
        """
        groups = set(args)

        found = []
        for unit in self.values():
            for group in unit.group:
                if group in groups:
                    found.append(unit)
                    break

        return found

    #     @register({"args": ["self", "-$2", "-$1", "$1"], "default": {"-$2": "$caster"}}, name="LISTSTAT")
    #     def getListStat(self, target, lst, stat):
    #         """
    #         Returns sum of all object stats in a list.

    #         .. code-block:: xml

    #             <i>target [$caster] lst LISTSTAT stat</i>
    #         """
    #         lst = self.getStat(target, lst)

    #         found = (self.getStat(self.getEntity(element), stat) for element in lst)

    #         if stat in self.stats:
    #             return sum(found)
    #         elif stat in self.lists:
    #             return list(i for j in found for i in j)
    #         elif stat in self.strings:
    #             return next(found)

    @register({"args": ["self", "-$2", "-$1", "$1"], "default": {"-$1": "$caster"}}, name="LISTGROUP")
    @register({"args": ["self", "-$1", "group", "$1"], "default": {"-$1": "$caster"}}, name="CLASS")
    def getListGroup(self, target: Entity, lst: str, group: str) -> str | bool:
        """
        Returns first element in list that is a member of group.

        .. code-block:: xml

            <i>target [$caster] lst LISTGROUP group</i>
            <i>target [$caster] CLASS group</i>
        """
        start = self.getStat(target, lst)
        for item in start:
            if group in self[item].group:
                return item
        return False

    @register({"args": ["self"], "all": True}, name="SEARCH")
    def getSearch(self, *args: str) -> list[Entity]:
        """
        Return objects contained in all given groups.

        .. code-block:: xml

            <i>SEARCH arg1 arg2 ...</i>
        """
        found = self.getAll(args[0], "group")
        for arg in args[1:]:
            new = []
            for i in found:
                if arg in i.group:
                    new.append(i)
            found = new

        return found

    # ---------------------------------------------------
    #                 Call wrappers                    -
    # ---------------------------------------------------
    @register({"args": ["self", "-$1", "$1", "$2"], "default": {"-$1": "$caster"}}, name="CAST")
    @register(["self", "#empty", "#empty", "$1"], name="INIT")
    @register({"args": ["self", "-$1", "#empty", "$1"], "default": {"-$1": "$caster"}}, name="ACTION")
    def _controlMove(self, casters: FullEntity, targets: FullEntity, moves: FullEntity, force: bool = False) -> bool:
        """
        Function to trigger an event. Returns True if an action triggers successfully.

        Note: If a list of entity selectors is received for any argument, all actions in the product will trigger.
        """
        value = False

        env = {"storage": None, "self": self}

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
            env["storage"] = {"caster": caster, "target": target, "move": move}
            test = move(env, force=force)
            if test is None:
                value = True
            elif self.logging:
                info(f"failed because {test}")

        return value

    @register({"args": ["self", "$1", "$2", "storage", "$3"], "default": {"$3": False}}, name="REPEAT")
    def controlRepeat(self, callback: Entity, amount: int, storage: dict, force: bool = False,
                      timeout: int = 100) -> bool:
        """
        Executes a callback n times.
        The final argument is to force retries. If set to True, the system will
        retry failures until exactly the requested attempts succeed. Over 100 consecutive failures
        will trigger an exception.

        .. code-block:: xml

            <i>REPEAT `(callback) 5 False</i>
        """
        env = {"storage": storage, "self": self}
        success = True
        for i in range(amount):
            if callback(env) is not None:
                success = False
                if self.logging:
                    info(f"Repeat failed at {i}th interval")

                if force:
                    for j in range(timeout - 1):
                        if callback(env) is None:
                            break
                    else:
                        raise Exception("Timeout reached in repeat function.")

        return success

    @register({"args": ["self", "$1", "$2", "$3", "storage"]}, name="IF")
    def controlIf(self, cond: bool, statement: Entity, other: Entity, storage: dict) -> None:
        """
        A more advanced if statement. Executes statement only if cond is true, else executes other.

        .. code-block:: xml

            <i>IF (cond) `(statement) `(other)</i>
        """
        env = {"storage": storage, "self": self}

        if cond:
            statement(env)
        else:
            other(env)

    @register({"args": ["self"], "kwargs": {"storage": "storage"}, "all": True}, name="OR")
    def controlOr(self, *args: Entity, storage: dict) -> bool:
        """
        A basic or statement. Executes arguments in order until one of them is true.

        Returns True if any argument is true, False otherwise.

        .. code-block:: xml

            <i>OR `(condition1) `(condition2)</i>
        """
        env = {"storage": storage, "self": self}
        for condition in args:
            if condition(env) is None:
                return True

        return False

    @register({"args": ["self"], "kwargs": {"storage": "storage"}, "all": True}, name="AND")
    def controlAnd(self, *args: Entity, storage: dict) -> bool:
        """
        A basic and statement. Executes arguments until one of them is false.

        Returns True if all statements are true. False otherwise.

        .. code-block:: xml

            <i>AND `(condition1) `(condition2)</i>
        """
        env = {"storage": storage, "self": self}

        for condition in args:
            result = condition(env)
            if result is not None:
                if self.logging:
                    info(f"And failed at: {result}")
                return False

        return True

    # ---------------------------------------------------
    #                 User Entrypoints                  -
    # ---------------------------------------------------
    def testMove(self, caster: str, target: str, move: str) -> bool:
        """
        Simulates an action.
        Returns true if the requirements pass successfully, False otherwise.

        .. code-block:: python

            main_map.testMove(caster, target, move)

        """
        env = {"storage": {
            "caster": self[caster],
            "target": self[target],
            "move": self[move],
        }, "self": self}

        return self[move].test(env) is None

    def castInit(self, moves: str, **kwargs) -> bool:
        """Cast an action without variables.

        .. code-block:: xml

            <i>INIT move</i>
        """
        return self.castMove(self["empty"], self["empty"], moves, **kwargs)

    def castAction(self, caster: str, move: str, **kwargs) -> bool:
        """Cast an action with only a caster.

        .. code-block:: xml

            <i>caster [$caster] ACTION move</i>
        """
        return self.castMove(caster, self["empty"], move, **kwargs)

    @register({"args": ["self", "$caster", "$target", "$move", "$1", "$2"], "default": {"$2": 0}}, name="FUTURE")
    def castFuture(self, caster: str, target: str, move: str, **kwargs) -> Self:
        """Same as castMove except returns a copy of instance if move succeeds.
        Does not change the original instance.

        Clones do not log output or generate reserve states.

        .. code-block:: python

            main_map.castFuture(caster, target, move)
        """
        new = self.copy()
        new.revert = 0
        new.logging = False
        if new.castMove(caster, target, move, **kwargs):
            return new

    def castMove(self, caster: str, target: str, move: str, force: bool = False, time: Optional[int] = None):
        """Cast an action including both a caster and a target.

        .. code-block:: xml

            <i>caster [$caster] CAST target move</i>
        """
        caster = self.getEntity(caster)
        target = self.getEntity(target)
        move = self.getEntity(move)

        value = self._controlMove(caster, target, move, force=force)
        if value:
            self._checkDelay()
            self.controlTime(self.increment if time is None else time)

        return value

    def castLambda(self, string: str) -> bool | str:
        """
        Transforms a state space directly from a user string.

        .. code-block:: python

            main_map.castLambda("caster CAST target move")
        """
        code = self.getQuote(string, skip_interpret=False)
        code({"storage": {}, "self": self})

    def castSingle(self, string: str) -> Any:
        """
        Call a function directly from a user input effect String.
        Returns the value it would return if used in a require.

        .. code-block:: python

            main_map.castSingle("caster CAST target move")
        """
        code = Script(string)
        return eval(code.code, Variables.env, {"storage": {}, "self": self})

    # ---------------------------------------------------
    #               Entity control                     -
    # ---------------------------------------------------
    @register({"args": ["self", "-$2", "-$1", "$1"], "default": {"-$2": "$caster"}}, name="GETS")
    def controlListAdd(self, targets: FullEntity, lst: str, entries: str | list[str]) -> bool:
        """
        Adds an element to a list.

        .. code-block:: xml

            <i>caster [$caster] lst GETS entries</i>
        """
        if isinstance(entries, str):
            entries = [entries]

        changed = False
        for target, entry in product(targets, entries):
            if not target.immutable:
                getattr(target, lst).append(entry)
                changed = True
                if self.logging:
                    info(f"{entry} added to {target} {lst}")

        return changed

    @register({"args": ["self", "-$2", "-$1", "$1"], "default": {"-$2": "$caster"}}, name="LOSES")
    def controlListRemove(self, targets: FullEntity, lst: str, entries: str | list[str]) -> bool:
        """
        Removes an element from a list.

        .. code-block:: xml

            <i>caster [$caster] lst LOSES entries</i>
        """

        if isinstance(entries, str):
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

    @register({"args": ["self", "-$1", "$1"], "default": {"-$1": "$caster"}}, name="CLEAR")
    def controlClear(self, targets: FullEntity, lst: str) -> bool:
        """
        Removes all from a targets list attribute.

        .. code-block:: xml

            <i>target [$caster] CLEAR lst</i>
        """
        changed = False
        for target in targets:
            if not target.immutable:
                getattr(target, lst).clear()
                changed = True
                if self.logging:
                    info(f"{target} {lst} has been cleared")

        return changed

    @register({"args": ["self", "-$1", "$1"], "default": {"-$1": None}}, name="SHUFFLE")
    def controlShuffle(self, targets: Optional[FullEntity], lst: str | list) -> list | bool:
        """
        Randomize order of a list.

        .. code-block:: xml

            <i>target SHUFFLE lst</i>
        """
        if targets is None:
            self.rand.shuffle(lst)
            return lst

        changed = False
        for target in targets:
            if not target.immutable:
                self.rand.shuffle(getattr(target, lst))
                changed = True
                if self.logging:
                    info(f"{target} {lst} has been shuffled")

        return changed

    @register(["self", "-$2", "-$1", "$1"], name="+=")
    @register(["self", "-$2", "-$1", "$1", -1], name="-=")
    @register({"args": ["self", "-$2", "-$1", "$1"], "default": {"-$2": "$caster"}}, name="CHANGE")
    def controlIncrement(self, targets: FullEntity, stat: str, increment: int, multi: int = 1) -> bool:
        """
        Increment a statistic by a static value.

        Note: Final value will be modified as follows (Stat = Stat + (increment * multi))

        .. code-block:: xml

            <i>target stat += increment</i>
            <i>target stat -= increment</i>
            <i>target [$caster] stat CHANGE increment</i>
        """
        changed = False
        total = int(increment * multi)
        for target in targets:
            if not target.immutable:
                setattr(target, stat, getattr(target, stat) + total)
                changed = True
                if self.logging:
                    info(f"{target} {stat} changed by {total} is now {self.getStat(target, stat)}")

        return changed

    @register({"args": ["self", "-$2", "-$1", "$1"], "default": {"-$2": "$caster"}}, name="REPLACE")
    def controlString(self, targets: FullEntity, stat: str, value: Any) -> bool:
        """
        Replace a value with another value.

        Note: This function also works on all attributes.

        .. code-block:: xml

            <i>caster [$caster] stat REPLACE value</i>
        """
        changed = False
        for target in targets:
            if not target.immutable:
                setattr(target, stat, value)
                changed = True
                if self.logging:
                    info(f"{target} {stat} changed to {value}")

        return changed

    @register({"args": ["self", "-$1", "$1"], "default": {"-$1": "$caster", "$1": "#empty"}}, name="RECRUIT")
    def controlRecruit(self, target: Entity, positions: FullLocation) -> Entity:
        """
        Create a new entity by copying another then move it to a position.

        Note: If position is not set, copy will be made but not moved into a location.
        Note: One new entity will be created for each position given.

        .. code-block:: xml

            <i>caster [$caster] RECRUIT position ["#empty"]</i>
        """
        new = target
        for position in positions:
            if not target.immutable:
                target.increment += 1
                name = f"{target.name}{target.increment}"
                new = target.copy(name=name, increment=0)
                self[name] = new
                if self.logging:
                    info(f"{name} has been recruited")
            self.controlTravel(new, position)

        return new

    @register(["self", "-$1"], name="DELETE")
    def controlDelete(self, targets: Entity):
        """
        Permanently remove an object from the game.

        .. code-block:: xml

            <i>target DELETE</i>
        """
        changed = False
        for target in targets:
            if not target.immutable:
                del self[target.name]
                if target.loc:
                    del self.map[target.loc[2]][target.loc]
                if self.logging:
                    info(f"{target} has been deleted")
                changed = True
        return changed

    # ---------------------------------------------------
    #                 Entity loc wrappers              -
    # ---------------------------------------------------
    @register({"args": ["self", "-$1"], "default": {"-$1": "$caster"}}, name="XLOC")
    @register({"args": ["self", "-$1", 1], "default": {"-$1": "$caster"}}, name="YLOC")
    @register({"args": ["self", "-$1", 2], "default": {"-$1": "$caster"}}, name="MAPNAME")
    def getLocData(self, target: Location | Entity, value=0) -> int | str:
        """
        Gets the x, y, or map name coordinate of target, False if target not on a map.

        .. code-block:: xml

            <i>target [$caster] XLOC</i>
            <i>target [$caster] YLOC</i>
            <i>target [$caster] MAPNAME</i>
        """
        loc = target.loc
        return loc[value] if loc else None

    @register(["self", "$1"], name="@")
    def getLocObject(self, target: tuple | Entity) -> Location:
        """
        Gets the location tuple of a target, False if target not on a map.

        .. code-block:: xml

            <i>target [$caster] LOC</i>
        """
        if isinstance(target, Location):
            return target
        elif isinstance(target, Entity):
            return Location(target.loc)
        elif target is None:
            return Location(None)
        elif target[-1] in self.map:
            return Location(target)
        elif "map" in self.map:
            return Location((*target, "map"))
        else:
            raise UndefinedSelectorError({target}, "board_type")

    @register({"args": ["self", "-$1", "$1", "$2", "$3"], "default": {"-$1": "$caster", "$3": "None"}}, name="SHIFT")
    def getShift(self, target: Location, x: int, y: int, name: Optional[str] = None) -> tuple | Entity:
        """
        Returns a new loc shifted x and y units from an old one

        .. code-block:: xml

            <i>target [$caster] SHIFT x y</i>
        """
        loc = target.loc
        if loc is not None:
            new_name = name if name else loc[2]
            new_loc = (loc[0] + x, loc[1] + y, new_name)
            if self.map[new_name].test_loc(new_loc):
                return new_loc

        return self['empty']

    # ---------------------------------------------------
    #              Board control wrappers              -
    # ---------------------------------------------------
    def printMap(self, board: str = "map"):
        """Print a map."""
        self.map[board].show()

    @register({"args": ["self", "-$1", "$1"], "default": {"-$1": "$caster"}}, name="MOVE")
    @register({"args": ["self", "-$1", "$1"], "default": {"-$1": "$caster"}}, name="TRAVEL")
    def controlTravel(self, casters: FullEntity, targets: Optional[FullLocation] = None) -> None:
        """Move one object to a new location.

        .. code-block:: xml

            <i>caster [$caster] MOVE target</i>
        """
        for caster in casters:
            for target in targets:
                # First move caster to the new location.
                if target.loc:
                    target_loc, bumped_unit = self.getMap(target).travel(caster.name, target.loc)
                    if bumped_unit and not self[bumped_unit].immutable:
                        self[bumped_unit].loc = None
                else:
                    target_loc = None

                # Then remove caster from the previous location
                if not caster.immutable:
                    if caster.loc:
                        del self.getMap(caster)[caster.loc]
                    caster.loc = target_loc

                if self.logging:
                    info(f"{caster} has moved to {target}")

    # ---------------------------------------------------
    #                 Game Loop Helpers                -
    # ---------------------------------------------------

    def gameLoop(self, time: int = 1, script: str = "tick") -> None:
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
                if current is not current.next:
                    current.state = None

                current.next.increment = current.increment
                current = current.next
                current.next = None
                continue

            current.controlTime(current.increment, script=script)

        if current.logging:
            info(f"EXITING {current.name}\n")

    @register({"args": ["self", "$1"], "default": {"$1": 1}}, name="EXIT")
    def exit(self, value: int = 1) -> None:
        """Requests the end of the game by setting Instance.cont to False, and exiting out of the game_loop.

        .. code-block:: xml

            <i>EXIT</i>
        """
        if self.logging:
            info(f"Exit requested with value of: {value}")
        self.cont = False
        self.value = value

    def resetState(self, script: str = "reset") -> Self:
        """Resets the game metadata to default.

        .. code-block:: python

            main_map.resetState()
        """
        self.cont = True
        self.value = None
        self.time = 0
        self.delay.clear()

        if self.seed is not None:
            self.rand.seed(self.seed)

        if self.logging:
            info(f"Env time is now {self.time}")

        if script in self:
            if self._controlMove(self["empty"], self["empty"], self[script]):
                self._checkDelay()

        elif self.logging:
            info("")

        if self.revert:
            self.state = [self.copy()]

        return self
