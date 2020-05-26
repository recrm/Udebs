import traceback
import itertools
import time
import inspect
from functools import partial

from .interpret import importModule

#---------------------------------------------------
#                  Utilities                       -
#---------------------------------------------------

class Timer:
    """Basic Timing context manager. Prints out the time it takes it's context to close."""
    def __init__(self, verbose=True):
        self.verbose = verbose
        self.total = None

    def __enter__(self, verbose=True):
        self.time = time.time()
        return self

    def __exit__(self, *args, **kwargs):
        self.total = time.time() - self.time
        if self.verbose:
            print("total time:", self.total)

    def __str__(self):
        return str(self.total)

def norecurse(f):
    """Wrapper function that forces a function to return True if it recurses."""
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
    def wrapper(args, f):
        f_name = f.__name__ if name is None else name

        if isinstance(args, list):
            args = {"args": args}

        importModule({
            f_name: {
                "f": f_name,
                **args,
            }
        }, {f_name: f() if inspect.isclass(f) else f})
        return f

    if args is None:
        return partial(wrapper, f)

    return wrapper(args, f)

#---------------------------------------------------
#                  Depricated                      -
#---------------------------------------------------

def placeholder(name):
    """Register a placeholder function that will be allocated after the udebs instance is created.

    **depricated - just register an empty function.
    """
    importModule({name: {
        "f": "f_" + name,
        "args": ["self"],
    }}, {"f_" + name: lambda x: None})

class Player:
    """Base Class for players.

    **depricated - please use udebs.utilities.register
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

    ** depricated - please use custom function.
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