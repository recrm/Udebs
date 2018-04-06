from udebs import interpret
import copy
import collections

class Entity(collections.MutableMapping):
    def __init__(self, field, options={}):
        self.field = field
        self.name = options.get("name", "")
        self.loc = options.get("loc", False)
        self.immutable = False

        self.data = {}
        for stat in field.stats:
            self[stat] = options.get(stat, 0)
        for lists in field.lists:
            self[lists] = options.get(lists, [])
        for string in field.strings:
            self[string] = options.get(string, '')

        self.immutable = options.get("immutable", False)

        if self.name:
            self.field[self.name] = self
            self.update()

    def __eq__(self, other):
        try:
            other = self.field.getEntity(other)
        except Exception:
            return False

        for k, v in self.__dict__.items():
            if k != "field" and v != getattr(other, k):
                return False

        return True

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        if not self.immutable:
            self.data[key] = value

    def __delitem__(self, key):
        return

    def __len__(self):
        return len(self.data)

    def __str__(self):
        return self.name

    def __repr__(self):
        return "<entity: "+self.name+">"

    def __iter__(self):
        yield self

    def __deepcopy__(self, memo):
        "Prevents field attribute from being copied."
        new = Entity(self.field)
        for k, v in self.__dict__.items():
            if k != "field":
                setattr(new, k, copy.deepcopy(v, memo))

        return new

    #---------------------------------------------------
    #                 Call Functions                   -
    #---------------------------------------------------
    def getEnv(self, caster, target):
        var_local = {
            "caster": caster,
            "target": target,
            "move": self,
            "C": caster,
            "T": target,
            "M": self,
        }
        return interpret._getEnv(var_local, {"self": self.field})

    def controlEffect(self, env, target=False):
        if target:
            env = self.getEnv(env, target)

        for effect in self.field.getStat(self, 'effect'):
            effect(env)

        return True

    def testRequire(self, env, target=False):
        if target:
            env = self.getEnv(env, target)

        for require in self.field.getStat(self, 'require'):
            if not require(env):
                return require

        return True

    def __call__(self, env, target=False):
        if target:
            env = self.getEnv(env, target)

        value = self.testRequire(env)
        if value == True:
            return self.controlEffect(env)
        return value

    #---------------------------------------------------
    #                Clone Functions                   -
    #---------------------------------------------------
    def controlClone(self):
        """Returns a clone of self."""
        #immutable entities cannot be reproduced.
        if self.immutable:
            return self

        #Create new
        new = copy.deepcopy(self)

        #Set name of new
        self['increment'] +=1
        name = self.name + str(self['increment'])
        new.name = name

        #Setup new group and inc
        new['increment'] = 0

        #Add new to field
        new.field[name] = new
        new.update()

        return new

    #---------------------------------------------------
    #               Update Functions                   -
    #---------------------------------------------------
    def controlLoc(self, loc=None):
        """Updates stored location with system location."""
        if not self.immutable:
            if loc is None:
                for map_ in self.field.map.values():
                    test = map_.getLoc(self.name)
                    if test:
                        self.loc = test
                        break
                else:
                    self.loc = False

            else:

                if loc:
                    name = self.field.getMap(loc[2])[loc]
                    assert name == self.name

                self.loc = loc

        return self.loc

    def controlIncrement(self, stat, increment, multiplyer=1):
        """Changes stored stat of target by increment."""
        increment = int(increment * multiplyer)
        self[stat] += increment
        return increment

    def controlListClear(self, lst):
        """Clear all items from Entity list."""
        if self.immutable:
            return False

        self[lst].clear()
        return True

    def controlListAdd(self, lst, entry):
        """Adds items in Entity list."""
        if self.immutable:
            return False

        if isinstance(entry, Entity):
            if entry.immutable:
                return False
            entry = entry.name
        self[lst].append(entry)
        return True

    def controlListRemove(self, lst, entry):
        """Removes items in Entity list."""
        if self.immutable:
            return False

        if entry in self[lst]:
            self[lst].remove(entry)

        return True
