from udebs import errors, interpret


class Entity:
    def __init__(self, field=None, debug=None, **options):
        if "_data" in options:
            # second path for copy operation only
            self.__dict__ = options["_data"]
            return

        # Get base data
        self.name = options.get("name", "")
        self.immutable = options.get("immutable", field.immutable)

        # Set the stats
        for stat in field.stats:
            setattr(self, stat, int(options.get(stat, 0)))
        for lists in field.lists:
            value = options.get(lists, [])
            if not isinstance(value, list):
                value = [value]
            setattr(self, lists, value)
        for string in field.strings:
            setattr(self, string, options.get(string, ''))

        # Transform effect and require into scripts
        for stat_list in [self.effect, self.require]:
            for i, elem in enumerate(stat_list):
                if isinstance(elem, str):
                    stat_list[i] = interpret.Script(elem, field.version, debug=debug)

        # Set loc.
        self.loc = None
        if not self.immutable:
            for map_ in field.map.values():
                for loc in map_:
                    if map_[loc] == self.name:
                        self.loc = loc
                        break

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

    # ---------------------------------------------------
    #                 Call Functions                    -
    # ---------------------------------------------------
    def test(self, env):
        for require in env["self"].getStat(self, 'require'):
            try:
                value = eval(require.code, env)
            except RecursionError:
                raise
            except Exception:
                raise errors.UdebsExecutionError(require)

            if not value:
                return require

        return True

    def __call__(self, env):
        value = self.test(env)
        if value is not True:
            return value

        for effect in env["self"].getStat(self, 'effect'):
            try:
                eval(effect.code, env)
            except RecursionError:
                raise
            except Exception:
                raise errors.UdebsExecutionError(effect)

        return True

    # ---------------------------------------------------
    #                Clone Functions                   -
    # ---------------------------------------------------
    def copy(self, **kwargs):
        """The dependency on field prevents me from doing this as __copy__"""

        for k, v in self.__dict__.items():
            if k not in kwargs:
                if isinstance(v, list):
                    v = v[:]
                kwargs[k] = v

        return Entity(_data=kwargs)

    def clone(self):
        """Returns a clone of self."""
        # Set name of new
        self.increment += 1
        name = self.name + str(self.increment)

        # Create new
        return self.copy(name=name, increment=0)
