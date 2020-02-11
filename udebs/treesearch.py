import copy
import functools
import math

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

class State:
    def __init__(self, storage=None):
        self.storage = storage if storage is not None else {}

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

    #---------------------------------------------------
    #                    Game Defined functions        -
    #---------------------------------------------------
    def pState(self, state):
        """Return an immutable representation of a game map."""
        def rotate(matrix):
            return tuple(zip(*matrix[::-1]))

        def flip(matrix):
            return tuple(reversed(matrix))

        value = state.map["map"].map

        symetries = [tuple(tuple(i) for i in value)]
        symetries.append(flip(symetries[0]))

        for i in range(6):
            symetries.append(rotate(symetries[-2]))

        return frozenset(symetries)

    def legalMoves(self, state):
        raise NotImplementedError

    def endState(self, state):
        raise NotImplementedError

#---------------------------------------------------
#             Various Tree Search Aglorithms       -
#---------------------------------------------------
class BruteForce(State):
    def result(self, state, maximizer=True):
        pState = self.pState(state)
        if pState not in self.storage:
            value, turns = self.endState(state), 0
            if value is None:
                result = (max if maximizer else min)(self.result(c, not maximizer) for c, e in self.substates(state))
                value, turns = result.value, result.turns + 1

            self.storage[pState] = Result(value, turns)
        return self.storage[pState]

class MarkovChain(State):
    def result(self, state, time=0):
        pState = self.pState(state)
        if pState not in self.storage:
            ev = self.endState(state)
            if ev is None:
                ev = sum(self.result(c, time) * p[3] for c, p in self.substates(state, time))

            self.storage[pState] = ev
        return self.storage[pState]

class AlphaBeta(State):
    def result(self, state, maximizer=True, alpha=-1, beta=1):
        pState = self.pState(state)
        if pState not in self.storage:
            value = self.endState(state)
            if value is None:
                value = -float("inf") if maximizer else float("inf")
                for child, entry in self.substates(state):
                    result = self.result(child, not maximizer, alpha, beta)
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
                        return value

            self.storage[pState] = value

        return self.storage[pState]

class AlphaMontyCarlo(State):
    def __init__(self, state, entry=None, prior=None):
        self.state = state
        self.children = None
        self.v = 0
        self.n = 0
        self.prior = prior
        self.entry = entry

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

class MontyCarlo(State):
    def __init__(self, state, entry=None, prior=None):
        self.state = state
        self.children = None
        self.v = 0
        self.n = 0
        self.entry = entry

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

class BruteLoop(State):
    def result(self, state, maximizer=True, deps=None, states=None, **kwargs):
        """Modified brute force solution for a situation where a game can loop in on itself.
        example - chopsticks.
        Note - This method is not guerenteed to work.
        Also - This method cannot count turns to victory.
        """
        if deps is None:
            deps = {}

        if states is None:
            states = {}

        pState = self.pState(state)
        if pState not in self.storage:
            self.storage[pState] = self.endState(state)
            if self.storage[pState] is None:

                substates, results = [], []
                for child, entry in self.substates(state):
                    substates.append(child)
                    results.append(self.result(child, not maximizer, deps, states))

                best = (max if maximizer else min)(results, key=lambda x: 0 if x is None else x)

                if best is None:
                    # If value is not found record dependencies and return None
                    states[pState] = state
                    for s, r in zip(substates, results):
                        if r is None:
                            child_pState = self.pState(s)
                            if child_pState not in deps:
                                deps[child_pState] = set()

                            deps[child_pState].add(pState)

                else:
                    # If value is found reprocess dependant nodes.
                    self.storage[pState] = best

                    for i in deps.get(pState, []):
                        self.result(states[i], not maximizer, deps=deps, states=states)

                    deps.pop(pState, None)

        return self.storage[pState]