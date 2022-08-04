import itertools
import time
import inspect
import traceback
import functools

from udebs.interpret import importModule


# ---------------------------------------------------
#                  Utilities                       -
# ---------------------------------------------------
# from udebs.treesearch.utilities import count_recursion


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


def register_raw(func, local=None, globs=None, name=None):
    """Use this to register a function without using a decorator.
    func - The function to register
    local - Local call pattern for given function.
    globs - Dictionary of global objects to add to udebs.
    name - Name to give function (defaults to func.__name__)

    .. code-block:: python

        def TEST2(arg1, arg2, arg3):
                return "hello world"

        udebs.register(TEST2, {"args": ["$1", "$2", "$3"]})


    """
    f_name = func.__name__ if name is None else name

    if local is None:
        local = {}

    if globs is None:
        globs = {}

    local_vars = {f_name: {"f": f_name}}
    if isinstance(local, list):
        local_vars[f_name]["args"] = local
    else:
        local_vars[f_name].update(local)

    global_vars = {f_name: func() if inspect.isclass(func) else func}
    global_vars.update(globs)

    importModule(local_vars, global_vars)
    return func


def register(local_raw=None, globs_raw=None, name=None):
    """Register a function with udebs using a decorator.

    .. code-block:: python

        @udebs.register({"args": ["$1", "$2", "$3"]})
        def TEST(arg1, arg2, arg3):
            return "hello world"

        @udebs.register({"args": ["$1", $2, $3]})
        class Test3:
            def __init__(self):
                self.message = "hello "

            def __call__(self, world):
                return self.message + world


    .. code-block:: xml

        <i>TEST one two three</i>

    """
    if hasattr(local_raw, "__name__"):
        return register_raw(local_raw)

    return lambda f: register_raw(f, local_raw, globs_raw, name)


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
