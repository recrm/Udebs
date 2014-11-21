#!/usr/bin/env python3

import sys
import re
import copy
import json
import itertools

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
        return next(itertools.islice(before, int(after), None), 'empty')
    
    def length(list_):
        return len(list(list_))
    
    #This is a rough hack until I can find a better way to do this.
    #I will not hold this to backwards compatabiliy.    
    def filter(iterable, value):
        return [i for i in iterable if i == value]
        
class variables:
    keywords = {
        "filter": {
            "f": "standard.filter",
            "args": ["$1", "$2"],
        },
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
        "testing": {
            "f": "TEST",
#            "default": {"$3": 50},
#            "args": ["-$1", "$1", "$2"],
#            "kwargs": {"none": "$3", "value": "empty", "test": 10},
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
    variables.keywords.update(dicts)
    variables.env.update(globs)

def getEnv(local, glob=False):
    value = copy.copy(variables.env)
    if glob:
        value.update(glob)
    value["storage"] = local
    return value

def formatS(string, debug):
    string = str(string)
    if string.isdigit():
        return string
    elif string[0] == "'":
        return string
    elif string[-1] == ")":
        return string
    elif string in variables.env:
        return string
    elif "$" in string:
        return interpret(string, debug)
        
    else:
        return "'"+string+"'"

def call(keyword, args, debug=False):
    """Converts string to function call."""
    if debug:
        print("call:", keyword, args)
    
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
        print("warning: unused arguments.", nodes)
        print(args)
#        raise(Exception)
    
    #Insert keyword arguments.
    for key, value in kwargs.items():
        arguments.append(str(key) + "=" + str(value))
        
    if debug:
        print("computed", data["f"] + "(" + ",".join(arguments) + ")")
    return data["f"] + "(" + ",".join(arguments) + ")"

def bracket(string):
    """Finds bracketed substrings in a string and sends them back to recursive."""
    start = string.find("(")
    end = string.find(")") + 1
    if not end:
        raise UdebsSyntaxError(string, "Brackets are mismatched.")
    substr = string[start:end]
    i = 0
    while substr.count("(") != substr.count(")"):
        end = string[end:].find(")") + end + 1
        substr = string[start:end]
        i +=1
        if i > 1000:
            raise UdebsSyntaxError(string, "Brackets are mismatched.")
            
    return start, end

#Processes a string.
def primary(string, debug=False):
    """Processes a string into it's corresponding list.
        
    string - String to process.
    debug - Prints debugging infor if true.
    
    """
    #check for and handle brackets in call string.
    if debug:
        print("checking", string)
    
    if "(" in string:
        start, end = bracket(string)
        
        if string[start-1] in variables.keywords:
            value = primary(string[start-1] + " " + string[start:end], debug)
            start -=1
        else:
            value = primary(string[start+1:end-1], debug)
        
        list_ = primary(string[:start], debug)
        list_.append(value)
        list_.extend(primary(string[end:], debug))
    else:
        list_ = re.split("\s+", string)
    
    while "" in list_:
        list_.remove("")
        
    for index in range(len(list_)):
        substring = list_[index]
        if isinstance(substring, list):
            continue
        
        #prefix lists
        elif substring[0] in variables.keywords and len(substring) > 1 and substring not in variables.keywords:
            list_[index] = [substring[0], substring[1:]]
    
    return list_

def secondary(list_, debug):
    """This function converts the structured list back into a string.
    
    """
    args = []
    keyword = None
    
    if debug:
        print("secondary", list_)
    
    for element in list_:
        if isinstance(element, list):
            args.append(secondary(element, debug))
            continue
        
        if element in variables.keywords:
            keyword = element
            
        args.append(element)
        
    #if no keyword, return tuple.
    if not keyword:
        value = "("
        for i in args:
            value +=formatS(i, debug)+","
        return value[:-1] + ")"
        
    #This is a function.
    return call(keyword, args, debug)

class UdebsSyntaxError(Exception):
    def __init__(self, entity, string):
        self.message = "'" + entity+"'" + " " + string
    def __str__(self):
        return repr(self.message)

def interpret(string, debug=False):
    if debug:
        print("Interpret:", string)

    #One time bracket replacements.
    string.replace("[", "(")
    string.replace("{", "(")
    string.replace("]", ")")
    string.replace("}", ")")
    
    #One time dot notation replacement.
    list_ = re.split("\s+", string)
    for index in range(len(list_)):
        i = list_[index]
        if "." in i:
            #I know this is illogical and confusing, but it just happened.
            if i[0] in variables.keywords:
                list_[index] = i[0] + "("+i[1:].replace(".", " ")+")"
            else:
                list_[index] = "("+i.replace(".", " ")+")"
                
    string = " ".join(list_)
    
    try:
        if debug:
            print("Bracket form:", string, "\n")
            
        list_ = primary(string, debug)
        if debug:
            print("List form:", list_, "\n")
        
        callstring = secondary(list_, debug)
        if debug:
            print("Final form:", callstring)
    except:
        print(string)
        raise
        
    return callstring


if __name__ == "__main__":
    with open("keywords.json") as fp:
        importModule(json.load(fp), {'self': None})
    interpret(sys.argv[1], debug=True)

