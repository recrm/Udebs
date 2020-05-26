import copy
import functools
import math
import time
from .instance import Instance

def countrecursion(f=None, verbose=True):
    """Function decorator, prints how many times a function calls itself."""
    time = 0
    def count(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            if "verbose" in kwargs:
                nonlocal verbose
                verbose = kwargs.pop("verbose")

            nonlocal time
            p = (time == 0)
            time +=1
            r = f(*args, **kwargs)
            if p and verbose:
                print("nodes visited:", time)
            return r
        return wrapper

    if f is None:
        return count
    return count(f)

def leafreturn(f):
    """Function decorator, imediatly returns if self.endState or self.value is not None."""
    @functools.wraps(f)
    def wrapper(self, *args, **kwargs):
        value = self.endState()
        if value is not None:
            return value
        return f(self, *args, **kwargs)
    return wrapper

def udebs_cache(f=None, maxsize=128, storage=None):
    """Function decorator, lru_cache handling Instance objects as str(Instance)."""
    if storage is None:
        storage = {}

    def cache(f):
        @functools.wraps(f)
        def wrapper(self, *args, **kwargs):
            if "storage" in kwargs:
                nonlocal storage
                storage = kwargs.pop("storage")

            key = (self.pState(), *args)

            if key in storage:
                return storage[key]

            storage[key] = f(self, *args, **kwargs)
            return storage[key]

        return wrapper

    if f is None:
        return cache
    return cache(f)

@functools.total_ordering
class Result:
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
    def substates(self, time=1):
        """Iterate over substates to a state."""
        stateNew = None
        for move in self.legalMoves():
            if stateNew is None:
                stateNew = copy.copy(self)

            if stateNew.castMove(*move[:3]):
                stateNew.controlTime(self.increment)
                yield stateNew, move
                stateNew = None

    def pState(self):
        return str(self)

    def legalMoves(self):
        raise NotImplementedError

    def endState(self):
        return self.value

#---------------------------------------------------
#             Various Tree Search Aglorithms       -
#---------------------------------------------------
class BruteForce(State):
    @countrecursion
    @udebs_cache
    def result(self, maximizer=True):
        value = self.endState()
        if value is not None:
            return Result(value, 0)

        options = []
        for child, _ in self.substates():
            options.append(child.result(not maximizer))

        result = (max if maximizer else min)(options)
        return Result(result.value, result.turns + 1)

class MarkovChain(State):
    @countrecursion
    @leafreturn
    @udebs_cache
    def result(self):
        total = 0
        for child, p in self.substates():
            total += child.result() * p[3]

        return total

class AlphaBeta(State):
    @countrecursion
    @leafreturn
    @udebs_cache
    def result(self, maximizer=True, alpha=-float("inf"), beta=float("inf")):
        value = -float("inf") if maximizer else float("inf")
        for child, e in self.substates():
            result = child.result(not maximizer, alpha, beta)

            if maximizer:
                if result > value:
                    value = result
                    if result > alpha:
                        alpha = result
            else:
                if result < value:
                    value = result
                    if result < beta:
                        beta = result

            if alpha >= beta:
                break

        if abs(value) == float("inf"):
            raise Exception("Tried to return infinite value. Either alpha > beta or node has no children:", pState)

        return value

#---------------------------------------------------
#                   Monty Carlo                    -
#---------------------------------------------------
class MontyCarlo(State):
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
    def init(self, entry=None, policy=None):
        self.prior = None if policy is None else policy.get(entry[1], 0)
        return super().init(entry)

    def weight(self, child, c=1, p=0.5):
        q = 1 - (child.v / child.n if child.n > 0 else p)
        un = math.sqrt(self.n / (child.n + 1))
        u = c * child.prior * un
        return q + u
