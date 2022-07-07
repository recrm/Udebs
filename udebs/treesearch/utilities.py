import functools
from collections import OrderedDict


def cache(f=None, maxsize=None, storage=None):
    """Function decorator, lru_cache handling Instance objects as str(Instance)."""
    if maxsize is None:
        maxsize = float("inf")

    if storage is None:
        storage = OrderedDict()

    def cache_inside(f2):
        @functools.wraps(f2)
        def cache_wrapper(self, *args, **kwargs):
            key = (self.hash(), *args)
            value = storage.get(key, None)
            if value is None:
                value = f2(self, *args, **kwargs)
                storage[key] = value
            else:
                storage.move_to_end(key)

            while storage.__len__() > maxsize:
                storage.popitem(False)

            return value

        return cache_wrapper

    if f is None:
        return cache_inside
    return cache_inside(f)


def alpha_beta_cache(f, maxsize=2 ** 20):
    empty = (-float("inf"), float("inf"))

    @functools.wraps(f)
    def cache_wrapper(self, alpha, beta, storage):
        key = self.hash()

        a_, b_ = storage.get(key, empty)
        if a_ > alpha:
            alpha = a_

        if b_ < beta:
            beta = b_

        if alpha >= beta:
            # Note: Alpha and beta may not be the same.
            # Returning either will produce the right answer, but
            # it is unclear which is more efficient.
            if key in storage:
                storage.move_to_end(key)
            return alpha

        result = f(self, alpha, beta, storage)
        if result <= alpha:
            storage[key] = (a_, result)
        elif result >= beta:
            storage[key] = (result, b_)
        else:
            storage[key] = (result, result)

        storage.move_to_end(key)
        if storage.__len__() > maxsize:
            storage.popitem(False)

        return result

    return cache_wrapper


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


def count_recursion(f):
    """Function decorator, prints how many times a function calls itself."""
    start_time = 0

    @functools.wraps(f)
    def count_recursion_wrapper(*args, **kwargs):
        nonlocal start_time
        p = (start_time == 0)
        start_time += 1
        r = f(*args, **kwargs)
        if p:
            print("nodes visited:", start_time)
            start_time = 0
        return r

    return count_recursion_wrapper


countrecursion = count_recursion
