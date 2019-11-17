from udebs.entity import Entity
import udebs
import os
import copy

class TestEntityClass():
    def setup(self):
        path = os.path.dirname(__file__)
        self.env = udebs.battleStart(path + "/test.xml")

    def test_init(self):
        new = Entity(self.env)
        stats = self.env.strings.union(self.env.stats, self.env.lists)
        for stat in stats:
            assert hasattr(new, stat)

    def test_copy(self):
        unit = self.env["unit1"]
        assert unit == unit.copy(self.env)

    def test_len(self):
        assert len(self.env["unit1"]) == 1
        assert len(list(iter(self.env["unit1"]))) == 1

    def test_clone(self):
        unit = self.env["unit1"]
        unit1 = unit.controlClone(self.env)

        assert unit.increment == 1
        assert unit1.increment == 0
        assert unit.name == "unit1"
        assert unit1.name == "unit11"

    def test_eq(self):
        unit = self.env["unit1"]
        assert (unit == "test") == False
        print(unit, repr(unit))


