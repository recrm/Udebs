import udebs
import os
from udebs.board import Board

#Test battleStart
class TestBattleStart:
    def setup(self):
        path = os.path.dirname(__file__)
        self.test = udebs.battleStart(path + "/test.xml")

    def test_config(self):
        assert self.test.logging == False
        assert self.test.name == "testing"
        assert self.test.revert == 4
        assert self.test.version == 1
        assert self.test.seed == 690
        assert self.test.immutable == False

    def test_definitions(self):
        assert "ACT" in self.test.stats
        assert "DESC" in self.test.strings
        assert "equipment" in self.test.lists
        assert "inventory" in self.test.rlist
        total = sum([len(i) for i in [self.test.lists, self.test.stats, self.test.strings]])
        assert total == 8

    def test_map(self):
        assert len(self.test.map) == 3
        assert isinstance(self.test.map['two'], Board)
        assert self.test.map['map'].x == 5
        assert self.test.map['map'].y == 6

        two = self.test.map['two']
        assert two.empty == 'immune'
        assert two.name == 'two'
        assert two.y == 3
        assert two.x == 2

    def test_loc_added(self):
        assert self.test["unit1"]

    def test_var(self):
        assert self.test.time == 4
        #delay not tested yet.

    def test_entity(self):
        #four defined plus one built in.
        assert len(self.test) == 13
        assert len(self.test["unit1"].group) == 1

        stats = self.test.strings.union(self.test.stats, self.test.lists)
        for value in self.test.values():
            for stat in stats:
                assert hasattr(value, stat)

    def test_string(self):
        test = udebs.battleStart("<udebs><config><logging>True</logging></config><map><x>6</x><y>6</y></map></udebs>")
        assert len(test) == 1

class TestBattleWrite:
    def test_equal(self):
        path = os.path.dirname(__file__) + "/test.xml"
        path2 = os.path.dirname(__file__) + "/write_test.xml"

        env1 = udebs.battleStart(path, name="test")
        udebs.battleWrite(env1, path2, True)
        env2 = udebs.battleStart(path2, script=None)
        assert env1 == env2
        os.remove(path2)

