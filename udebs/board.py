from collections.abc import MutableMapping
import math

class Board(MutableMapping):
    def __init__(self, field, **options):
        self.field = field
        self.name = options.get("name", "map")
        self.empty = options.get("empty", "empty")
        self.type = options.get("type", False)

        #Set up maps.
        dim = options.get("dim", (1,1))
        if isinstance(dim, tuple):
            self.map = []
            for e in range(dim[0]):
                self.map.append([self.empty for i in range(dim[1])])

        elif isinstance(dim, list):
            self.map = dim

    def __eq__(self, other):
        if not isinstance(other, Board):
            return False

        values = [
            self.map == other.map,
            self.name == other.name,
            self.empty == other.empty,
        ]
        return all(values)

    def __getitem__(self, key):
        if key[0] >= 0:
            if key[1] >= 0:
                 return self.map[key[0]][key[1]]
        raise IndexError

    def __setitem__(self, key, value):
        if key[0] >= 0:
            if key[1] >= 0:
                self.map[key[0]][key[1]] = value
                return
        raise IndexError

    def __delitem__(self, key):
        if key[0] >= 0:
            if key[1] >= 0:
                self.map[key[0]][key[1]] = self.empty
                return
        raise IndexError

    def __len__(self):
        return self.x * self.y

    def __iter__(self):
        for x in range(self.x):
            for y in range(self.y):
                yield (x, y, self.name)

    def __repr__(self):
        return "<board: "+self.name+">"

    def copy(self, field):
        options = {
            "name": self.name,
            "empty": self.empty,
            "type": self.type,
            "dim": [i[:] for i in self.map]
        }

        return Board(field, **options)

    @property
    def x(self):
        return len(self.map)

    @property
    def y(self):
        if not hasattr(self, "_y"):
            self._y = max([len(x) for x in self.map])
        return self._y

    #---------------------------------------------------
    #                    Methods                       -
    #---------------------------------------------------
    def show(self):
        for x in range(self.y):
            for y in range(self.x):
                value = self[y,x]
                if value == self.empty:
                    value = "_"

                print(value, end=" ")

            print()

    def getDistance(self, one, two, method):
        """Returns distance between two locations.

        one - starting loc
        two - end loc
        method - metric or callback to use

        """
        if not isinstance(method, str):
            count = 0
            for i in self.getAdjacent(one, method):
                if two in i:
                    return count
                count +=1
            return float("inf")

        #Note: Dictonary switch method doubles this functions run time.
        elif not self.testLoc(one) or not self.testLoc(two):
            return float("inf")
        elif method == 'y':
            return int(abs(one[1] - two[1]))
        elif method == 'x':
            return int(abs(one[0] - two[0]))
        elif method == 'z':
            return int(abs(two[0] + two[1]) - (one[0] + one[1]))
        elif method == 'hex':
            return int((abs(one[0] - two[0]) + abs(one[1] - two[1]) + abs((two[0] + two[1]) - (one[0] + one[1])))/2)
        elif method == "p1":
            return int(abs(one[0] - two[0]) + abs(one[1] - two[1]))
        elif method == "p2":
            return int(math.sqrt(math.pow(one[0] - two[0], 2) + math.pow(one[1] - two[1], 2)))
        elif method == "pinf":
            return int(max(abs(one[0] - two[0]), abs(one[1] - two[1])))
        else:
            raise UndefinedMetricError(method)

    def getAdjacent(self, center, callback, pointer=None, include_center=True):
        """
        Iterates over concentric circles of adjacent tiles.

        center - starting local
        callback - Callback used to determine what is a valid tile.
        pointer - Optional dict to store pathing data.

        """
        if not self.testLoc(center):
            yield []
            return

        if include_center:
            yield [center]
        else:
            yield []

        searched = {center}
        next_search = self.adjacent(center, pointer)
        next_search.difference_update(searched)

        while True:
            new = set()
            for node in next_search:
                if self.testLoc(node):
                    env = self.field.getEnv(center, node, callback)
                    if callback.testRequire(env) == True:
                        new.add(node)

            searched.update(next_search)
            next_search = set().union(*[self.adjacent(node, pointer) for node in new])
            next_search.difference_update(searched)

            if len(new) > 0:
                # sorted is required to force algorithm to be deterministic
                yield sorted(list(new))
            else:
                break

    def getPath(self, start, finish, callback):
        """
        Algorithm to find a path between start and finish assuming callback.

        start, finish - Start and finish locations.
        callback - Callback used to determine what is a valid tile.

        Returns empty list if there is no path.

        """
        if not self.testLoc(start) or not self.testLoc(finish):
            return []

        pointer = {}

        if start == finish:
            return [start]

        #Populate pointer.
        for i in self.getAdjacent(start, callback, pointer):
            if finish in i:
                break
        else:
            return []

        found = [finish]
        while True:
            new = pointer[found[-1]]
            found.append(new)
            if new == start:
                found.reverse()
                return found

    def getFill(self, center, callback, distance=float("inf"), rand=None, include_center=True):
        """
        Returns a list of map spaces that center fills into.

        center - Starting loc
        callback - Callback used to determine what is a valid tile.
        distance - Maximum fill distance from target.
        rand - Instance of random.Random() to use for data shuffle.

        """
        if not self.testLoc(center):
            return []

        found = []
        count = 0
        #first iteration is always the center itself.
        for i in self.getAdjacent(center, callback, include_center=include_center):
            found.extend(i)
            if count >= distance:
                break
            count +=1

        if rand:
            rand.shuffle(found)
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

    def testBlock(self, start, finish, callback):
        """
        Tests to see if there exists a path from start to finish.

        start, finish - Starting and finishing locations.
        callback - Callback used to determine what is a valid tile.

        """
        if self.testLoc(start) and self.testLoc(finish):
            for i in self.getAdjacent(start, callback):
                for q in i:
                    if finish in self.adjacent(q):
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

        if self.type:
            found.add((x -1, y +1, map_))
            found.add((x +1, y -1, map_))

        if self.type == "diag":
            found.add((x +1, y +1, map_))
            found.add((x -1, y -1, map_))

        if isinstance(pointer, dict):
            for item in found:
                if item not in pointer:
                    pointer[item] = location

        return found

class UndefinedMetricError(Exception):
    def __init__(self, metric):
        self.metric = metric
    def __str__(self):
        return repr(self.metric)+" is not a valid distance metric."
