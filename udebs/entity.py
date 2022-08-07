from udebs import errors, interpret


class Entity:
    def __init__(self, field=None, debug=None, **options):
        if "_data" in options:
            # second path for copy operation only
            self.__dict__ = options["_data"]
            return

        self.other = {"name", "immutable", "loc"}
        self.lists = set()

        # Get base special data
        self.immutable = options.get("immutable", field.immutable)
        self.loc = None

        # Set guaranteed attributes
        self.increment = 0
        self.group = []
        self.effect = []
        self.require = []
        self.name = ""

        # Set the stats
        for stat in field.stats:
            setattr(self, stat, int(options.get(stat, 0)))
            self.other.add(stat)
        for lists in field.lists.union({"group"}):
            value = options.get(lists, [])
            if not isinstance(value, list):
                value = [value]
            setattr(self, lists, value)
            self.lists.add(lists)
        for string in field.strings:
            setattr(self, string, options.get(string, None))
            self.other.add(string)

        # Transform effect and require into scripts
        for stat_list in [self.effect, self.require]:
            for i, elem in enumerate(stat_list):
                if isinstance(elem, str):
                    stat_list[i] = interpret.Script(elem, debug=debug)

        # Set loc.
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
                print(env)
                raise errors.UdebsExecutionError(require)

            if not value:
                return require

        return True

    def __call__(self, env, force=False):
        if not force:
            value = self.test(env)
            if value is not True:
                return value

        for effect in env["self"].getStat(self, 'effect'):
            try:
                eval(effect.code, env)
            except Exception:
                raise errors.UdebsExecutionError(effect)

        return True

    # ---------------------------------------------------
    #                Clone Functions                   -
    # ---------------------------------------------------
    def copy(self, **kwargs):
        """Make a copy of this entity for use in other instances."""
        kwargs["other"] = self.other
        kwargs["lists"] = self.lists

        for k in self.other:
            if k not in kwargs:
                kwargs[k] = self.__dict__[k]

        for k in self.lists:
            if k not in kwargs:
                kwargs[k] = self.__dict__[k][:]

        return Entity(_data=kwargs)
