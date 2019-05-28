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

class State:
    """A State space calculator designed for TicTacToe."""
    algorithm="BruteForce"

    def __init__(self, state, algorithm="bruteForce", storage=None, entry=None, probability=1, debug=False):
        # Instantiating class
        self.state = state
        self.storage = {} if storage is None else storage
        self.entry = entry
        self.probability = probability
        self.algorithm = algorithm
        self.debug = debug

    @property
    def pStatew(self):
        if not hasattr(self, "_pState"):
            self._pState = self.pState(self.state)
        return self._pState

    def __repr__(self):
        return "<{} State>".format(self.pStatew)

    def substates(self):
        """Iterate over substates to a state."""
        stateNew = copy.deepcopy(self.state)
        for move in self.legalMoves(self.state):
            if stateNew.castMove(*move[:3], time=1):
                newState = self.__class__(stateNew, storage=self.storage, entry=move, algorithm=self.algorithm)

                if self.debug:
                    print(newState.pStatew, newState.result())

                if len(move) > 3:
                    newState.probability = move[3]

                yield newState
                stateNew = copy.deepcopy(self.state)

    def result(self, *args, force=False, **kwargs):
        """Calculate the best solution to a substate."""
        try:
            # If already solved return solution.
            if not force:
                if self.pStatew in self.storage:
                    return self.storage[self.pStatew]

            # Check if we are in a leaf.
            endState = self.endState(self.state)
            if endState is not None:
                best = self.storage[self.pStatew] = self.createResult(endState)
            else:
                best = getattr(self, self.algorithm)(*args, force=force, **kwargs)

            if self.debug:
                print("final", self.pStatew, best)

            return best
        except KeyboardInterrupt:
            raise ResultException(self.state.getMap())

    def createResult(self, value, **kwargs):
        """Create a result object based on self."""
        return Result(name=self.pStatew, value=value, probability=self.probability, **kwargs)

    def tree(self):
        """Generates a state tree."""
        if self.algorithm != "bruteForce":
            raise Exception("Generating tree requires bruteForce algorithm.")

        result = self.result()
        if result != 0:
            return result

        moves = {}
        completed = set()
        subtree = False
        for substate in self.substates():
            if substate.pStatew in completed:
                continue

            completed.add(substate.pStatew)

            subresult = substate.tree()
            if isinstance(subresult, Result):
                if subresult.turns == 1:
                    continue
            
            moves[substate.pStatew] = subresult
            if isinstance(subresult, dict):
                subtree = True
            
        if len(moves) == 0:
            return result
        
        if not subtree:
            test = self.checkEqual(moves.values())
            if test is not None:
                return result
        
        return moves

    def checkEqual(self, iterator):
        iterator = iter(iterator)
        try:
            first = next(iterator)
        except StopIteration:
            return None
        
        if all(first == rest for rest in iterator):
            return first
    
    def parApply(self, par, *args):
        """Open child nodes in parallel"""
        with Pool(processes=par) as pool:
            gen = ((i, *args) for i in self.substates())
            results = pool.starmap(resolve, gen)

        scores = []
        for result, storage in results:
            print(len(storage))
            self.storage.update(storage)
            scores.append(result)

        print(len(self.storage))

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
#             states.pop(self.pStatew, None)
        
        return self.storage[self.pStatew]

    def expectationValue(self, par=False):
        if par:
            results = self.parApply(par)
        else:
            results = [i.result() for i in self.substates()]
        
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
