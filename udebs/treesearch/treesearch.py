import math
import time
from udebs.instance import Instance
from udebs.treesearch.utilities import cache, alpha_beta_cache


class State(Instance):
    """Base class for all tree search algorithms."""

    def substates(self):
        """Iterate over substates to a state.

        yields a tuple, (child instance, action tuple)
        if the legalMoves iterator yielded something other than a tuple. This method will yield just that object for both values.
        """
        new_state = self.copy()
        for move in self.legalMoves():
            if new_state.castMove(*move):
                yield new_state, move
                new_state = self.copy()

    def hash(self):
        """Implement this function if you plan on using treesearch.cache"""
        raise NotImplementedError

    def legalMoves(self):
        """This function must be implemented. Iterate over all (caster, target, move) tuples that are valid children of current node."""
        raise NotImplementedError

    def endState(self):
        """Example implementations use this function to fetch a states leaf value."""
        return self.value

    def result(self):
        raise NotImplementedError


# ---------------------------------------------------
#             Various Tree Search Algorithms       -
# ---------------------------------------------------
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
    @alpha_beta_cache
    def result(self, alpha, beta, storage):
        value = self.value
        if value is not None:
            return -abs(value)

        current = -float("inf")
        for child in self.substates():
            computed = -child.result(-beta, -alpha, storage)
            if computed > current:
                current = computed
                if computed > alpha:
                    alpha = computed
                    if alpha >= beta:
                        break

        return current


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


# ---------------------------------------------------
#                   Monty Carlo                    -
# ---------------------------------------------------
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
            iters += 1

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
