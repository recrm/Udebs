import traceback
import itertools
import time
import inspect
import functools
from collections import OrderedDict

from .interpret import importModule


# ---------------------------------------------------
#                  Utilities                       -
# ---------------------------------------------------

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


class Timer:
    """Basic Timing context manager. Prints out the time it takes it's context to close."""

    def __init__(self, verbose=True):
        self.verbose = verbose
        self.total = None

    def __enter__(self, verbose=True):
        self.time = time.perf_counter()
        return self

    def __exit__(self, *args, **kwargs):
        self.total = time.perf_counter() - self.time
        if self.verbose:
            print("total time:", self.total)

    def __str__(self):
        return str(self.total)


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


def no_recurse(f):
    """Wrapper function that forces a function to return True if it recurse."""

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


def register(f, args=None, name=None):
    """Register a function with udebs. Works as a function or a decorator.

    .. code-block:: python

        @udebs.register({"args": ["$1", "$2", "$3"]})
        def TEST(arg1, arg2, arg3):
            return "hello world"

        def TEST2(arg1, arg2, arg3):
            return "hello world"

        udebs.register(TEST2, {"args": ["$1", "$2", "$3"]})

        @udebs.register({"args": ["$1", $2, $3]})
        class Test3:
            def __init__(self):
                self.message = "hello "

            def __call__(self, world):
                return self.message + world


    .. code-block:: xml

        <i>TEST one two three</i>

    """

    def wrapper(args2, f2):
        f_name = f2.__name__ if name is None else name

        if isinstance(args2, list):
            args2 = {"args": args2}

        importModule({
            f_name: {
                "f": f_name,
                **args2,
            }
        }, {f_name: f2() if inspect.isclass(f2) else f2})
        return f2

    if args is None:
        return functools.partial(wrapper, f)

    return wrapper(args, f)


# ---------------------------------------------------
#                  Deprecated                      -
# ---------------------------------------------------

def placeholder(name):
    """Register a placeholder function that will be allocated after the udebs instance is created.

    **deprecated - just register an empty function.
    """
    importModule({name: {
        "f": "f_" + name,
        "args": ["self"],
    }}, {"f_" + name: lambda x: None})


class Player:
    """Base Class for players.

    **deprecated - please use udebs.utilities.register
    """

    def __init__(self, name):
        importModule({name: {
            "f": "f_" + name,
            "args": ["self"],
        }}, {"f_" + name: self})

    def __call__(self, state):
        raise NotImplementedError("Player subclasses should implement a __call__ method.")


def lookup(name, table):
    """Function for adding a basic lookup function to the interpreter.

    ** deprecated - please use custom function.
    """

    def wrapper(*args):
        value = table
        for arg in args:
            try:
                value = value[arg]
            except KeyError:
                return 0

        return value

    importModule({name: {
        "f": "f_" + name,
        "all": True,
    }}, {"f_" + name: wrapper})
