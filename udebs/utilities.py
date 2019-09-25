import traceback
import itertools
import time
from udebs import interpret, entity
from functools import singledispatch, update_wrapper

class Timer:
    def __enter__(self):
        self.time = time.time()

    def __exit__(self, *args, **kwargs):
        print(time.time() - self.time)

def dispatchmethod(func):
    """
    This provides for a way to use ``functools.singledispatch`` inside of a class. It has the same
    basic interface that ``singledispatch`` does:
    
    >>> class A:
    ...     @dispatchmethod
    ...     def handle_message(self, message):
    ...         # Fallback code...
    ...         pass
    ...     @handle_message.register(int)
    ...     def _(self, message):
    ...         # Special int handling code...
    ...         pass
    ...
    >>> a = A()
    >>> a.handle_message(42)
    # Runs "Special int handling code..."
    
    Note that using ``singledispatch`` in these cases is impossible, since it tries to dispatch
    on the ``self`` argument, not the ``message`` argument. This is technically a double
    dispatch, since both the type of ``self`` and the type of the second argument are used to
    determine what function to call - for example:
    
    >>> class A:
    ...     @dispatchmethod
    ...     def handle_message(self, message):
    ...         print('A other', message)
    ...         pass
    ...     @handle_message.register(int)
    ...     def _(self, message):
    ...         print('A int', message)
    ...         pass
    ...
    >>> class B:
    ...     @dispatchmethod
    ...     def handle_message(self, message):
    ...         print('B other', message)
    ...         pass
    ...     @handle_message.register(int)
    ...     def _(self, message):
    ...         print('B int', message)
    ...
    >>> def do_stuff(A_or_B):
    ...     A_or_B.handle_message(42)
    ...     A_or_B.handle_message('not an int')
    
    On one hand, either the ``dispatchmethod`` defined in ``A`` or ``B`` is used depending
    upon what object one passes to ``do_stuff()``, but on the other hand, ``do_stuff()``
    causes different versions of the dispatchmethod (found in either ``A`` or ``B``) 
    to be called (both the fallback and the ``int`` versions are implicitly called).
    
    Note that this should be fully compatable with ``singledispatch`` in any other respects
    (that is, it exposes the same attributes and methods).
    """
    dispatcher = singledispatch(func)

    def register(type, func=None):
        if func is not None:
            return dispatcher.register(type, func)
        else:
            def _register(func):
                return dispatcher.register(type)(func)
            
            return _register

    def dispatch(type):
        return dispatcher.dispatch(type)

    def wrapper(inst, dispatch_data, *args, **kwargs):
        cls = type(dispatch_data)
        impl = dispatch(cls)
        return impl(inst, dispatch_data, *args, **kwargs)

    wrapper.register = register
    wrapper.dispatch = dispatch
    wrapper.registry = dispatcher.registry
    wrapper._clear_cache = dispatcher._clear_cache
    update_wrapper(wrapper, func)
    return wrapper

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
            if isinstance(arg, entity.Entity):
                arg = arg.name

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

def wrapproperty(f):
    """Allows a method to memoize itself."""
    def wrapper(obj, *args, **kwargs):

        name = "_" + f.__name__
        if not hasattr(obj, name) or getattr(obj, name) is None:
            setattr(obj, name, f(obj, *args, **kwargs))

        return getattr(obj, name)

    return wrapper

class Player:
    def __init__(self, name):
        interpret.importModule({name: {
            "f": "f_" + name,
            "args": ["self"],
        }}, {"f_" + name: self})

    def __call__(self, state):
        raise NotImplementedError("Player subclasses should implement a __call__ method.")
