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
        "all": True
    },
    "max": {
        "f": "max",
        "all": True
    },
    "==": {
        "f": "standard.equal",
        "all": True
    },
    "!=": {
        "f": "standard.notequal",
        "all": True
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
        "all": True
    },
    "*": {
        "f": "standard.multiply",
        "all": True
    },
    "if": {
        "f": "standard.logicif",
        "args": ["$1", "$2", "$3"],
        "default": {"$2": True, "$3": False}
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
        "all": True
    },
    "length": {
        "f": "len",
        "args": ["$1"]
    }
}
