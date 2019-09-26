from udebs import interpret
import collections
import copy

class Entity(collections.MutableMapping):
    def __init__(self, field, **options):
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

    def __eq__(self, other):
        if not isinstance(other, Entity):
            return False

        for k, v in self.__dict__.items():
            if v != getattr(other, k):
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
        return 1

    def __repr__(self):
        return "<entity: "+self.name+">"

    def __iter__(self):
        yield self

    #---------------------------------------------------
    #                 Call Functions                   -
    #---------------------------------------------------
    def controlEffect(self, env):
        for effect in env["self"].getStat(self, 'effect'):
            effect(env)

        return True

    def testRequire(self, env):
        for require in env["self"].getStat(self, 'require'):
            if not require(env):
                return require

        return True

    def __call__(self, env):
        value = self.testRequire(env)
        if value == True:
            return self.controlEffect(env)
        return value

    #---------------------------------------------------
    #                Clone Functions                   -
    #---------------------------------------------------
    def copy(self, field, **kwargs):
        """The dependency on field prevents me from doing this as __copy__"""

        options = {}
        options.update(self.__dict__["data"])
        options.update(self.__dict__)
        options.update(kwargs)

        for k, v in options.items():
            if isinstance(v, list):
                options[k] = v[:]

        return Entity(field, **options)

    def controlClone(self, instance):
        """Returns a clone of self."""
        #Set name of new
        self['increment'] +=1
        name = self.name + str(self['increment'])

        #Create new
        return self.copy(instance, name=name, increment=0)
