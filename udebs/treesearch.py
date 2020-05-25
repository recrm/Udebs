import copy
import functools
import math
from .instance import Instance

class MutableInt:
    def __init__(self):
        self.value = 0

    def inc(self):
        self.value +=1

    def __str__(self):
        return str(self.value)

def countrecursion(f):
    """Function decorator, prints how many times a function calls itself."""
    def wrapper(*args, times=None, **kwargs):
        p = False
        if times is None:
            times = MutableInt()
            p = True

        times.inc()
        r = f(*args, times=times, **kwargs)
        if p:
            print("nodes visited:", times)
        return r

    return wrapper

def prefill(arguments):
    def outer(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            for i in arguments:
                if kwargs.get(i) is None:
                    kwargs[i] = {}

            return f(*args, **kwargs)

        return wrapper
    return outer

def leafreturn(f):
    @functools.wraps(f)
    def wrapper(self, *args, **kwargs):
        value = self.endState()
        if value is not None:
            return value
        return f(self, *args, **kwargs)
    return wrapper

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
                stateNew.controlTime(time)
                yield stateNew, move
                stateNew = None

    def pState(self):
        raise NotImplementedError

    def legalMoves(self):
        raise NotImplementedError

    def endState(self):
        return self.value

#---------------------------------------------------
#             Various Tree Search Aglorithms       -
#---------------------------------------------------
class BruteForce(State):
    @prefill(["storage"])
    @leafreturn
    def result(self, maximizer=True, storage=None, **kwargs):
        pState = self.pState()
        if pState not in storage:
            gen = (c.result(not maximizer, storage=storage, **kwargs) for c, e in self.substates())
            result = (max if maximizer else min)(gen)
            storage[pState] = Result(result.value, result.turns + 1)
        return storage[pState]

class MarkovChain(State):
    @prefill(["storage"])
    @leafreturn
    def result(self, time=0, storage=None, **kwargs):
        pState = self.pState()
        if pState not in storage:
            gen = (c.result(time, storage=storage, **kwargs) * p[3] for c, p in self.substates(time))
            storage[pState] = sum(gen)
        return storage[pState]

class AlphaBeta(State):
    @prefill(["storage", "partial"])
    @leafreturn
    def result(self, maximizer=True, alpha=-1, beta=1, time=1, storage=None, partial=None, **kwargs):
        pState = self.pState()
        if pState not in storage:

            label = beta if maximizer else alpha
            if partial.get(pState, {}).get(label, None) is not None:
                return partial[pState][label]

            value = -float("inf") if maximizer else float("inf")
            for child, e in self.substates(time=time):
                result = child.result(not maximizer, alpha, beta, time, storage=storage, partial=partial, **kwargs)

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
                    if pState not in partial:
                        partial[pState] = {}

                    partial[pState][label] = value

                    return value

            storage[pState] = value

        return storage[pState]

class BruteLoop(State):
    @prefill(["deps", "states", "storage"])
    @leafreturn
    def result(self, maximizer=True, deps=None, states=None, storage=None, **kwargs):
        """Modified brute force solution for a situation where a game can loop in on itself.
        example - chopsticks.
        Note - This method is not guerenteed to work.
        """
        pState = self.pState()
        if pState not in storage:
            storage[pState] = None
            substates, results = [], []
            for child, entry in self.substates():
                substates.append(child)
                results.append(child.result(not maximizer, deps=deps, states=states, storage=storage, **kwargs))

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
                    states[i].result(not maximizer, deps=deps, states=states, storage=storage, **kwargs)

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