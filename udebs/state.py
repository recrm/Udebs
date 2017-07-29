import copy
import functools
import random

@functools.total_ordering
class Result:
    def __init__(self, name, value=None):
        self.name = name
        self.value = value
        
    def __eq__(self, other):
        if isinstance(other, Result):
            return self.value == other.value
        return self.value == other
        
    def __lt__(self, other):
        check = self.value
        if self.value == None:
            check = 0

        if isinstance(other, Result):
            checko = other.value
            if other.value == None:
                checko = 0
        
            return check < checko
        
        return check < other
        
    def __repr__(self):
        return "{}:{}".format(self.name, self.value)

class State:
    """A State space calculator designed for TicTacToe."""
    def __init__(self, state, algorithm="bruteForce", storage=None):
        # Instantiating class
        self.state = state
        self.algorithm = algorithm
        self.storage = {} if storage is None else storage
        self.pState = self.pState(state)
        
    def substates(self):
        """Iterate over substates to a state."""
        stateNew = copy.deepcopy(self.state)

        for move in self.legalMoves(self.state):
            if stateNew.controlMove(*move):
                yield self.__class__(stateNew, self.algorithm, self.storage)
                stateNew = copy.deepcopy(self.state)

    def result(self, minimizer=False, *args, **kwargs):
        """Calculate the best solution to a substate."""

        # If already solved return solution.
        if self.pState in self.storage:
            return self.storage[self.pState]

        # Check if we are in a leaf.
        endState = self.endState(self.state)
        if endState is not None:
            best = self.storage[self.pState] = Result(self.pState, endState)
        else:
            best = getattr(self, self.algorithm)(minimizer, *args, **kwargs)

        return best

    #---------------------------------------------------
    #                    Solvers                       -
    #---------------------------------------------------
    def alphaBeta(self, minimizer, alpha=None, beta=None):
        """Simple implementation of alpha beta search
        Only saves node result if a search completes because prune is contextual.
        """
        if alpha is None:
            alpha = -float("inf")
            beta = float("inf")
        
        value = -float("inf")
        if minimizer:
            value *= -1
        
        for state in self.substates():
            result = state.result(not minimizer, alpha, beta)
            
            if minimizer:
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
            self.storage[self.pState] = value
        
        return value
    
    def bruteForce(self, minimizer):
        """Brute force method for solving a game tree.
        Opens every node in the tree.
        """
        results = [i.result(not minimizer) for i in self.substates()]
        
        if minimizer:
            best = min(results)
        else:
            best = max(results)
            
        self.storage[self.pState] = best                
        return best
        
    def bruteForceLoop(self, minimizer):
        """Modified brute force solution for a situation where a game can loop in on itself.
        example - chopsticks.
        
        Note - This method is not guerenteed to work. 
        """
        self.storage[self.pState] = Result(self.pState)
        
        results = [i.result(not minimizer) for i in self.substates()]
        
        if minimizer:
            best = min(results)
        else:
            best = max(results)
            
        for key, value in self.storage.items():
            if value.name == self.pState:
                self.storage[key] = best
                
        return self.storage[self.pState]
                
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
