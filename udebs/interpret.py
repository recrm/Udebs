import copy
import json
import itertools
import os

#---------------------------------------------------
#            Imports and Variables                 -
#---------------------------------------------------

class standard:
    """
    Basic functionality built into the Udebs scripting language.
    None of the functions here can depend on any other Udebs module.
    """
    def _print(*args):
        print(*args)
        return True

    def logicif(cond, value, other):
        return value if cond else other

    def inside(before, after, amount=1):
        if isinstance(after, str):
            return before in after

        if amount == 0:
            return True

        count = 0
        for item in after:
            if item == before:
                count +=1
                if count >= amount:
                    return True

        return False

    def notin(*args, **kwargs):
        return not standard.inside(*args, **kwargs)

    def equal(*args):
        x = args[0]
        for y in args:
            if y != x:
                return False
        return True

    def notequal(*args):
        x = args[0]
        for y in args[1:]:
            if x == y:
                return False
        return True

    def gt(before, after):
        return before > after

    def lt(before, after):
        return before < after

    def gtequal(before, after):
        return before >= after

    def ltequal(before, after):
        return before <= after

    def plus(*args):
        return sum(args)

    def multiply(*args):
        i = 1
        for number in args:
            i *= number
        return i

    def logicor(*args, storage=None, field=None):
        env = _getEnv(storage, {"self": field})
        for i in args:
            if isinstance(i, UdebsStr):
                i = field.getEntity(i).testRequire(env)
            if i:
                return True
        return False

    def mod(before, after):
        return before % after

    def setvar(storage, variable, value):
        storage[variable] = value
        return True

    #prefix functions
    def getvar(storage, variable):
        return storage[variable]

    def div(before, after):
        return before/after

    def logicnot(element):
        return not element

    def minus(before, element):
        return before - element

    def sub(before, after):
        return next(itertools.islice(before, int(after), None), 'empty')

    def length(list_):
        return len(list(list_))

    def quote(string):
        return UdebsStr(string)

class variables:
    modules = {
        0: {},
        1: {},
        "other": {},
    }
    env = {
        "__builtins__": {"abs": abs, "min": min, "max": max},
        "standard": standard,
        "storage": {},
    }
    default = {
        "f": "",
        "args": [],
        "kwargs": {},
        "all": False,
        "default": {},
         "string": [],
    }

    def keywords(version=1):
        return dict(variables.modules[version], **variables.modules["other"])

def importFunction(f, args):
    module = {
        f.__name__: {
            "f": f.__name__
        }
    }

    module[f.__name__].update(args)
    importModule(module, {f.__name__: f})

def importModule(dicts={}, globs={}, version="other"):
    """
    Allows user to extend base variables available to the interpreter.
    Should be run before the instance object is created.
    """
    variables.modules[version].update(dicts)
    variables.env.update(globs)

def importSystemModule(name, globs={}):
    """Convenience script for import system keywords."""
    versions = [0,1]
    path = os.path.dirname(__file__)
    for version in versions:
        filename = "{}/keywords/{}-{}.json".format(path, name, str(version))
        with open(filename) as fp:
            importModule(json.load(fp), globs, version)

def _getEnv(local, glob=False):
    """Retrieves a copy of the base variables."""
    value = copy.copy(variables.env)
    if glob:
        value.update(glob)
    value["storage"] = local
    return value

#---------------------------------------------------
#            Interpreter Functions                 -
#---------------------------------------------------
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
    #String quoted by user.
    elif string[0] == string[-1] and string[0] in {"'", '"'}:
        return string
    #String has already been handled by call
    elif string[-1] == ")":
        return string
    elif string in variables.env:
        return string
    #In case prefix notation used in keyword defaults.
    elif string[0] in variables.keywords(version):
        return interpret(string, version)
    else:
        return "'"+string+"'"

def call(args, version):
    """Converts callList into functionString."""
    #Find keyword
    keywords = [i for i in args if i in variables.keywords(version)]

    #Too many keywords is a syntax error.
    if len(keywords) > 1:
        raise UdebsSyntaxError("CallList contains to many keywords '{}'".format(args))

    #No keywords creates a tuple object.
    elif len(keywords) == 0:
        return "(" + ",".join(formatS(i,version) for i in args) + ")"

    keyword = keywords[0]

    #Get and fix data for this keyword.
    data = copy.copy(variables.default)
    data.update(variables.keywords(version)[keyword])

    #Create dict of values
    current = args.index(keyword)
    nodes = copy.copy(data["default"])

    for index in range(len(args)):
        value = "$" if index >= current else "-$"
        value += str(abs(index - current))
        if args[index] != keyword:
            nodes[value] = args[index]

    #Force strings into quoted arguments.
    for string in data["string"]:
        nodes[string] = "'"+str(nodes[string]).replace("'", "\\'")+"'"

    #Claim keyword arguments.
    kwargs = {}
    for key, value in data["kwargs"].items():
        if value in nodes:
            newvalue = nodes[value]
            del nodes[value]
        else:
            newvalue = value
        kwargs[key] = formatS(newvalue, version)

    arguments = []
    #Insert positional arguments
    for key in data["args"]:
        if key in nodes:
            arguments.append(formatS(nodes[key], version))
            del nodes[key]
        else:
            arguments.append(formatS(key, version))

    #Insert ... arguments.
    if data["all"]:
        for key in sorted(nodes.keys(), key=lambda x: int(x.replace("$", ""))):
            arguments.append(formatS(nodes[key], version))
            del nodes[key]

    if len(nodes) > 0:
        raise UdebsSyntaxError("Keyword contains unused arguments. '{}'".format(" ".join(args)))

    #Insert keyword arguments.
    for key in sorted(kwargs.keys()):
        arguments.append(str(key) + "=" + str(kwargs[key]))

    return data["f"] + "(" + ",".join(arguments) + ")"

def split_callstring(raw, version):
    """Converts callString into callList."""
    openBracket = {'(', '{', '['}
    closeBracket = {')', '}', ']'}
    callList = []
    buf = ''
    inBrackets = 0
    inQuotes = False
    dotLegal = True

    for char in raw.strip():

        if char in {'"', "'"}:
            inQuotes = not inQuotes

        elif not inQuotes:
            if char in openBracket:
                inBrackets +=1

            elif char in closeBracket:
                inBrackets -=1

            elif not inBrackets:
                if dotLegal:
                    if char == ".":
                        callList.append(buf)
                        buf = ''
                        continue

                    elif char.isspace():
                        dotLegal = False
                        if callList:
                            callList = [".".join(callList) + "." + buf]
                            buf = ''

                if char.isspace():
                    if buf:
                        callList.append(buf)
                        buf = ''
                    continue

        buf += char
    callList.append(buf)

    if inBrackets:
        raise UdebsSyntaxError("Brackets are mismatched. '{}'".format(raw))

    if '' in callList:
        raise UdebsSyntaxError("Empty element in callList. '{}'".format(raw))

    #Length one special cases.
    if len(callList) == 1:
        value = callList[0]

        #Prefix calling.
        if value not in variables.keywords(version):
            if value[0] in variables.keywords(version):
                return [value[0], value[1:]]

    return callList

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
            elif entry[0] in variables.keywords(version) and entry not in variables.keywords(version):
                found.append(interpret(entry, version, debug))
            else:
                found.append(entry)

        comp = call(found, version)
        if debug:
            print("call:", _list)
            print("computed:", comp)

        return UdebsStr(comp)

    except:
        print(string)
        raise

#---------------------------------------------------
#                Script Main Class                 -
#---------------------------------------------------
#An easy way to distinguish between interpreted strings.
class UdebsStr(str):
    pass

class Script:
    def __init__(self, effect, version=1, debug=False):
        #Raw text given to script.
        self.raw = effect
        self.interpret = effect
        if not isinstance(effect, UdebsStr):
            self.interpret = interpret(effect, version, debug)

        self.code = compile(self.interpret, '<string>', "eval")

    def __repr__(self):
        return "<Script " + self.raw + ">"

    def __str__(self):
        return self.raw

    def __call__(self, env):
        try:
            return eval(self.code, env)
        except Exception:
            raise UdebsExecutionError(self)

    def __eq__(self, other):
        if not isinstance(other, Script):
            return False

        return self.raw == other.raw

#---------------------------------------------------
#                     Errors                       -
#---------------------------------------------------
class UdebsSyntaxError(Exception):
    def __init__(self, string):
        self.message = string
    def __str__(self):
        return repr(self.message)

class UdebsExecutionError(Exception):
    def __init__(self, script):
        self.script = script
    def __str__(self):
        return "invalid '{}'".format(self.script.raw)

#---------------------------------------------------
#                     Runtime                      -
#---------------------------------------------------
importSystemModule("base")
importSystemModule("udebs")
