import copy
import functools
import math
from .instance import Instance

def countrecursion(f=None, verbose=False):
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
    @leafreturn
    @udebs_cache
    def result(self, maximizer=True):
        options = []
        for child, _ in self.substates():
            options.append(child.result(not maximizer))

        result = (max if mximizer else min)(options)
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
            raise Exception("Node has no children or value:", pState)

        return value

class BruteLoop(State):
    @leafreturn
    def result(self, maximizer=True, deps=None, states=None, storage=None):
        """Modified brute force solution for a situation where a game can loop in on itself.
        example - chopsticks.
        Note - This method is not guerenteed to work.
        Note - Should be implemented as a special algorithm for chopsticks and not included release.
        """
        pState = self.pState()
        if pState not in storage:
            storage[pState] = None
            substates, results = [], []
            for child, entry in self.substates():
                substates.append(child)
                results.append(child.result(not maximizer, deps=deps, states=states, storage=storage))

            best = (max if maximizer else min)(results, key=lambda x: 0 if x is None else x)

            if best is None:
                # If value is not found record dependencies and return None
                states[pState] = self
                for s, r in zip(substates, results):
                    if r is None:
                        child_pState = s.pState()
                        if child_pState not in deps:
                            deps[child_pState] = set()

                        deps[child_pState].add(pState)

            else:
                # If value is found reprocess dependant nodes.
                storage[pState] = best

                for i in deps.get(pState, []):
                    states[i].result(not maximizer, deps=deps, states=states, storage=storage)

                deps.pop(pState, None)

        return storage[pState]

#---------------------------------------------------
#   Monty Carlo / Not currently Instance subclass  -
#---------------------------------------------------
class AlphaMontyCarlo():
    def __init__(self, state, entry=None, prior=None):
        self.state = state
        self.children = None
        self.v = 0
        self.n = 0
        self.prior = prior
        self.entry = entry

    def substates(self, state, time=1):
        """Iterate over substates to a state."""
        stateNew = None
        for move in self.legalMoves(state):
            if stateNew is None:
                stateNew = copy.copy(state)

            if stateNew.castMove(*move[:3]):
                stateNew.controlTime(time)
                yield stateNew, move
                stateNew = None

    def result(self, maximizer=True, **kwargs):
        if self.children is None:
            value, policy = self.simulate(maximizer, **kwargs)
            self.children = []
            for child, entry in self.substates(self.state):
                node = self.__class__(child, entry=entry, prior=policy.get(entry[1], 0))
                self.children.append(node)

        else:
            # selection
            node = max(self.children, key=self.weight)
            value = node.result(not maximizer, **kwargs)
            value = 1 - value

        self.v += value
        self.n += 1
        return self.v / self.n

    def weight(self, child, c=1, p=0.5):
        q = 1 - (child.v / child.n if child.n > 0 else p)
        un = math.sqrt(self.n / (child.n + 1))
        u = c * child.prior * un
        return q + u

    def simulate(self, maximizer=True):
        raise NotImplementedError

class MontyCarlo():
    def __init__(self, state, entry=None, prior=None):
        self.state = state
        self.children = None
        self.v = 0
        self.n = 0
        self.entry = entry

    def substates(self, state, time=1):
        """Iterate over substates to a state."""
        stateNew = None
        for move in self.legalMoves(state):
            if stateNew is None:
                stateNew = copy.copy(state)

            if stateNew.castMove(*move[:3]):
                stateNew.controlTime(time)
                yield stateNew, move
                stateNew = None

    def result(self, maximizer=True, **kwargs):
        if self.children is None:
            value = self.simulate(maximizer, **kwargs)
            self.children = []
            for child, entry in self.substates(self.state):
                node = self.__class__(child, entry=entry)
                self.children.append(node)

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

    def simulate(self, maximizer=True):
        raise NotImplementedError