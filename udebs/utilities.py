import traceback
import itertools
import time
from udebs import interpret, entity

class Timer:
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
    interpret.importModule({name: {
        "f": "f_" + name,
        "args": ["self"],
    }}, {"f_" + name: lambda x: None})

class Player:
    def __init__(self, name):
        interpret.importModule({name: {
            "f": "f_" + name,
            "args": ["self"],
        }}, {"f_" + name: self})

    def __call__(self, state):
        raise NotImplementedError("Player subclasses should implement a __call__ method.")
