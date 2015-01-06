#!/usr/bin/env python3

import sys
import re
import copy
import json
import itertools

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

    def inside(before, after):
        return before in after

    def notin(before, after):
        return before not in after

    def equal(*args):
        x = args[0]
        for y in args:
            if y != x:
                return False
        return True

    def notequal(before, after):
        return before != after

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

    def logicor(*args):
        return any(args)

    def logicif(cond, value, other):
        return value if cond else other

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

class variables:
    """
    Base environment object that Udebs scripts are interpreted through.
    """
    keywords = {
        "SUB": {
            "f": "standard.sub",
            "args": ["-$1", "$1"],
        },
        "in": {
            "f": "standard.inside",
            "args": ["-$1", "$1"],
        },
        "not-in": {
            "f": "standard.notin",
            "args": ["-$1", "$1"],
        },
        "if": {
            "f": "standard.logicif",
            "args": ["$1", "$2", "$3"],
            "default": {"$2": True, "$3": False},
        },
        "min": {
            "f": "min",
            "all": True,
        },
        "max": {
            "f": "max",
            "all": True,
        },
        "==": {
            "f": "standard.equal",
            "all": True,
        },
        "!=": {
            "f": "standard.notequal",
            "args": ["-$1", "$1"],
        },
        ">": {
            "f": "standard.gt",
            "args": ["-$1", "$1"],
        },
        "<": {
            "f": "standard.lt",
            "args": ["-$1", "$1"],
        },
        ">=": {
            "f": "standard.gtequal",
            "args": ["-$1", "$1"],
        },
        "<=": {
            "f": "standard.ltequal",
            "args": ["-$1", "$1"],
        },
        "%": {
            "f": "standard.mod",
            "args": ["-$1", "$1"],
        },
        "+": {
            "f": "standard.plus",
            "all": True,
        },
        "*": {
            "f": "standard.multiply",
            "all": True,
        },
        "or": {
            "f": "standard.logicor",
            "all": True,
        },
        "|": {
            "f": "abs",
            "args": ["$1"]
        },
        "/": {
            "f": "standard.div",
            "args": ["-$1", "$1"],
            "default": {"-$1": 1}
        },
        "!": {
            "f": "standard.logicnot",
            "args": ["$1"],
        },
        "-": {
            "f": "standard.minus",
            "args": ["-$1", "$1"],
            "default": {"-$1": 0}
        },
        "=": {
            "f": "standard.setvar",
            "args": ["storage", "-$1", "$1"],
        },
        "$": {
            "f": "standard.getvar",
            "args": ["storage","$1"],
        },
        "print": {
            "f": "standard._print",
            "all": True,
        },
        "length": {
            "f": "standard.length",
            "args": ["$1"],
        },
    }
    env = {"__builtin__": None, "standard": standard, "storage": {}, "abs": abs, "min": min, "max": max}
    default = {
        "f": "",
        "args": [],
        "kwargs": {},
        "all": False,
        "default": {},
        "string": [],
    }


def importModule(dicts={}, globs={}):
    """
    Allows user to extend base variables available to the interpreter.
    Should be run before the instance object is created.
    """
    variables.keywords.update(dicts)
    variables.env.update(globs)

def _getEnv(local, glob=False):
    """Retrieves a copy of the base variables."""
    value = copy.copy(variables.env)
    if glob:
        value.update(glob)
    value["storage"] = local
    return value

class UdebsSyntaxError(Exception):
    def __init__(self, string):
        self.message = string
    def __str__(self):
        return repr(self.message)

class UdebsParserError(Exception):
    def __init__(self, string):
        self.message = string
    def __str__(self):
        return repr(self.message)

def formatS(string, debug):
    """Converts a string into its python representation."""
    string = str(string)
    if string.isdigit():
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
    elif string[0] in variables.keywords:
        return interpret(string, debug)
    else:
        return "'"+string+"'"

def call(args, debug=False):
    """Converts callList into functionString."""
    if not isinstance(args, list):
        raise UdebsParserError("There is a bug in the parser, call recived '{}'".format(args))

    if debug:
        print("call:", args)

    #Find keyword
    keywords = [i for i in args if i in variables.keywords]

    #If there are too many keywords, some might stand alone.
    if len(keywords) > 1:
        for key in keywords[:]:
            values = variables.keywords[key]
            arguments = sum(len(values.get(i, [])) for i in ["args", "kwargs", "default"])
            if arguments == 0 and not values.get("all", False):
                new = call([key])
                args[args.index(key)] = new
                keywords.remove(key)

    #Still to many keywords is a syntax error.
    if len(keywords) > 1:
        raise UdebsSyntaxError("CallList contains to many keywords '{}'".format(args))

    #No keywords creates a tuple object.
    elif len(keywords) == 0:
        value = "("
        for i in args:
            value +=formatS(i, debug)+","
        computed = value[:-1] + ")"
        if debug:
            print("computed:", computed)
        return computed

    keyword = keywords[0]

    #Get and fix data for this keyword.
    data = copy.copy(variables.default)
    data.update(variables.keywords[keyword])

    #Create dict of values
    current = args.index(keyword)
    nodes = copy.copy(data["default"])

    for index in range(len(args)):
        value = "$" if index >= current else "-$"
        value += str(abs(index - current))
        if args[index] != keyword:
            nodes[value] = args[index]

    #Force strings into long arguments.
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
        kwargs[key] = formatS(newvalue, debug)

    arguments = []
    #Insert positional arguments
    for key in data["args"]:
        if key in nodes:
            arguments.append(formatS(nodes[key], debug))
            del nodes[key]
        else:
            arguments.append(formatS(key, debug))

    #Insert ... arguments.
    if data["all"]:
        for key in sorted(list(nodes.keys())):
            arguments.append(formatS(nodes[key], debug))
            del nodes[key]

    if len(nodes) > 0:
        raise UdebsSyntaxError("Keyword contains unused arguments. '{}'".format(args))

    #Insert keyword arguments.
    for key in sorted(kwargs.keys()):
        arguments.append(str(key) + "=" + str(kwargs[key]))

    computed = data["f"] + "(" + ",".join(arguments) + ")"
    if debug:
        print("computed:", computed)
    return computed

def split_callstring(raw):
    """Converts callString into callList."""
    openBracket = {'(', '{', '['}
    closeBracket = {')', '}', ']'}
    string = raw.strip()
    callList = []
    buf = ''
    inBrackets = 0
    dotLegal = True

    for char in string:
        #Ignore everything until matching bracket is found.
        if inBrackets:
            if char in openBracket:
                inBrackets +=1
            elif char in closeBracket:
                inBrackets -=1
            buf += char
            continue

        #Normal whitespace split`
        elif char.isspace():
            if dotLegal:
                dotLegal = False
                if callList:
                    buf = ".".join(callList)+"."+buf
                    callList = []
            if buf:
                callList.append(buf)
                buf = ''
            continue

        #Dot split
        elif dotLegal and char == ".":
            callList.append(buf)
            buf = ''
            continue

        #Found opening Bracket
        if char in openBracket:
            if len(buf) > 1:
                raise UdebsSyntaxError("Too many bits before bracket. '{}'".format(raw))
            inBrackets +=1

        #Everything else
        buf += char

    callList.append(buf)

    if inBrackets:
        raise UdebsSyntaxError("Brackets are mismatched. '{}'".format(raw))

    if '' in callList:
        raise UdebsSyntaxError("Empty element in callList. '{}'".format(raw))

    #Length one special cases.
    if len(callList) == 1:
        value = callList[0]

        #unnecessary brackets. (Future fix: deal with this at start of function as these are common.)
        if value[0] in openBracket and value[-1] in closeBracket:
            return split_callstring(value[1:-1])

        #Prefix calling.
        if value not in variables.keywords:
            if value[0] in variables.keywords:
                return [value[0], value[1:]]

    return callList

def interpret(string, debug=False, first=True):
    """Recursive function that parses callString"""
    #Small hack for solitary keywords
    if first and string in variables.keywords:
        return call([string])

    _list = split_callstring(string)
    #Exit condition
    if len(_list) == 1:
        return _list[0]

    if debug:
        print("Interpret:", string)

    _list = [interpret(i, debug, False) for i in _list]
    return call(_list, debug)

if __name__ == "__main__":
    with open("keywords.json") as fp:
        importModule(json.load(fp), {'self': None})
    interpret(sys.argv[1], debug=True)
