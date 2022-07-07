true = True
false = False

data = {
    "elem": {
        "f": "standard.sub",
        "args": ["-$1", "$1"]
    },
    "in": {
        "f": "standard.inside",
        "args": ["-$1", "$1", "$2"],
         "default": {"$2": 1}
    },
    "not-in": {
        "f": "standard.notin",
        "args": ["-$1", "$1", "$2"],
        "default": {"$2": 1}
    },
    "min": {
        "f": "min",
        "all": true
    },
    "max": {
        "f": "max",
        "all": true
    },
    "==": {
        "f": "standard.equal",
        "all": true
    },
    "!=": {
        "f": "standard.notequal",
        "all": true
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
    "+": {
        "f": "standard.plus",
        "all": true
    },
    "*": {
        "f": "standard.multiply",
        "all": true
    },
    "if": {
        "f": "standard.logicif",
        "args": ["$1", "$2", "$3"],
        "default": {"$2": true, "$3": false}
    },
    "|": {
        "f": "abs",
        "args": ["$1"]
    },
    "/": {
        "f": "operator.truediv",
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
    "->": {
        "f": "standard.setvar",
        "args": ["storage", "-$1", "$1"]
    },
    "=": {
        "f": "standard.setvar",
        "args": ["storage", "-$1", "$1"]
    },
    "$": {
        "f": "storage.__getitem__",
        "args": ["$1"]
    },
    "print": {
        "f": "standard.print",
        "all": true
    },
    "length": {
        "f": "len",
        "args": ["$1"]
    }
}
