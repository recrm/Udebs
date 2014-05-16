#!/usr/bin/env python3

import sys
import re
import copy
import json

class standard:
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
        i = 0
        for number in args:
            i += number
        return i
        
    def multiply(*args):
        i = 1
        for number in args:
            i *= number
        return i
        
    def logicor(*args):
        return any(args)
        
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
        try:
            return before[int(after)]
        except IndexError:
            return 'empty'

class variables:
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
        "min": {
            "f": "min",
            "all": True,
        },
        "max": {
            "f": "max",
            "all": True,
        },
        "?": {
            "f": "standard.logicif",
            "args": ["$1", "$2", "$3"],
            "default": {"$2": True, "$3": False},
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
            "args": ["-$1", "$1"],
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
            "args": ["storage", "$1"],
        },
        "print": {
            "f": "standard._print",
            "all": True,
        }
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
    if isinstance(dicts, list):
        for dictionary in dicts:
            variables.keywords.update(dictionary)
    else:
        variables.keywords.update(dicts)
        
    if isinstance(globs, list):
        for dictionary in globs:
            variables.env.update(dictionary)
    else:
        variables.env.update(globs)

def getEnv(local, glob=False):
    value = copy.copy(variables.env)
    if glob:
        value.update(glob)
    value["storage"] = local
    return value

def call(expression, debug=False):
    """Converts string to function call."""
    if debug:
        print("call:", expression)
    
    for value in expression:
        if value in variables.keywords:
            keyword = value
            break
    else:
        for i in range(len(expression)):
            expression[i] = s(expression[i], debug)
        return "{"+",".join(expression)+"}"
    
    #Get data for this keyword
    data = copy.copy(variables.default)
    data.update(variables.keywords[keyword])

    #Create dict of values
    current = expression.index(keyword)
    nodes = copy.copy(data["default"])
    for index in range(len(expression)):
        symbol = "$" if index >= current else "-$"
        value = symbol + str(abs(index - current))
        if expression[index] != keyword:
            nodes[value] = expression[index]

    #Force strings into long arguments.
    for string in data["string"]:
        nodes[string] = "'"+nodes[string].replace("'", "\\'")+"'"

    #Insert positional arguments
    function = data["f"]+"{"
    for key in data["args"]:
        if key in nodes:
            function += s(nodes[key], debug)+","
            del nodes[key]
        else:
            function += s(key, debug)+","

    #Claim keyword arguments.
    for key, value in data["kwargs"].items():
        if value in nodes:
            data["kwargs"][key] = nodes[value]
            del nodes[value]        

    #Insert ... arguments.
    if data["all"]:
        for key in sorted(list(nodes.keys())):
            if key != "$0":
                function += s(nodes[key], debug)+","
                del nodes[key]

    if len(nodes) > 0:
        print("warning: unused arguments.", nodes)
    
    #Insert keyword arguments.
    for key, value in data["kwargs"].items():
        function += str(key) + "=" + s(str(value)) +","

    #Remove trailing comma and close argument.
    if function[-1] == ",":
        function = function[:-1]+"}"
    
    return function

def bracket(string, debug):
    """Finds bracketed substrings in a string and sends them back to recursive."""
    start = string.find("(")
    end = string.find(")") + 1
    substr = string[start:end]
    while substr.count("(") != substr.count(")"):
        end = string[end:].find(")") + end + 1
        substr = string[start:end]

    if debug:
        print("entering subshell")
    value = s(string[start+1:end-1], debug)
    if debug:
        print(value)
        print("exiting subshell")            
    return s(string[:start] + value + string[end:], debug)

def s(string, debug):
    """Converts arguments to proper type."""
    if debug:
        print("checking:", string)
    #type is already string or loc.
    if not isinstance(string, str):
        return str(string)
    elif string.isdigit():
        return string
    elif string in variables.env:
        return string
    elif string[0] == "'":
        return string
    
    #bracket calling
    elif "(" in string:
        return bracket(string, debug)
    
    #Normal call technique
    elif " " in string:
        value = re.split("\s+", string)
        return call(value, debug)
    
    #prefix calling
    elif string[0] in variables.keywords and string[1] != ".":
        return call([string[0], string[1:]], debug)
    
    #skip if contains brackets (already been processed).
    elif "{" in string:
        return string

    #dot notation calling technique (cannot contain brackets)
    elif "." in string:
        value = re.split("\.", string)
        return call(value, debug)
    
    return "'"+string+"'"

def interpret(string, debug=False):
    try:
        final = s(string, debug)
    except:
        print(string)
        raise
    final = final.replace("{", "(")
    final = final.replace("}", ")")
    return final

if __name__ == "__main__":
    with open("udebs/keywords.json") as fp:
        importModule(json.load(fp), {'self': None})
    print(interpret(sys.argv[1], debug=True))

