import traceback
import itertools
import time
from . import interpret, entity
from functools import partial
import inspect

class Timer:
    """Basic Timing context manager. Prints out the time it takes it's context to close."""
    def __enter__(self):
        self.time = time.time()
        return self

    def __exit__(self, *args, **kwargs):
        print(time.time() - self.time)

#---------------------------------------------------
#                  Utilities                       -
#---------------------------------------------------

def _norecurse(f):
    """Wrapper function that forces a function to return True if it recurses."""
    def func(*args, **kwargs):
        for i in traceback.extract_stack():
            if i[2] == f.__name__:
                return True

        return f(*args, **kwargs)

    return func

def lookup(name, table):
    """Function for adding a basic lookup function to the interpreter."""
    def wrapper(*args):
        value = table
        for arg in args:
            try:
                value = value[arg]
            except KeyError:
                return 0

        return value

    interpret.importModule({name: {
        "f": "f_" + name,
        "all": True,
    }}, {"f_" + name: wrapper})

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

def placeholder(name):
    """Register a placeholder function that will be allocated after the udebs instance is created.

    **depricated - just register an empty function.
    """
    interpret.importModule({name: {
        "f": "f_" + name,
        "args": ["self"],
    }}, {"f_" + name: lambda x: None})

class Player:
    """Base Class for players.

    **depricated - please use udebs.utilities.register
    """
    def __init__(self, name):
        interpret.importModule({name: {
            "f": "f_" + name,
            "args": ["self"],
        }}, {"f_" + name: self})

    def __call__(self, state):
        raise NotImplementedError("Player subclasses should implement a __call__ method.")

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

        interpret.importModule({
            f_name: {
                "f": f_name,
                **args,
            }
        }, {f_name: f() if inspect.isclass(f) else f})
        return f

    if args is None:
        return partial(wrapper, f)

    return wrapper(args, f)

