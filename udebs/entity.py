from udebs import interpret
import itertools
import logging
import copy
import collections
import sys

class Entity(collections.MutableMapping):
    def __init__(self, field, options={}):
        self.field = field
        self.name = options.get("name", "")
        self.loc = options.get("loc", False)
        self.immutable = False

        self.__data = {}
        for stat in field.stats:
            self.__data[stat] = options.get(stat, 0)
        for lists in field.lists:
            self.__data[lists] = options.get(lists, [])
        for string in field.strings:
            self.__data[string] = options.get(string, '')

        if "group" in self.__data:
            if self.name not in self.__data['group']:
                self['group'] = [self.name] + self['group']

        self.immutable = options.get("immutable", False)

        if self.name:
            self.field[self.name] = self
            self.update()

    def __eq__(self, other):
        try:
            other = self.field.getEntity(other)
        except Exception:
            return False

        values = [
            self.name == other.name,
            self.loc == other.loc,
            self.immutable == other.immutable,
            self.__data == other.__data,
        ]
        return all(values)

    def __getitem__(self, key):
        return self.__data[key]

    def __setitem__(self, key, value):
        if not self.immutable:
            self.__data[key] = value

    def __delitem__(self, key):
        return

    def __iter__(self):
        return iter(self.__data)

    def __len__(self):
        return len(self.__data)

    def __str__(self):
        return self.name

    def __repr__(self):
        return "<entity: "+self.name+">"

    def __iter__(self):
        yield self

    def __deepcopy__(self, memo):
        "Prevents field attribute from being copied."
        new = Entity(self.field)
        new.name = self.name
        new.loc = self.loc
        new.immutable = self.immutable
        new.__data = copy.deepcopy(self.__data)

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
            env = self.getEnv(caster, target)

        for i in self.field.getStat(self, 'effect'):
            i.call(env)

        return True

    def testRequire(self, env, target=False):
        if target:
            env = self.getEnv(env, target)

        for i in self.field.getStat(self, 'require'):
            if not i.call(env):
                return i

        return True

    def call(self, env, target=False):
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
        new['group'].remove(self.name)
        new['group'] = [name] + new['group']
        new['increment'] = 0

        #Add new to field
        new.field[name] = new
        new.update()

        return new

    #---------------------------------------------------
    #               Update Functions                   -
    #---------------------------------------------------
    def controlLoc(self):
        """Updates stored location with system location."""
        if not self.immutable:
            for map_ in self.field.map.values():
                test = map_.getLoc(self.name)
                if test:
                    self.loc = test
                    break
            else:
                self.loc = False

        return self.loc

    def controlIncrement(self, stat, increment, multiplyer=1):
        """Changes stored stat of target by increment."""
        increment = int(increment * multiplyer)
        self[stat] = self[stat] + increment
        return increment

    def controlListClear(self, lst):
        """Clear all items from Entity list."""
        if self.immutable:
            return False

        list_ = self[lst]
        list_.clear()
        if lst == "group":
            list_.append(self.name)

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
