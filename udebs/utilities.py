import traceback
import itertools
import time
from udebs import interpret, entity

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

def norecurse(f):
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
    """Register a placeholder function that will be allocated after the udebs instance is created."""
    interpret.importModule({name: {
        "f": "f_" + name,
        "args": ["self"],
    }}, {"f_" + name: lambda x: None})

class Player:
    """Base Class for players."""
    def __init__(self, name):
        interpret.importModule({name: {
            "f": "f_" + name,
            "args": ["self"],
        }}, {"f_" + name: self})

    def __call__(self, state):
        raise NotImplementedError("Player subclasses should implement a __call__ method.")

def register(args, second=None):
    """Register a function with udebs. Works as a function or a decorator.

    .. code-block:: python

        @udebs.register({"args": ["$1", "$2", "$3"]})
        def TEST(arg1, arg2, arg3):
            return "hello world"

        def TEST2(arg1, arg2, arg3):
            return "hello world"

        udebs.register(TEST2, {"args": ["$1", "$2", "$3"]})

    .. code-block:: xml

        <i>TEST one two three</i>

    """
    if second is not None:
        interpret.importFunction(args, second)
        return None

    def wrapper(f):
        interpret.importFunction(f, args)
        return f

    return wrapper

