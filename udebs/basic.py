from udebs.interpret import register, Variables
import logging

log = logging.getLogger(__name__)

Variables.modules.update({
    "min": {
        "f": "min",
        "all": True
    },
    "max": {
        "f": "max",
        "all": True
    },
    "|": {
        "f": "abs",
        "args": ["$1"]
    },
    "length": {
        "f": "len",
        "args": ["$1"]
    },
    ">": {
        "f": "operator.gt",
        "args": ["-$1", "$1"]
    },
    "<": {
        "f": "operator.lt",
        "args": ["-$1", "$1"]
    },
    ">=": {
        "f": "operator.ge",
        "args": ["-$1", "$1"]
    },
    "<=": {
        "f": "operator.le",
        "args": ["-$1", "$1"]
    },
    "%": {
        "f": "operator.mod",
        "args": ["-$1", "$1"]
    },
    "/": {
        "f": "operator.floordiv",
        "args": ["-$1", "$1"],
        "default": {"-$1": 1}
    },
    "!": {
        "f": "operator.not_",
        "args": ["$1"]
    },
    "-": {
        "f": "operator.sub",
        "args": ["-$1", "$1"],
        "default": {"-$1": 0}
    },
    "$": {
        "f": "storage.__getitem__",
        "args": ["$1"]
    },
})


# ---------------------------------------------------
#            Imports and Variables                  -
# ---------------------------------------------------
@register({"all": True}, name="print")
def print_inner(*args):
    """
    prints extra output to console.

    .. code-block:: xml

        <i>print arg1 arg2 ...</i>
    """
    print(*args)
    log.info(" ".join(str(i) for i in args))
    return True


@register({"args": ["$1", "$2", "$3"], "default": {"$2": True, "$3": False}}, name="if")
def logicif(cond, value, other):
    """
    returns value if condition else other.

    (Note, this function evaluates all conditions regardless of if condition.)
    (Deprecated in version 1.1.0 in favor of AND, OR blocks.)

    .. code-block:: xml

        <i>if cond value other</i>
    """
    return value if cond else other


@register({"args": ["-$1", "$1", "$2"], "default": {"$2": 1}}, name="in")
def inside(before, after, amount=1):
    """
    Returns true if before in after amount times else false.

    .. code-block:: xml

        <i>value in obj</i>
    """
    if isinstance(after, str):
        return before in after

    if amount == 0:
        return True

    count = 0
    for item in after:
        if item == before:
            count += 1
            if count >= amount:
                return True

    return False


@register({"args": ["-$1", "$1", "$2"], "default": {"$2": 1}}, name="not-in")
def notin(*args, **kwargs):
    """
    Returns false if value in obj else true.

    .. code-block:: xml

        <i>value not-in obj</i>
    """
    return not inside(*args, **kwargs)


@register({"all": True}, name="==")
def equal(*args):
    """Checks for equality of args.

    .. code-block:: xml

        <i>== arg1 arg2 ...</i>
        <i>arg1 == arg2</i>
    """
    x = args[0]
    for y in args:
        if y != x:
            return False
    return True


@register({"all": True}, name="!=")
def notequal(*args):
    """Checks for inequality of args.

    .. code-block:: xml

        <i>!= arg1 arg2 ...</i>
        <i>arg1 != arg2</i>
    """
    x = args[0]
    for y in args[1:]:
        if x == y:
            return False
    return True


@register({"all": True}, name="+")
def plus(*args):
    """Sums arguments

    .. code-block:: xml

        <i>arg1 + arg2</i>
        <i>+ arg1 arg2 ...</i>
    """
    return sum(args)


@register(["$1"], name="sum")
def sumation(arg):
    return sum(arg)


@register({"all": True}, name="*")
def multiply(*args):
    """Multiplies arguments

    .. code-block:: xml

        <i>arg1 * arg2</i>
        <i>* arg1 arg2 ...</i>
    """
    i = 1
    for number in args:
        i *= number
    return i


@register(["storage", "-$1", "$1"], name="->")
@register(["storage", "-$1", "$1"], name="=")
def setvar(storage, variable, value):
    """Stores value inside of variable.

    Note: always returns true so can be used in require block.

    .. code-block:: xml

        <i>variable = value</i>
        <i>variable -> value</i>
    """
    storage[variable] = value
    return True


@register(["-$1", "$1"], name="elem")
def sub(array, i):
    """Gets the ith element of array.

    .. code-block:: xml

        <i>array sub i</i>
    """
    try:
        return array[i]
    except IndexError:
        return "empty"
