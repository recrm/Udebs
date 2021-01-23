from collections.abc import MutableMapping
import math
import copy

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

    def __eq__(self, other):
        if not isinstance(other, Board):
            return False

        if self.map == other.map:
            if self.name == other.name:
                if self.empty == other.empty:
                    return True
        return False

    def __getitem__(self, key):
        x, y = key[0], key[1]
        if x >= 0:
            if y >= 0:
                return self.map[x][y]
        raise IndexError

    def __setitem__(self, key, value):
        x, y = key[0], key[1]
        if x >= 0:
            if y >= 0:
                self.map[x][y] = value
                return
        raise IndexError

    def __delitem__(self, key):
        x, y = key[0], key[1]
        if x >= 0:
            if y >= 0:
                self.map[x][y] = self.empty
                return
        raise IndexError

    def __len__(self):
        return self.x * self.y

    def __iter__(self):
        for x in range(self.x):
            for y in range(self.y):
                yield x, y, self.name

    def __repr__(self):
        return "<board: " + self.name + ">"

    def __copy__(self):
        return self.copy()

    def copy(self):
        options = {}
        for k, v in self.__dict__.items():
            if k == "map":
                v = [i[:] for i in self.map]
            options[k] = v

        return Board(_data=options)

    # ---------------------------------------------------
    #                    Methods                       -
    # ---------------------------------------------------
    def show(self):
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

    def getDistance(self, one, two, method, **kwargs):
        """Returns distance between two locations.

        one - starting loc
        two - end loc
        method - metric or callback to use

        """
        if not isinstance(method, str):
            count = 0
            for i in self.getAdjacent(one, callback=method, **kwargs):
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

    def getAdjacent(self, start, sort=None, pointer=None, state=None, callback=None):
        """
        Iterates over concentric circles of adjacent tiles.

        new - starting local
        sort - a function that can be used to sort the order nodes are explored.
        pointer - optional dictionary for tracking pathing
        state - the state if callback is to be used
        callback - callback to filter cells

        """
        if isinstance(start, set):
            new = start
            start = next(iter(start))
        else:
            new = {start}

        searched = copy.copy(new)

        while len(new) > 0:
            yield new

            next_ = set()
            for child in new:
                for x_, y_ in sides[:self.count]:
                    loc = (child[0] + x_, child[1] + y_, self.name)
                    if loc not in searched:
                        searched.add(loc)
                        if self.testLoc(loc):
                            if callback:
                                env = state.getEnv(start, loc, callback)
                                if not callback.testRequire(env) is True:
                                    continue
                            next_.add(loc)
                            if pointer:
                                pointer[loc] = child
            new = next_
            if sort:
                new = sort(new)

    def getPath(self, start, finish, **kwargs):
        """
        Algorithm to find a path between start and finish assuming callback.

        start, finish - Start and finish locations.

        Returns empty list if there is no path.

        """
        if not isinstance(start, set):
            start = {start}

        if not isinstance(finish, set):
            finish = {finish}

        pointer = {i: None for i in start}

        # Populate pointer.
        for i in self.getAdjacent(start, pointer=pointer, **kwargs):
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

    def getFill(self, center, distance=float("inf"), include_center=True, **kwargs):
        """
        Returns a list of map spaces that center fills into.

        center - Starting loc
        distance - Maximum fill distance from target.
        include_center - Boolean to determine if center should be included.

        """
        if not isinstance(center, set):
            center = {center}

        found = set()
        count = 0
        for i in self.getAdjacent(center, **kwargs):
            found.update(i)
            if count >= distance:
                break
            count += 1

        if not include_center:
            found -= center

        return found

    def testLoc(self, loc):
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

    def testBlock(self, start, finish, max_dist=None, **kwargs):
        """
        Tests to see if there exists a path from start to finish.

        start, finish - Starting and finishing locations.

        """
        if max_dist is None:
            max_dist = float("inf")

        if start == finish and max_dist > 0:
            return True

        i = self.getAdjacent(finish)
        next(i)
        final = next(i)
        for dist, i in enumerate(self.getAdjacent(start, **kwargs)):
            if i.intersection(final):
                return True

            if dist + 1 >= max_dist:
                return False

        return False
