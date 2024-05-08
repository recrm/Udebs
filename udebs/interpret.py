import inspect

from udebs import errors
import operator


class Variables:
    modules = {}
    env = {
        "__builtins__": {"abs": abs, "min": min, "max": max, "len": len, "getattr": getattr},
        "operator": operator,
    }
    default = {
        "f": "",
        "args": [],
        "kwargs": {},
        "all": False,
        "default": {},
        "string": [],
    }


# ---------------------------------------------------
#            Interpreter Functions                 -
# ---------------------------------------------------
def formatS(string):
    """Converts a string into its python representation."""
    string = str(string)
    if string == "self":
        return string
    elif string == "storage":
        return string
    elif string == "false":
        return "False"
    elif string == "true":
        return "True"
    elif string == "None":
        return string
    elif string.isdigit():
        return string
    # String quoted by user.
    elif string[0] == string[-1] and string[0] in {"'", '"'}:
        return string
    # String has already been handled by call
    elif string[-1] == ")":
        return string
    elif string in Variables.env:
        return string
    # In case prefix notation used in keyword defaults.
    elif string[0] in Variables.modules:
        return interpret(string)
    else:
        return "'" + string + "'"


def call(args, root=False):
    """Converts callList into functionString."""
    # Find keyword
    keywords = [i for i in args if i in Variables.modules]

    # Too many keywords is a syntax error.
    if len(keywords) > 1:
        raise errors.UdebsSyntaxError(f"CallList contains to many keywords '{args}'")

    # No keywords create a tuple object.
    elif len(keywords) == 0 and not root:
        return "(" + ",".join(formatS(i) for i in args) + ")"

    elif len(keywords) == 0 and root:
        raise errors.UdebsSyntaxError(f"No keywords in root objected '{args}'")

    keyword = keywords[0]

    # Get and fix data for this keyword.
    data = {}
    data.update(Variables.default)
    data.update(Variables.modules[keyword])

    # Create dict of values
    current = args.index(keyword)
    nodes = {}
    nodes.update(data["default"])

    for index in range(len(args)):
        value = "$" if index >= current else "-$"
        value += str(abs(index - current))
        if args[index] != keyword:
            nodes[value] = args[index]

    # Force strings into quoted arguments.
    for string in data["string"]:
        new = str(nodes[string]).replace("\\", "\\\\").replace("'", "\\'")
        nodes[string] = f"'{new}'"

    # Claim keyword arguments.
    kwargs = {}
    for key, value in data["kwargs"].items():
        if value in nodes:
            new_value = nodes[value]
            del nodes[value]
        else:
            new_value = value
        kwargs[key] = formatS(new_value)

    arguments = []
    # Insert positional arguments
    for key in data["args"]:
        if key in nodes:
            arguments.append(formatS(nodes[key]))
            del nodes[key]
        else:
            arguments.append(formatS(key))

    # Insert ... arguments.
    if data["all"]:
        for key in sorted(nodes.keys(), key=lambda x: int(x.replace("$", ""))):
            arguments.append(formatS(nodes[key]))
            del nodes[key]

    if len(nodes) > 0:
        raise errors.UdebsSyntaxError("Keyword contains unused arguments. '{" ".join(args)}'")

    # Insert keyword arguments.
    for key in sorted(kwargs.keys()):
        arguments.append(str(key) + "=" + str(kwargs[key]))

    return data["f"] + "(" + ",".join(arguments) + ")"


def split_callstring(raw):
    """Converts callString into call_list."""
    open_bracket = {'(', '{', '['}
    close_bracket = {')', '}', ']'}
    call_list = []
    buf = ''
    in_brackets = 0
    in_quotes = False
    dot_legal = True

    for char in raw.strip():

        if char in {'"', "'"}:
            in_quotes = not in_quotes

        elif not in_quotes:
            if char in open_bracket:
                in_brackets += 1

            elif char in close_bracket:
                in_brackets -= 1

            elif not in_brackets:
                if dot_legal:
                    if char == ".":
                        call_list.append(buf)
                        buf = ''
                        continue

                    elif char.isspace():
                        dot_legal = False
                        if call_list:
                            call_list = [".".join(call_list) + "." + buf]
                            buf = ''

                if char.isspace():
                    if buf:
                        call_list.append(buf)
                        buf = ''
                    continue

        buf += char
    call_list.append(buf)

    if in_brackets:
        raise errors.UdebsSyntaxError(f"Brackets are mismatched. '{raw}'")

    if '' in call_list:
        raise errors.UdebsSyntaxError(f"Empty element in call_list. '{raw}'")

    # Length one special cases.
    if len(call_list) == 1:
        value = call_list[0]

        # Prefix calling.
        if value not in Variables.modules:
            if value[0] in Variables.modules:
                return [value[0], value[1:]]

    return call_list


def interpret(string, debug=False, root=False):
    """Recursive function that parses callString"""
    try:
        _list = split_callstring(string)
        if debug:
            print("Interpret:", string)
            print("Split:", _list)

        found = []
        for entry in _list:
            if entry[0] == "(" and entry[-1] == ")":
                found.append(interpret(entry[1:-1], debug))
            elif "." in entry:
                found.append(interpret(entry, debug))
            elif entry[0] in Variables.modules and entry not in Variables.modules:
                found.append(interpret(entry, debug))
            else:
                found.append(entry)

        comp = call(found, root=root)
        if debug:
            print("call:", _list)
            print("computed:", comp)

        return comp

    except Exception:
        print(string)
        raise


# ---------------------------------------------------
#                Script Main Class                 -
# ---------------------------------------------------
class Script:
    """Storage class for interpreted code ready for the eval function."""
    def __init__(self, effect, debug=False, skip_interpret=False):
        # Raw text given to script.
        self.raw = None if skip_interpret else effect
        self.interpret = effect if skip_interpret else interpret(effect, debug, root=True)
        self.code = compile(self.interpret, '<string>', "eval")

    def __repr__(self):
        return "<Script " + self.raw + ">"

    def __str__(self):
        return self.raw

    def __eq__(self, other):
        if not isinstance(other, Script):
            return False

        return self.raw == other.raw


# ---------------------------------------------------
#                     Runtime                      -
# ---------------------------------------------------
def _register_raw(func, local=None, globs=None, name=None):
    """Use this to register a function without using a decorator.
    func - The function to register
    local - Local call pattern for given function.
    globs - Dictionary of global objects to add to udebs.
    name - Name to give function (defaults to func.__name__)
    """
    if name is None and not hasattr(func, "__name__"):
        raise errors.UdebsSyntaxError("Must set name attribute when registering a class object.")

    f_name = func.__name__ if hasattr(func, "__name__") else name
    title = name if name is not None else f_name

    if local is None:
        local = {}
    elif isinstance(local, list):
        local = {"args": local}

    local_vars = {
        title: {
            "f": f_name,
            **local,
        }
    }

    if globs is None:
        globs = {}

    globs[f_name] = func() if inspect.isclass(func) else func

    Variables.modules.update(local_vars)
    Variables.env.update(globs)
    return func


def register(function, *args, name=None):
    """Register a function with udebs using a decorator.

    name - keyword used to signify this function from within udebs.

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
    if hasattr(function, "__call__"):
        return _register_raw(function, *args, name=name)

    return lambda f: _register_raw(f, function, *args, name=name)
