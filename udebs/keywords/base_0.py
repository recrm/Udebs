true = True
false = False

data = {
    "SUB": {
        "f": "standard.sub",
        "args": ["-$1", "$1"]
    },
    "in": {
        "f": "standard.inside",
        "args": ["-$1", "$1"]
    },
    "not-in": {
        "f": "standard.notin",
        "args": ["-$1", "$1"]
    },
    "if": {
        "f": "standard.logicif",
        "args": ["$1", "$2", "$3"],
        "default": {"$2": true, "$3": false}
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
        "args": ["-$1", "$1"]
    },
    ">": {
        "f": "standard.gt",
        "args": ["-$1", "$1"]
    },
    "<": {
        "f": "standard.lt",
        "args": ["-$1", "$1"]
    },
    ">=": {
        "f": "standard.gtequal",
        "args": ["-$1", "$1"]
    },
    "<=": {
        "f": "standard.ltequal",
        "args": ["-$1", "$1"]
    },
    "%": {
        "f": "standard.mod",
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
    "or": {
        "f": "standard.logicor",
        "all": true
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
        "args": ["$1"]
    },
    "-": {
        "f": "standard.minus",
        "args": ["-$1", "$1"],
        "default": {"-$1": 0}
    },
    "=": {
        "f": "standard.setvar",
        "args": ["storage", "-$1", "$1"]
    },
    "$": {
        "f": "standard.getvar",
        "args": ["storage","$1"]
    },
    "print": {
        "f": "standard.print",
        "all": true
    },
    "length": {
        "f": "standard.length",
        "args": ["$1"]
    },
    "`": {
        "f": "standard.quote",
        "args": ["$1"],
        "string": ["$1"]
    }
}
