import random
import collections

class Board(collections.MutableMapping):
    def __init__(self, options={}):
        self.name = options.get("name", "map")
        self.empty = options.get("empty", "empty")
        self.type = options.get("type", False)

        #Set up maps.
        dim = options.get("dim", (1,1))
        if isinstance(dim, tuple):
            self._map = []
            for e in range(dim[0]):
                self._map.append([self.empty for i in range(dim[1])])

        elif isinstance(dim, list):
            self._map = dim

    def __eq__(self, other):
        if not isinstance(other, Board):
            return False

        values = [
            self._map == other._map,
            self.name == other.name,
            self.empty == other.empty,
        ]
        return all(values)

    def __getitem__(self, key):
        if not self.testLoc(key):
            raise IndexError
        return self._map[key[0]][key[1]]

    def __setitem__(self, key, value):
        if not self.testLoc(key):
            raise IndexError
        self._map[key[0]][key[1]] = value

    def __delitem__(self, key):
        if not self.testLoc(key):
            raise IndexError
        self._map[key[0]][key[1]] = self.empty

    def __len__(self):
        return self.x * self.y

    def __iter__(self):
        for x in range(self.x):
            for y in range(self.y):
                yield (x, y, self.name)

    def __repr__(self):
        return "<board: "+self.name+">"

    @property
    def x(self):
        return len(self._map)

    @property
    def y(self):
        if not hasattr(self, "_y"):
            try:
                self._y = max([len(x) for x in self._map])
            except ValueError:
                self._y = 0
        return self._y

    #---------------------------------------------------
    #                    Methods                       -
    #---------------------------------------------------
    def getLoc(self, string):
        """Return loc of first instance of string in map.

        string - Name to search force

        """
        for loc in self:
            if self[loc] == string:
                return (loc[0], loc[1], self.name)
        return False

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
        if not self.testLoc(one) or not self.testLoc(two):
            return float("inf")
        elif method == 'y':
            return int( abs( one[1] - two[1] ) )
        elif method == 'x':
            return int( abs( one[0] - two[0] ) )
        elif method == 'z':
            return abs(two[0] + two[1]) - (one[0] + one[1])
        elif method == 'hex':
            return (abs(one[0] - two[0]) + abs(one[1] - two[1]) + abs((two[0] + two[1]) - (one[0] + one[1])))/2
        elif method == "p1":
            return int(abs(one[0] - two[0]) + abs(one[1] - two[1]))
        elif method == "p2":
            return int(math.sqrt(math.pow(one[0] - two[0], 2) + math.pow(one[1] - two[1], 2)))
        elif method == "pinf":
            return max(abs(one[0] - two[0]), abs(one[1] - two[1]))
        else:
            raise UndefinedMetricError(method)

    def getAdjacent(self, center, callback=False, pointer=None):
        """
        Iterates over concentric circles of adjacent tiles.

        center - starting local
        callback - Callback used to determine what is a valid tile.
        pointer - Optional dict to store pathing data.

        """
        if not self.testLoc(center):
            yield list()
            return

        new = {center}
        searched = {center}
        next = self.adjacent(center, pointer)

        next.difference_update(searched)

        while len(new) > 0:
            #Sorted is needed to force program to be deterministic.
            yield sorted(list(new))
            new = set()
            for node in next:
                if self.testLoc(node):
                    if callback and callback.testRequire(center, node) == True:
                        new.add(node)

            searched.update(next)
            next = set().union(*[self.adjacent(node, pointer) for node in new])
            next.difference_update(searched)

    def getPath(self, start, finish, callback=False):
        """
        Algorithm to find a path between start and finish assuming move.

        start, finish - Start and finish locations.
        move - Callback used to determine what is a valid tile.

        Returns empty list if there is no path.

        """
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

    def getFill(self, center, callback=False, distance=float("inf")):
        """
        Returns a list of map spaces that center fills into.

        center - Starting loc
        callback - Callback used to determine what is a valid tile.
        distance - Maximum fill distance from target.

        """
        found = []
        count = 0
        #first iteration is always the center itself.
        for i in self.getAdjacent(center, callback):
            found.extend(i)
            if count >= distance:
                break
            count +=1

        random.shuffle(found)
        return found

    def testLoc(self, loc):
        """
        Test a loc to see if it is valid.

        loc - Starting loc

        """
        if loc:
            x = loc[0]
            y = loc[1]
            try:
                map_ = loc[2]
            except IndexError:
                map_ = "map"

            if self.name == map_:
                if 0 <= x < self.x:
                    if 0 <= y < self.y:
                        return True
        return False

    def testBlock(self, start, finish, callback):
        """
        Tests to see if there exists a path from start to finish.

        start, finish - Starting and finishing locations.
        callback - Callback used to determine what is a valid tile.

        """
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

    def controlMove(self, name, loc):
        if not self.testLoc(loc):
            return False
        self[loc] = name
        return True

    def controlBump(self, loc):
        if not self.testLoc(loc):
            return False
        del self[loc]
        return True

class UndefinedMetricError(Exception):
    def __init__(self, metric):
        self.metric = metric
    def __str__(self):
        return repr(self.metric)+" is not a valid distance metric."
