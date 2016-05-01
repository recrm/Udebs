from udebs.instance import *
import udebs
import os
from nose.tools import *
import copy

class TestEntityClass():
    def setUp(self):
        path = os.path.dirname(__file__)
        self.env = udebs.battleStart(path + "/test.xml")

    def test_init(self):
        new = Entity(self.env)
        assert new.name in new.group
        stats = self.env.strings.union(self.env.stats, self.env.lists)
        for stat in stats:
            assert hasattr(new, stat)

    def test_update(self):
        unit = self.env["unit1"]
        assert unit.loc == (0,0,"two")
        store = unit.loc
        unit.loc = False
        unit.update()
        assert store == unit.loc

    def test_copy(self):
        unit = self.env["unit1"]
        assert unit == copy.copy(unit)
