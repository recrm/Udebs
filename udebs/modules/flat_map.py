import math
from abc import ABC, abstractmethod
from typing import Self, Iterator, Optional
from numbers import Number

from udebs.board import Board, Location
from udebs.interpret import register
from udebs.entity import Entity


class BoardMapRoot(Board, ABC):
    def __init__(self, name, empty, **kwargs):
        super().__init__(name, empty, **kwargs)
        self.x = len(self.map)
        self.y = max([len(x) for x in self.map])
        self.empty = empty

    @property
    @abstractmethod
    def sides(self):
        raise NotImplementedError

    def travel(self, obj, location):
        existing_name = self[location]
        self[location] = obj

        cannon_loc = (location[0], location[1], self.name)
        if existing_name != self.empty:
            return cannon_loc, existing_name

        return cannon_loc, None

    def populate_map(self, empty, dim):
        # Set up maps.
        map_ = []
        for e in range(dim[0]):
            map_.append([empty for _ in range(dim[1])])
        return map_

    def __getitem__(self, key: tuple) -> str:
        x, y = key[0], key[1]
        if x >= 0:
            if y >= 0:
                return self.map[x][y]
        raise IndexError

    def __setitem__(self, key: tuple, value: str) -> None:
        x, y = key[0], key[1]
        if x >= 0:
            if y >= 0:
                self.map[x][y] = value
                return
        raise IndexError

    def __delitem__(self, key: tuple) -> None:
        x, y = key[0], key[1]
        if x >= 0:
            if y >= 0:
                self.map[x][y] = self.empty
                return
        raise IndexError

    def __len__(self) -> int:
        return self.x * self.y

    def __iter__(self):
        for x in range(self.x):
            for y in range(self.y):
                yield x, y, self.name

    def copy(self) -> Self:
        dim = [i[:] for i in self.map]
        return type(self)(self.name, empty=self.empty, overwrite_map=dim)

    def show(self) -> None:
        """Pretty prints a map."""
        maxi = 0
        for name in self.values():
            if name != self.empty and len(str(name)) > maxi:
                maxi = len(str(name))

        for y in range(self.y):
            if type(self) is HexMap:
                print(" " * y * maxi, end="")

            for x in range(self.x):
                value = self[x, y]
                if value == self.empty:
                    value = "_"

                print(str(value).ljust(maxi), end=" ")

            print()

    # ---------------------------------------------------
    #                    Methods                       -
    # ---------------------------------------------------
    def get_distance(self, one: tuple, two: tuple, method: str, **kwargs) -> float:
        """Returns distance between two locations.

        one - starting location
        two - end loc
        method - metric or callback to use

        """
        if not isinstance(method, str):
            count = 0
            for i in self.get_adjacent(one, callback=method, **kwargs):
                if two in i:
                    return count
                count += 1
            return float("inf")
        elif method == 'y':
            return int(abs(one[1] - two[1]))
        elif method == 'x':
            return int(abs(one[0] - two[0]))
        elif method == 'z':
            return int(abs(two[0] + two[1]) - (one[0] + one[1]))
        elif method == 'hex':
            return int((abs(one[0] - two[0]) + abs(one[1] - two[1]) + abs((two[0] + two[1]) - (one[0] + one[1]))) / 2)
        elif method == "p1":
            return int(abs(one[0] - two[0]) + abs(one[1] - two[1]))
        elif method == "p2":
            return int(math.sqrt(math.pow(one[0] - two[0], 2) + math.pow(one[1] - two[1], 2)))
        elif method == "pinf":
            return int(max(abs(one[0] - two[0]), abs(one[1] - two[1])))
        else:
            raise ValueError(f"{method} is an invalid metric")

    def get_adjacent(self, start: tuple | set[tuple], sort=None, pointer=None, state=None,
                     callback=None) -> Iterator[set[tuple]]:
        """
        Iterates over concentric circles of adjacent tiles.

        new - starting local
        sort - a function that can be used to sort the order nodes will be explored.
        pointer - optional dictionary for tracking pathing
        state - the state if callback is to be used
        callback - callback to filter cells

        """
        caster = None
        if not isinstance(start, set):
            new = {start}
        else:
            new = start
            start = list(start)

        searched = set()
        searched.update(new)

        while len(new) > 0:
            yield new

            next_ = set()
            for child in new:
                for x_, y_ in self.sides:
                    loc = (child[0] + x_, child[1] + y_, self.name)
                    if loc not in searched:
                        searched.add(loc)
                        if self.test_loc(loc):
                            if callback:
                                if state is None:
                                    raise Exception("state must be set in get_adjacent if callback is set")

                                if caster is None:
                                    caster = state.getEntity(start)

                                env = {"storage": {
                                    "caster": caster,
                                    "target": state.getEntity(loc),
                                    "move": callback
                                }, "self": state}
                                if callback.test(env) is not None:
                                    continue
                            next_.add(loc)
                            if pointer:
                                pointer[loc] = child
            new = next_
            if sort:
                new = sort(new)

    def get_path(self, start: tuple, finish: tuple, **kwargs) -> list[tuple]:
        """
        Algorithm to find a path between start and finish assuming callback.

        start, finish - Start and finish locations.

        Returns an empty list if there is no path.

        """
        if not isinstance(finish, set):
            finish = {finish}

        if not isinstance(start, set):
            start = {start}

        pointer = {i: None for i in start}

        print(start)

        # Populate pointer.
        for i in self.get_adjacent(start, pointer=pointer, **kwargs):
            print(i, "iteration")

            final = finish.intersection(i)
            if len(final) > 0:
                break
        else:
            return []

        new = final.pop()
        found = [new]
        print(found, "found")
        while pointer[new]:
            new = pointer[new]
            found.append(new)
            print(found, "found")

        found.reverse()
        return found

    def get_fill(self, center: tuple, distance: float = float("inf"),
                 include_center: bool = True, **kwargs) -> set[tuple]:
        """
        Returns a list of map spaces that center fills into.

        center - Starting loc
        distance - Maximum fill distance from target.
        include_center - Boolean to determine if center should be included.

        """
        found = set()
        count = 0
        for i in self.get_adjacent(center, **kwargs):
            found.update(i)
            if count >= distance:
                break
            count += 1

        if not include_center:
            found.remove(center)

        return found

    def test_block(self, start: tuple, finish: tuple, max_dist: float = float("inf"), **kwargs) -> bool:
        """
        Tests to see if there exists a path from start to finish.

        start, finish - Starting and finishing locations.

        """
        if start == finish and max_dist > 0:
            return True

        i = self.get_adjacent(finish)
        next(i)
        final = next(i)
        for dist, i in enumerate(self.get_adjacent(start, **kwargs)):
            if i.intersection(final):
                return True

            if dist + 1 >= max_dist:
                return False

        return False


class SquareMap(BoardMapRoot):
    type = "square"
    sides = [
        (-1, 0),
        (0, 1),
        (1, 0),
        (0, -1),
    ]


class HexMap(BoardMapRoot):
    type = "hex"
    sides = [
        (-1, 0),
        (0, 1),
        (1, 0),
        (0, -1),
        (-1, 1),
        (1, -1),
    ]


class DiagMap(BoardMapRoot):
    type = "diag"
    sides = [
        (-1, 0),
        (0, 1),
        (1, 0),
        (0, -1),
        (-1, 1),
        (1, -1),
        (1, 1),
        (-1, -1),
    ]


@register({"args": ["self", "$2", "$3", "$1"], "default": {"$2": "$caster", "$3": "$target"}}, name="PATH")
def get_path(state, caster: Location | Entity, target: Location | Entity, callback: Entity) -> list[Location]:
    """
    Finds a path between caster and target using callback as filter for valid space.

    .. code-block:: xml

        <i>PATH callback caster [$caster] target [$target]</i>
    """

    print(caster, target)

    if caster.loc:
        map_ = state.getMap(caster)
        print(map_)
        map_.show()

        if map_.test_loc(target.loc):
            path = map_.get_path(caster.loc, target.loc, callback=callback, state=state)
            return [Location(i) for i in path]

    return []


@register({"args": ["self", "$2", "$3", "$1"], "default": {"$2": "$caster", "$3": "$target"}}, name="DISTANCE")
def get_distance(state, caster: Location | Entity, target: Location | Entity, method: str) -> Number:
    """
    Returns distance between caster and target using method as a metric.

    .. code-block:: xml

        <i>PATH method caster [$caster] target [$target]</i>
    """
    if caster.loc:
        map_ = state.getMap(caster)
        if map_.test_loc(target.loc):
            return map_.get_distance(caster.loc, target.loc, method, state=state)

    return float("inf")


@register({"args": ["self", "$2", "$3", "$1"], "default": {"$2": "$caster", "$3": "$target", "-$1": None},
           "kwargs": {"max_dist": "-$1"}}, name="BLOCK")
def test_block(state, caster: Location | Entity, target: Location | Entity, callback: Entity,
               max_dist: Optional[int] = None) -> bool:
    """
    Test to see if a path exists between caster and target using callback as filter for valid space.

    .. code-block:: xml

        <i>BLOCK callback caster [$caster] target [$target]</i>
    """
    if max_dist is None:
        max_dist = float("inf")

    if caster.loc:
        map_ = state.getMap(caster)
        if map_.test_loc(target.loc):
            return map_.test_block(caster.loc, target.loc, callback=callback, state=state, max_dist=max_dist)

    return False


@register({"args": ["self", "$1", "$2", "$3", "$4"], "default": {"$2": "#empty", "$3": True, "$4": None}},
          name="FILL")
def get_fill(state, center: Location | Entity, callback: Optional[Entity] = None, include_center: bool = True,
             distance: Optional[Number] = None) -> list[Location]:
    """
    Gets all squares in a pattern starting at the center, using callback as filter for valid space.

    .. code-block:: xml

        <i>FILL center callback include_center [true] distance [null]</i>
    """
    if distance is None:
        distance = float("inf")

    if center.loc:
        map_ = state.getMap(center)
        fill = sorted(map_.get_fill(center.loc, distance, include_center, callback=callback, state=state))
        return [Location(i) for i in fill]

    return []
