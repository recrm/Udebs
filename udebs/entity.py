class Entity():
    def __init__(self, field, **options):
        if "_data" in options:
            # second path for copy operation only
            self.__dict__ = options["_data"]
            return

        self.name = options.get("name", "")
        self.loc = options.get("loc", False)
        self.immutable = options.get("immutable", False)

        for stat in field.stats:
            self.__dict__[stat] = options.get(stat, 0)
        for lists in field.lists:
            self.__dict__[lists] = options.get(lists, [])
        for string in field.strings:
            self.__dict__[string] = options.get(string, '')

    def __eq__(self, other):
        if not isinstance(other, Entity):
            return False

        return self.__dict__ == other.__dict__

    def __len__(self):
        return 1

    def __repr__(self):
        return f"<entity: {self.name}{'!' if self.immutable else ''}>"

    def __iter__(self):
        yield self

    def __str__(self):
        return self.name

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

        for k, v in self.__dict__.items():
            if k not in kwargs:
                if isinstance(v, list):
                    v = v[:]
                kwargs[k] = v

        return Entity(field, _data=kwargs)

    def controlClone(self, instance):
        """Returns a clone of self."""
        #Set name of new
        self.increment +=1
        name = self.name + str(self.increment)

        #Create new
        return self.copy(instance, name=name, increment=0)
