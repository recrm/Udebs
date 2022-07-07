from udebs import errors

class operator:
    @staticmethod
    def gt(one, two):
        return one > two

    @staticmethod
    def lt(one, two):
        return one < two

    @staticmethod
    def ge(one, two):
        return one >= two

    @staticmethod
    def le(one, two):
        return one <= two

    @staticmethod
    def mod(one, two):
        return one % two

    @staticmethod
    def truediv(one, two):
        return one / two

    @staticmethod
    def not_(one):
        return not one

    @staticmethod
    def sub(one, two):
        return one - two


# ---------------------------------------------------
#            Imports and Variables                  -
# ---------------------------------------------------
class Standard:
    """
    Basic functionality wrappers.

    Do not import any of these, included only as reference for udebs config file syntax.
    """

    @staticmethod
    def print(*args):
        """
        prints extra output to console.

        .. code-block:: xml

            <i>print arg1 arg2 ...</i>
        """
        print(*args)
        return True

    @staticmethod
    def logicif(cond, value, other):
        """
        returns value if condition else other.

        (Note, this function evaluates all conditions regardless of if condition.)
        (Deprecated in version 1.1.0 in favor of AND, OR blocks.)

        .. code-block:: xml

            <i>if cond value other</i>
        """
        return value if cond else other

    @staticmethod
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

    @staticmethod
    def notin(*args, **kwargs):
        """
        Returns false if value in obj else true.

        .. code-block:: xml

            <i>value not-in obj</i>
        """
        return not Standard.inside(*args, **kwargs)

    @staticmethod
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

    @staticmethod
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

    @staticmethod
    def gt(before, after):
        """Checks if before is greater than after

        .. code-block:: xml

            <i>before &gt; after</i>
        """
        return before > after

    @staticmethod
    def lt(before, after):
        """Checks if before is less than after

        .. code-block:: xml

            <i>before &lt; after</i>
        """
        return before < after

    @staticmethod
    def gtequal(before, after):
        """Checks if before is greater than or equal to after

        .. code-block:: xml

            <i>before &gt;= after</i>
        """
        return before >= after

    @staticmethod
    def ltequal(before, after):
        """Checks if before is less than or equal to after

        .. code-block:: xml

            <i>before &lt;= after</i>
        """
        return before <= after

    @staticmethod
    def plus(*args):
        """Sums arguments

        .. code-block:: xml

            <i>arg1 + arg2</i>
            <i>+ arg1 arg2 ...</i>
        """
        return sum(args)

    @staticmethod
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

    @staticmethod
    def mod(before, after):
        """Returns before mod after.

        .. code-block:: xml

            <i>before % after</i>
        """
        return before % after

    @staticmethod
    def setvar(storage, variable, value):
        """Stores value inside of variable.

        Note: always returns true so can be used in require block.

        .. code-block:: xml

            <i>variable = value</i>
            <i>variable -> value</i>
        """
        storage[variable] = value
        return True

    @staticmethod
    def getvar(storage, variable):
        """Retrieves a variable

        .. code-block:: xml

            <i>$ variable</i>
            <i>$variable</i>
        """
        return storage[variable]

    @staticmethod
    def div(before, after):
        """Returns before divided by after.

        .. code-block:: xml

            <i>before / after</i>
        """
        return before / after

    @staticmethod
    def logicnot(element):
        """Switches a boolean from true to false and vice versa

        .. code-block:: xml

            <i>! element</i>
            <i>!element</i>
        """
        return not element

    @staticmethod
    def minus(before, element):
        """Returns before - element. (before defaults to 0 if not given)

        .. code-block:: xml

            <i>before - element</i>
            <i>-element</i>
        """
        return before - element

    @staticmethod
    def sub(array, i):
        """Gets the ith element of array.

        .. code-block:: xml

            <i>array sub i</i>
        """
        try:
            return array[i]
        except IndexError:
            return "empty"

    @staticmethod
    def length(list_):
        """Returns the length of an iterable.

        .. code-block:: xml

            <i>length list_</i>
        """
        return len(list(list_))


class Variables:
    versions = [0, 1]
    modules = {
        -1: {},
    }
    env = {
        "__builtins__": {"abs": abs, "min": min, "max": max, "len": len},
        "standard": Standard,
        "operator": operator,
        "storage": None,
    }
    default = {
        "f": "",
        "args": [],
        "kwargs": {},
        "all": False,
        "default": {},
        "string": [],
    }

    @staticmethod
    def keywords(version=1):
        return dict(Variables.modules[version], **Variables.modules[-1])


def importFunction(f, args):
    """
    Allows a user to import a single function into udebs.

    **deprecated - please use udebs.utilities.register
    """

    module = {
        f.__name__: {
            "f": f.__name__
        }
    }

    module[f.__name__].update(args)
    importModule(module, {f.__name__: f})


def importModule(dicts=None, globs=None, version=-1):
    """
    Allows user to extend base variables available to the interpreter.
    Should be run before the instance object is created.

    **deprecated for users - please use udebs.utilities.register
    """
    if globs is None:
        globs = {}
    if dicts is None:
        dicts = {}
    if version not in Variables.modules:
        Variables.modules[version] = {}

    Variables.modules[version].update(dicts)
    Variables.env.update(globs)


"""This whole function needs to be rewritten"""


def importSystemModule(name, globs=None):
    """Convenience script for import system keywords."""
    if globs is None:
        globs = {}

    from udebs import keywords

    for version in Variables.versions:
        module_name = f"{name}_{str(version)}"
        importModule(getattr(keywords, module_name).data, globs, version)


def getEnv(local, glob=None):
    """Retrieves a copy of the base variables."""
    new_env = {}
    new_env.update(Variables.env)
    if glob:
        new_env.update(glob)
    new_env["storage"] = local
    return new_env


# ---------------------------------------------------
#            Interpreter Functions                 -
# ---------------------------------------------------
def formatS(string, version):
    """Converts a string into its python representation."""
    string = str(string)
    if string == "self":
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
    elif string[0] in Variables.keywords(version):
        return interpret(string, version)
    else:
        return "'" + string + "'"


def call(args, version):
    """Converts callList into functionString."""
    # Find keyword
    keywords = [i for i in args if i in Variables.keywords(version)]

    # Too many keywords is a syntax error.
    if len(keywords) > 1:
        raise errors.UdebsSyntaxError("CallList contains to many keywords '{}'".format(args))

    # No keywords create a tuple object.
    elif len(keywords) == 0:
        return "(" + ",".join(formatS(i, version) for i in args) + ")"

    keyword = keywords[0]

    # Get and fix data for this keyword.
    data = {}
    data.update(Variables.default)
    data.update(Variables.keywords(version)[keyword])

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
        kwargs[key] = formatS(new_value, version)

    arguments = []
    # Insert positional arguments
    for key in data["args"]:
        if key in nodes:
            arguments.append(formatS(nodes[key], version))
            del nodes[key]
        else:
            arguments.append(formatS(key, version))

    # Insert ... arguments.
    if data["all"]:
        for key in sorted(nodes.keys(), key=lambda x: int(x.replace("$", ""))):
            arguments.append(formatS(nodes[key], version))
            del nodes[key]

    if len(nodes) > 0:
        raise errors.UdebsSyntaxError("Keyword contains unused arguments. '{}'".format(" ".join(args)))

    # Insert keyword arguments.
    for key in sorted(kwargs.keys()):
        arguments.append(str(key) + "=" + str(kwargs[key]))

    return data["f"] + "(" + ",".join(arguments) + ")"


def split_callstring(raw, version):
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
        raise errors.UdebsSyntaxError("Brackets are mismatched. '{}'".format(raw))

    if '' in call_list:
        raise errors.UdebsSyntaxError("Empty element in call_list. '{}'".format(raw))

    # Length one special cases.
    if len(call_list) == 1:
        value = call_list[0]

        # Prefix calling.
        if value not in Variables.keywords(version):
            if value[0] in Variables.keywords(version):
                return [value[0], value[1:]]

    return call_list


def interpret(string, version=1, debug=False):
    """Recursive function that parses callString"""
    try:
        _list = split_callstring(string, version)
        if debug:
            print("Interpret:", string)
            print("Split:", _list)

        found = []
        for entry in _list:
            if entry[0] == "(" and entry[-1] == ")":
                found.append(interpret(entry[1:-1], version, debug))
            elif "." in entry:
                found.append(interpret(entry, version, debug))
            elif entry[0] in Variables.keywords(version) and entry not in Variables.keywords(version):
                found.append(interpret(entry, version, debug))
            else:
                found.append(entry)

        comp = call(found, version)
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

    def __init__(self, effect, version=1, debug=False, skip_interpret=False):
        # Raw text given to script.
        self.raw = effect
        self.interpret = effect if skip_interpret else interpret(effect, version, debug)
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
importSystemModule("base")
importSystemModule("udebs")
