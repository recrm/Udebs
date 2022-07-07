true = True
false = False

data = {
    "GETS": {
        "f": "self.controlListAdd",
        "args": ["-$2", "-$1", "$1"],
        "default": {"-$2": "$caster"}
    },
    "LOSES": {
        "f": "self.controlListRemove",
        "args": ["-$2", "-$1", "$1"],
        "default": {"-$2": "$caster"}
    },
    "CLEAR": {
        "f": "self.controlClear",
        "args": ["-$1", "$1"],
        "default": {"-$1": "$caster"}
    },
    "CHANGE": {
        "f": "self.controlIncrement",
        "args": ["-$2", "-$1", "$1"],
        "default": {"-$2": "$caster"}
    },
    "EXIT": {
        "f": "self.exit",
        "args": ["$1"],
        "default": {"$1": 1}
    },
    "+=": {
        "f": "self.controlIncrement",
        "args": ["-$2", "-$1", "$1"]
    },
    "-=": {
        "f": "self.controlIncrement",
        "args": ["-$2", "-$1", "$1", -1]
    },

    "REPLACE": {
        "f": "self.controlString",
        "args": ["-$2", "-$1", "$1"],
        "default": {"-$2": "$caster"}
    },
    "RECRUIT": {
        "f": "self.controlRecruit",
        "args": ["-$1", "$1"],
        "default": {"-$1": "$caster", "$1": "#empty"}
    },
    "DELETE": {
        "f": "self.controlDelete",
        "args": ["-$1"]
    },
    "MOVE": {
        "f": "self.controlTravel",
        "args": ["-$1", "$1"],
        "default": {"-$1": "$caster"}
    },
    "CAST": {
        "f": "self._controlMove",
        "args": ["-$1", "$1", "$2"],
        "default": {"-$1": "$caster"}
    },
    "INIT": {
        "f": "self._controlMove",
        "args": ["#empty", "#empty", "$1"]
    },
    "ACTION": {
        "f": "self._controlMove",
        "args": ["-$1", "#empty", "$1"]
    },
    "OR": {
        "f": "self.controlOr",
        "kwargs": {"storage":  "storage"},
        "all": true
    },
    "AND": {
        "f": "self.controlAnd",
        "kwargs": {"storage":  "storage"},
        "all": true
    },
    "REPEAT": {
        "f": "self.controlRepeat",
        "args": ["$1", "$2", "storage"]
    },
    "DELAY": {
        "f": "self.controlDelay",
        "args": ["$1", "$2", "storage"]
    },
    "TIME": {
        "f": "self.controlTime",
        "args": ["$1"],
        "default": {"$1": 0}
    },
    "STAT": {
        "f": "self.getStat",
        "args": ["-$1", "$1"],
        "default": {"-$1": "$caster"}
    },
    "VAR": {
        "f": "self.getVar",
        "args": ["$1"]
    },
    "CLASS": {
        "f": "self.getListGroup",
        "args": ["-$1", "group", "$1"],
        "default": {"-$1": "$caster"}
    },
    "LISTSTAT": {
        "f": "self.getListStat",
        "args": ["-$2", "-$1", "$1"],
        "default": {"-$2": "$caster"}
    },
    "LISTGROUP": {
        "f": "self.getListGroup",
        "args": ["-$2", "-$1", "$1"],
        "default": {"-$1": "$caster"}
    },
    "XLOC": {
        "f": "self.getLocData",
        "args": ["-$1"],
        "default": {"-$1": "$caster"}
    },
    "YLOC": {
        "f": "self.getLocData",
        "args": ["-$1", 1],
        "default": {"-$1": "$caster"}
    },
    "MAPNAME": {
        "f": "self.getLocData",
        "args": ["-$1", 2],
        "default": {"-$1": "$caster"}
    },
    "LOC": {
        "f": "self.getLocObject",
        "args": ["-$1"],
        "default": {"-$1": "$caster"}
    },
    "SHIFT": {
        "f": "self.getShift",
        "args": ["-$1", "$1", "$2", "$3"],
        "default": {"-$1": "$caster", "$3": "None"}
    },
    "NAME": {
        "f": "self.getName",
        "args": ["-$1"],
        "default": {"-$1": "$caster"}
    },
    "#": {
        "f": "self.getEntity",
        "args": ["$1"]
    },
    "SHUFFLE": {
        "f": "self.controlShuffle",
        "args": ["-$1", "$1"]
    },
    "DICE": {
        "f": "self.rand.randint",
        "args": [0, "$1"]
    },
    "ALL": {
        "f": "self.getGroup",
        "all": true
    },
    "SEARCH": {
        "f": "self.getSearch",
        "all": true
    },
    "FILL": {
        "f": "self.getFill",
        "args": ["$1", "$2", "$3", "$4"],
        "default": {"$2": "#empty", "$3": true, "$4": None}
    },
    "PATH": {
        "f": "self.getPath",
        "args": ["$2", "$3", "$1"],
        "default": {"$2": "$caster", "$3": "$target"}
    },
    "DISTANCE": {
        "f": "self.getDistance",
        "args": ["$2", "$3", "$1"],
        "default": {"$2": "$caster", "$3": "$target"}
    },
    "BLOCK": {
        "f": "self.testBlock",
        "args": ["$2", "$3", "$1"],
        "default": {"$2": "$caster", "$3": "$target"},
        "kwargs": {"max_dist": "-$1"}
    },
    "FUTURE": {
        "f": "self.testFuture",
        "args": ["$caster", "$target", "$move", "$1", "$2"],
        "default": {"$2": 0}
    },
    "MAP": {
        "f": "self.getMap",
        "args": ["-$1"],
        "default": {"-$1": "$caster"}
    },
    "`": {
        "f": "self.getQuote",
        "args": ["$1"],
        "string": ["$1"]
    }
}
