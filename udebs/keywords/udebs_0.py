true = True
false = False

data = {
    "TIME": {
        "f": "self.controlTime",
        "args": ["$1"]
    },
    "INIT": {
        "f": "self.castInit",
        "args": ["$1"]
    },
    "CAST": {
        "f": "self._controlMove",
        "args": ["-$1", "$1", "$2"],
        "default": {"-$1": "$caster"}
    },
    "DELAY": {
        "f": "self.controlDelay",
        "args": ["$1", "$2", "storage"]
    },
    "GETS": {
        "f": "self.controlListAdd",
        "args": ["$1", "$2", "$3"]
    },
    "LOSES": {
        "f": "self.controlListRemove",
        "args": ["$1", "$2", "$3"]
    },
    "CLEAR": {
        "f": "self.controlClear",
        "args": ["$1", "$2"]
    },
    "CHANGE": {
        "f": "self.controlIncrement",
        "args": ["$1", "$2", "$3"]
    },
    "REPLACE": {
        "f": "self.controlString",
        "args": ["$1", "$2", "$3"]
    },
    "RECRUIT": {
        "f": "self.controlRecruit",
        "args": ["$1", "$2"]
    },
    "DELETE": {
        "f": "self.controlDelete",
        "args": ["$1"]
    },
    "MOVE": {
        "f": "self.controlTravel",
        "args": ["$1", "$2"]
    },
    "TRAVEL": {
        "f": "self.controlTravel",
        "args": ["-$1", "$1"],
        "default": {"-$1": "$caster"}
    },
    "CLASS": {
        "f": "self.getListGroup",
        "args": ["$1", "group", "$2"]
    },
    "LISTGROUP": {
        "f": "self.getListGroup",
        "args": ["$1", "$2", "$3"]
    },
    "ALL": {
        "f": "self.getGroup",
        "args": ["$1"]
    },
    "SEARCH": {
        "f": "self.getSearch",
        "all": true
    },
    "FILL": {
        "f": "self.getFill",
        "args": ["$1", "$2"]
    },
    "PATH": {
        "f": "self.getPath",
        "args": ["$1", "$2", "$3"]
    },
    "DISTANCE": {
        "f": "self.getDistance",
        "args": ["$caster", "$target", "$1"]
    },
    "DICE": {
        "f": "self.rand.randint",
        "args": [0, "$1"]
    },
    "STAT": {
        "f": "self.getStat",
        "args": ["$1", "$2"]
    },
    "LISTSTAT": {
        "f": "self.getListStat",
        "args": ["$1", "$2"]
    },
    "FILTER": {
        "f": "self.getFilter",
        "args": ["$1", "$caster", "$2"]
    },
    "FUTURE": {
        "f": "self.testFuture",
        "args": ["$caster", "$target", "$move", "$1", "$2"],
        "default": {"$2": 0}
    },
    "BLOCK": {
        "f": "self.testBlock",
        "args": ["$caster", "$target", "$1"]
    },
    "XLOC": {
        "f": "self.getX",
        "args": ["$1"]
    },
    "YLOC": {
        "f": "self.getY",
        "args": ["$1"]
    },
    "LOC": {
        "f": "self.getLoc",
        "args": ["$1"]
    },
    "NAME": {
        "f": "self.getName",
        "args": ["$1"]
    }
}
