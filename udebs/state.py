import copy
import functools
from multiprocessing import Pool

def resolve(state):
    return state.result(), state.storage

class ResultException(Exception):
    def __init__(self, map_):
        self.map = map_
    def __repr__(self):
        self.map.show()
        return "stopped doing this map"

@functools.total_ordering
class Result:
    def __init__(self, name, value=None, probability=1, turns=0):
        self.name = name
        self.cvalue = self.value = value
        if self.cvalue is None:
            self.cvalue = 0

        self.probability = probability
        self.turns = turns

    def __eq__(self, other):
        if isinstance(other, Result):
            return (self.cvalue, self.turns) == (other.cvalue, other.turns)
        return self.value == other

    def __lt__(self, other):
        if isinstance(other, Result):
            if self.cvalue == other.cvalue:
                if self.cvalue < 0:
                    return self.turns < other.turns
                return self.turns > other.turns
            return self.cvalue < other.cvalue
        return self.cvalue < other

    def __repr__(self):
        return "{}:{}:{}".format(self.name, self.value, self.turns)

    def __int__(self):
        return self.cvalue

class State:
    """A State space calculator designed for TicTacToe."""
    def __init__(self, state, algorithm="bruteForce", storage=None, entry=None, probability=1, debug=False):

        if storage is None:
            storage = {}

        # Instantiating class
        self.state = state
        self.storage = storage
        self.entry = entry
        self.probability = probability
        self.algorithmf = getattr(self, algorithm)
        self.algorithm = algorithm
        self.debug = debug

    @property
    def pStatew(self):
        if not hasattr(self, "_pState"):
            self._pState = self.pState(self.state)
        return self._pState

    def __repr__(self):
        return "<{} State>".format(self.pStatew)

    def substates(self, time=1):
        """Iterate over substates to a state."""
        stateNew = copy.copy(self.state)
        for move in self.legalMoves(self.state):
            if stateNew.castMove(*move[:3], time=time):
                prob = 1
                if len(move) > 3:
                    prob = move[3]

                newState = self.__class__(stateNew, storage=self.storage, entry=move,
                                          algorithm=self.algorithm, probability=prob)

                if self.debug:
                    print(newState.pStatew, end=" ")
                    print(newState.result().value)

                yield newState
                stateNew = copy.copy(self.state)

    def result(self, *args, force=False, **kwargs):
        """Calculate the best solution to a substate."""
        # If already solved return solution.
        if not force:
            if not self.debug:
                if self.pStatew in self.storage:
                    return self.storage[self.pStatew]

        # Check if we are in a leaf.
        endState = self.endState(self.state)
        if endState is not None:
            best = self.storage[self.pStatew] = self.createResult(endState)
        else:
            best = self.algorithmf(*args, force=force, **kwargs)

        if self.debug:
            print("final", best)

        return best

    def createResult(self, value, **kwargs):
        """Create a result object based on self."""
        return Result(name=self.pStatew, value=value, probability=self.probability, **kwargs)

    def parApply(self, par, *args, **kwargs):
        """Open child nodes in parallel"""
        with Pool(processes=par) as pool:
            gen = ((i, *args) for i in self.substates(**kwargs))
            results = pool.starmap(resolve, gen)

        scores = []
        for result, storage in results:
            self.storage.update(storage)
            scores.append(result)

        return scores

    #---------------------------------------------------
    #                    Solvers                       -
    #---------------------------------------------------
    def alphaBeta(self, alpha=None, beta=None, **kwargs):
        """Simple implementation of alpha beta search
        Only saves node result if a search completes because prune is contextual.
        """
        if alpha is None:
            alpha = -float("inf")
            beta = float("inf")

        value = -float("inf")
        if self.state.time % 2:
            value *= -1

        for state in self.substates():
            result = state.result(alpha, beta)

            if self.state.time % 2:
                if result < value:
                    value = result

                if result < beta:
                    beta = result
            else:
                if result > value:
                    value = result

                if result > alpha:
                    alpha = result

            if alpha >= beta:
                break
        else:
            self.storage[self.pStatew] = value

        return value

    def bruteForce(self, par=False, **kwargs):
        """Brute force method for solving a game tree.
        Opens every node in the tree.
        """
        if par:
            results = self.parApply(par)
        else:
            results = [i.result() for i in self.substates()]

        if self.state.time % 2:
            best = min(results)
        else:
            best = max(results)

        final = self.createResult(best.value, turns=best.turns + 1)

        self.storage[self.pStatew] = final
        return final

    def bruteForceLoop(self, force=False, deps=None, states=None, **kwargs):
        """Modified brute force solution for a situation where a game can loop in on itself.
        example - chopsticks.
        Note - This method is not guerenteed to work.
        Also - This method cannot count turns to victory.
        """
        if deps is None:
            deps = {}

        if states is None:
            states = {}

        self.storage[self.pStatew] = self.createResult(None)

        substates = list(self.substates())
        results = [i.result(deps=deps, states=states) for i in substates]

        if self.state.time % 2:
            best = min(results)
        else:
            best = max(results)

        if best == None:
            states[self.pStatew] = self
            for s, r in zip(substates, results):
                if r == None:
                    if s.pStatew not in deps:
                        deps[s.pStatew] = []

                    deps[s.pStatew].append(self.pStatew)

        else:
            self.storage[self.pStatew] = best

            for i in deps.get(self.pStatew, []):
                states[i].result(deps=deps, states=states, force=True)

            deps.pop(self.pStatew, None)

        return self.storage[self.pStatew]

    def expectationValue(self, par=False, time=0, **kwargs):
        if par:
            results = self.parApply(par, time=time)
        else:
            results = [i.result(time=time) for i in self.substates(time=time)]

        total = sum(i.value * i.probability for i in results)

        self.storage[self.pStatew] = self.createResult(total)
        return self.storage[self.pStatew]

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

    def endState(self, state, entry):
        raise NotImplementedError
