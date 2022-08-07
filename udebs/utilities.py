import itertools
import time
import traceback
import functools

# ---------------------------------------------------
#                  Utilities                       -
# ---------------------------------------------------


def modify_state(state, entities=None, logging=True, revert=True):
    """Experimental: Creates a copy of an Instance object with modifications designed for improved tree search."""
    if entities is None:
        entities = {}
    clone = state.copy()
    if logging:
        clone.logging = True

    if revert:
        clone.revert = 0
        clone.state = False

    if entities is not None:
        for key, attributes in entities.items():
            new = state[key].copy()

            for name, value in attributes.items():
                setattr(new, name, value)

            clone[key] = new

    return clone


class Timer:
    """Basic Timing context manager. Prints out the time it takes its context to close."""

    def __init__(self, verbose=True, name=""):
        self.verbose = verbose
        self.total = None
        self.name = name

    def __enter__(self, verbose=True):
        self.time = time.perf_counter()
        return self

    def __exit__(self, *args, **kwargs):
        self.total = time.perf_counter() - self.time
        if self.verbose:
            print("({})".format(self.name), "total time:", self.total)

    def __str__(self):
        return str(self.total)


def no_recurse(f):
    """Wrapper function that forces a function to return True if it recurse."""

    @functools.wraps(f)
    def func(*args, **kwargs):
        for i in traceback.extract_stack():
            if i[2] == f.__name__:
                return True

        return f(*args, **kwargs)

    return func


def alternate(*args):
    """An alternation function for processing moves."""
    processed = []
    for i in args:
        if not isinstance(i, list):
            i = [i]
        processed.append(i)

    maximum = max(len(i) for i in processed)
    gen = (itertools.islice(itertools.cycle(i), maximum) for i in processed)
    yield from zip(*gen)
