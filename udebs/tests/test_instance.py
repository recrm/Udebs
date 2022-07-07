import copy
import udebs
import os
from pytest import raises


class TestInstanceGets:
    def setup(self):
        path = os.path.dirname(__file__)
        self.env = udebs.battleStart(path + "/test.xml", log=True)

    def test_eq(self):
        assert self.env == self.env
        assert self.env != {}
        cp = copy.copy(self.env)
        assert cp == self.env
        self.env.controlIncrement(self.env["unit1"], "ACT", 1)
        assert cp != self.env

        cp = copy.copy(self.env)
        cp.time += 1
        assert cp != self.env

        cp = copy.copy(self.env)
        cp["nope"] = 2
        assert self.env != cp

    def test_get_entity(self):
        unit = self.env["unit1"]

        assert unit is self.env.getEntity("unit1")
        assert unit is self.env.getEntity((0, 0, "two"))
        assert unit in self.env.getEntity(["unit1", (0, 0, "two")])

        assert self.env["empty"] == self.env.getEntity(None)

        with raises(udebs.UndefinedSelectorError):
            self.env.getEntity("unit")

        with raises(udebs.UndefinedSelectorError):
            self.env.getEntity((0, 0, "unknown"))

        with raises(udebs.UndefinedSelectorError):
            self.env.getEntity((-1, 0, "two"))

    def test_getMap(self):
        map_ = self.env.getMap( "two")
        assert self.env.getMap(map_) == map_
        assert self.env.getMap((0, 0, "two")) == map_
        assert self.env.getMap(self.env["unit1"]) == map_
        with raises(udebs.UndefinedSelectorError):
            self.env.getMap("unknown")

    def test_castSingle(self):
        self.env.castSingle("#unit1 ACT += 1")
        # This also tests rlist and groups
        assert self.env.getStat(self.env["unit1"], "ACT") == 16

    def test_udebs_parser(self):
        test = self.env.getQuote("(function((unit).NAME),function(unit.LOC))")
        assert len(test.require) == 2

    # Entity controllers
    def test_getStat(self):
        empty = self.env["empty"]
        unit1 = self.env["unit1"]

        with raises(udebs.UndefinedSelectorError):
            test = self.env.getStat(unit1, "nope")
            print(test)

        assert self.env.getStat(unit1, "DESC") == "description"
        assert self.env.getStat(unit1, "group") == ["group1"]

    def test_controlListAdd(self):
        self.env.castSingle("#unit2 inventory GETS move1")
        assert len(self.env.getStat(self.env["unit2"], "inventory")) == 1

    def test_controlListRemove(self):
        self.env.castSingle("#unit1 inventory LOSES move1")
        assert len(self.env.getStat(self.env["unit1"], "inventory")) == 1

    def test_controlListClear(self):
        self.env.castSingle("#unit1 CLEAR inventory")
        assert len(self.env.getStat(self.env["unit1"], "inventory")) == 0

    def test_controlShuffle(self):
        self.env.castSingle("#unit1 SHUFFLE inventory")
        assert len(self.env.getStat(self.env["unit1"], "inventory")) == 2

    def test_controlIncrement(self):
        self.env.castSingle("#unit2 ACT -= 1")
        assert self.env.getStat(self.env["unit2"], "ACT") == -1

    def test_controlString(self):
        self.env.castSingle("#unit2 ACT REPLACE 10")
        assert self.env.getStat(self.env["unit2"], "ACT") == 10

    def test_controlRecruit(self):
        script = "#unit2 RECRUIT (1 1 two)"
        self.env.castSingle(script)
        assert self.env.getEntity((1, 1, "two")).name == "unit21"

        self.env.castSingle("#unit2 RECRUIT #empty")
        assert self.env.getEntity("unit22").loc is None

    def test_controlTravel(self):
        self.env.castSingle("#unit1 MOVE #unit2")
        assert self.env.getEntity("unit1").loc == (1, 0, "two")
        assert self.env.getEntity("unit2").loc is None
        assert self.env["empty"].loc is None

        with raises(Exception):
            self.env.castSingle("unit1 MOVE (FILL (0 0 two) empty)")

    # Entity Locs
    def test_getLoc(self):
        assert self.env.castSingle("#unit1.LOC") == (0, 0, "two")

    def test_getX(self):
        assert self.env.castSingle("#unit1.XLOC") == 0

    def test_getY(self):
        assert self.env.castSingle("#unit1.YLOC") == 0

    def test_getName(self):
        assert self.env.castSingle("#unit1.NAME") == "unit1"

    # Get Functions
    def test_getListStat(self):
        assert self.env.castSingle("#unit1 inventory LISTSTAT ACT") == 5
        assert self.env.castSingle("#unit1 inventory LISTSTAT inventory") == []
        assert self.env.castSingle("#unit1 inventory LISTSTAT DESC") == ""

    def test_getListGroup(self):
        assert self.env.castSingle("#unit1 inventory LISTGROUP move2") == "move1"
        assert self.env.castSingle("#unit1 inventory LISTGROUP move1") is False

    def test_getGroup(self):
        assert len(self.env.castSingle("ALL group1 group3")) == 2

    def test_getSearch(self):
        assert len(self.env.castSingle("SEARCH group1 group3")) == 1

    def test_gameLoop(self):
        index = 0
        self.env.cont = True
        print(self.env.time)
        for i in self.env.gameLoop():
            if index == 1:
                i.next = self.env

            index += 1
            if index > 4:
                i.castSingle("EXIT")

        assert index == 5
        assert self.env.time == 7
        self.env.resetState()
        assert self.env.time == 0
        assert self.env.cont is True

    def test_revert(self):
        self.env.controlTime(4)
        assert self.env.time == 8
        a = self.env.getRevert(2)
        assert a.time == 6
        assert self.env.getRevert(100) is False

    def test_error(self):
        error = udebs.UndefinedSelectorError("one", "entity")
        print(error)

    # Other functions
    def test_mapIter(self):
        assert len(list(self.env.mapIter("two"))) == 6

    def test_castAction(self):
        assert self.env.castAction("move2", "move2") is False

    def test_testMove(self):
        empty = self.env["empty"]
        assert self.env.testMove(empty, empty, self.env["tick"])
        assert self.env.testMove(empty, empty, self.env["move2"]) is False
