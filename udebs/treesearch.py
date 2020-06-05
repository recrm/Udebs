import functools
import math
import time
from .instance import Instance
from collections import OrderedDict

def modifystate(state, entities={}, logging=True, revert=True):
    """Experimental: Creates a copy of an Instance object with modifications designed for improved treesearch."""
    clone = state.copy()
    if logging:
        clone.logging=True

    if revert:
        clone.revert = 0
        clone.state = False

    if entities is not None:
        for key, value in entities.items():
            new = state[key].copy()

            if "group" in value:
                new.group = value["group"]

            if "immutable" in value:
                new.immutable = value["immutable"]

            clone[key] = new

    return clone

def countrecursion(f):
    """Function decorator, prints how many times a function calls itself."""
    time = 0
    @functools.wraps(f)
    def countrecursion_wrapper(*args, **kwargs):
        nonlocal time
        p = (time == 0)
        time +=1
        r = f(*args, **kwargs)
        if p:
            print("nodes visited:", time)
            time = 0
        return r
    return countrecursion_wrapper

def cache(f=None, maxsize=None, storage=None):
    """Function decorator, lru_cache handling Instance objects as str(Instance)."""
    if maxsize is None:
        maxsize = float("inf")

    if storage is None:
        storage = OrderedDict()

    def cache(f):
        @functools.wraps(f)
        def cache_wrapper(self, *args, **kwargs):
            key = (self.hash(), *args)
            value = storage.get(key, None)
            if value is None:
                value = f(self, *args, **kwargs)
                storage[key] = value
            else:
                storage.move_to_end(key)

            while (storage.__len__() > maxsize):
                storage.popitem(False)

            return value

        return cache_wrapper

    if f is None:
        return cache
    return cache(f)

@functools.total_ordering
class Result:
    """Experimental: Object for handling gt and lt relationships when counting turns to victory."""
    def __init__(self, value, turns):
        self.value = value
        self.turns = turns

    def __eq__(self, other):
        return (self.value, self.turns) == (other.value, other.turns)

    def __lt__(self, other):
        if self.value != other.value:
            return self.value < other.value
        elif self.value < 0:
            return self.turns < other.turns
        return self.turns > other.turns

    def __repr__(self):
        return str((self.value, self.turns))

    def __int__(self):
        return self.value

class State(Instance):
    """Base class for all tree search algorithms."""
    def substates(self, override=None):
        """Iterate over substates to a state.

        yields a tuple, (child instance, action tuple)
        if the legalMoves iterator yielded something other than a tuple. This method will yield just that object for both values.
        """
        stateNew = None
        moves = override
        if moves is None:
            moves = self.legalMoves()

        for move in moves:
            if isinstance(move, tuple):
                if stateNew is None:
                    stateNew = self.copy()

                if stateNew.castMove(*move[:3]):
                    stateNew.controlTime(self.increment)
                    yield stateNew, move
                    stateNew = None
            else:
                yield move, move

    def hash(self):
        """Implement this function if you plan on using treesearch.cache"""
        raise NotImplementedError

    def __str__(self):
        raise NotImplementedError

    def legalMoves(self):
        """This function must be implemented. Iterate over all (caster, target, move) tuples that are valid children of current node."""
        raise NotImplementedError

    def endState(self):
        """Example implementations use this function to fetch a states leaf value."""
        return self.value

#---------------------------------------------------
#             Various Tree Search Aglorithms       -
#---------------------------------------------------
class BruteForce(State):
    """Example implementation of a brute force minimax solver."""
    @cache
    def result(self):
        value = self.endState()
        if value is not None:
            return -abs(value)

        results = []
        for child, e in self.substates():
            if child is not e:
                child = child.result()

            results.append(-child)

        return max(results)

class AlphaBeta(State):
    """Example implementation of an alphabeta minimax solver."""
    @cache
    def result(self, alpha=-float("inf"), beta=float("inf")):
        value = self.endState()
        if value is not None:
            return -abs(value)

        for child, e in self.substates():
            if child is not e:
                child = child.result(-beta, -alpha)

            result = -child

            if result > alpha:
                alpha = result

            if alpha >= beta:
                break

        return alpha

class MarkovChain(State):
    """Example implementation of a markov chain calculator."""
    @cache
    def result(self):
        value = self.endState()
        if value is not None:
            return value

        total = 0
        for child, p in self.substates():
            total += child.result() * p[3]

        return total

#---------------------------------------------------
#                   Monty Carlo                    -
#---------------------------------------------------
class MontyCarlo(State):
    """Experimental: Example implementation of a Monty Carlo treesearch algorithm."""
    def init(self, entry=None):
        self.children = None
        self.v = 0
        self.n = 0
        self.entry = entry
        return self

    def result(self, maximizer=True, **kwargs):
        if self.children is None:
            value, *args = self.simulate(maximizer, **kwargs)
            self.children = [c.init(e, *args) for c, e in self.substates()]

        else:
            # selection
            node = max(self.children, key=self.weight)
            value = node.result(not maximizer, **kwargs)
            value = 1 - value

        self.v += value
        self.n += 1
        return self.v / self.n

    def weight(self, child, c=1):
        if child.n == 0:
            return float("inf")

        q = 1 - (child.v / child.n)
        un = math.sqrt(math.log(self.n) / child.n)
        return q + (c * un)

    def think(self, think_time, verbose=True, **kwargs):
        t_end = time.time() + think_time
        iters = 0
        while time.time() < t_end:
            self.result(**kwargs)
            iters +=1

        if verbose:
            print(f"processed {iters} new iterations")

    def select(self, f=None):
        if f is None:
            f = (lambda x: x.n)

        return max(self.children, key=f)

    def simulate(self, maximizer=True):
        raise NotImplementedError

class AlphaMontyCarlo(MontyCarlo):
    """Experimental: Alpha Zero inspired variant of MontyCarlo treesearch."""
    def init(self, entry=None, policy=None):
        self.prior = None if policy is None else policy.get(entry[1], 0)
        return super().init(entry)

    def weight(self, child, c=1, p=0.5):
        q = 1 - (child.v / child.n if child.n > 0 else p)
        un = math.sqrt(self.n / (child.n + 1))
        u = c * child.prior * un
        return q + u
