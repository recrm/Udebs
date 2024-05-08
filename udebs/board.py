from collections.abc import MutableMapping
from typing import Iterator
import math

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


class Board(MutableMapping):
    """This is a test."""

    def __init__(self, **options):
        if "_data" in options:
            # second path for copy operation only
            self.__dict__ = options["_data"]
            return

        self.name = options.get("name", "map")
        self.empty = options.get("empty", "empty")
        self.type = options.get("type", False)
        self.count = 4
        if self.type:
            self.count += 2
            if self.type == "diag":
                self.count += 2

        # Set up maps.
        dim = options.get("dim", (1, 1))
        if isinstance(dim, tuple):
            self.map = []
            for e in range(dim[0]):
                self.map.append([self.empty for _ in range(dim[1])])

        elif isinstance(dim, list):
            self.map = dim

        self.x = len(self.map)
        self.y = max([len(x) for x in self.map])

    def __eq__(self, other) -> bool:
        if not isinstance(other, Board):
            return False

        if self.map == other.map:
            if self.name == other.name:
                if self.empty == other.empty:
                    return True
        return False

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

    def __repr__(self) -> str:
        return "<board: " + self.name + ">"

    def __copy__(self) -> "Board":
        return self.copy()

    def copy(self) -> "Board":
        options = {}
        for k, v in self.__dict__.items():
            if k == "map":
                v = [i[:] for i in self.map]
            options[k] = v

        return Board(_data=options)

    # ---------------------------------------------------
    #                    Methods                       -
    # ---------------------------------------------------
    def show(self) -> None:
        """Pretty prints a map."""
        maxi = 0
        for name in self.values():
            if name != self.empty and len(str(name)) > maxi:
                maxi = len(str(name))

        for y in range(self.y):
            if self.type == "hex":
                print(" " * y * maxi, end="")

            for x in range(self.x):
                value = self[x, y]
                if value == self.empty:
                    value = "_"

                print(str(value).ljust(maxi), end=" ")

            print()

    def get_distance(self, one: tuple, two: tuple, method: str, **kwargs) -> float:
        """Returns distance between two locations.

        one - starting loc
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
        sort - a function that can be used to sort the order nodes are explored.
        pointer - optional dictionary for tracking pathing
        state - the state if callback is to be used
        callback - callback to filter cells

        """
        if not isinstance(start, set):
            new = {start}
        else:
            new = start

        start = state.getEntity(start)
        searched = set()
        searched.update(new)

        while len(new) > 0:
            yield new

            next_ = set()
            for child in new:
                for x_, y_ in sides[:self.count]:
                    loc = (child[0] + x_, child[1] + y_, self.name)
                    if loc not in searched:
                        searched.add(loc)
                        if self.test_loc(loc):
                            if callback:
                                env = {"storage": {
                                    "caster": start,
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

        Returns empty list if there is no path.

        """
        if not isinstance(finish, set):
            finish = {finish}

        pointer = {i: None for i in start}

        # Populate pointer.
        for i in self.get_adjacent(start, pointer=pointer, **kwargs):
            final = finish.intersection(i)
            if len(final) > 0:
                break
        else:
            return []

        new = final.pop()
        found = [new]
        while pointer[new]:
            new = pointer[new]
            found.append(new)

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

    def test_loc(self, loc: tuple) -> bool:
        """
        Test a loc to see if it is valid.

        loc - Starting loc

        """
        if loc:
            try:
                map_ = loc[2]
            except IndexError:
                map_ = "map"

            if self.name == map_:
                if 0 <= loc[0] < self.x:
                    if 0 <= loc[1] < self.y:
                        return True

        return False

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
