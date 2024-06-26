import udebs
import os
from pytest import raises
import copy


class TestBoardClass:
    def setup(self):
        path = os.path.dirname(__file__)
        self.test = udebs.battleStart(path + "/test.xml")
        self.one = self.test.map["one"]
        self.two = self.test.map["two"]
        self.map = self.test.map['map']

    def test_size(self):
        assert self.one.y == 4
        assert self.two.x == 2
        assert len(self.map) == 30

    def test_get(self):
        assert "unit1" == self.two[(0, 0)]

    def test_get2(self):
        with raises(IndexError):
            self.two[(3, 3)]
        with raises(IndexError):
            self.two[(3, 3)] = "test"
        with raises(IndexError):
            del self.two[(3, 3)]

    def test_get3(self):
        with raises(IndexError):
            self.one[(-1, 0)]
        with raises(IndexError):
            self.one[(-1, 0)] = "test"
        with raises(IndexError):
            del self.one[(-1, 0)]

    def test_get4(self):
        with raises(TypeError):
            self.one[False]
        with raises(TypeError):
            self.one[False] = "test"
        with raises(TypeError):
            del self.one[False]

    def test_insert(self):
        self.one[(0, 0)] = "unit1"
        assert self.one[(0, 0)] == "unit1"
        assert self.one[(1, 0)] == "empty"

    def test_len(self):
        assert len(self.two) == 6
        assert len(self.one) == 16

    def test_iter(self):
        assert len(list(self.two)) == 6
        assert len(list(self.one)) == 16

    def test_x_y(self):
        assert self.two.x == 2
        assert self.two.y == 3

    def test_copy(self):
        three = copy.copy(self.two)
        assert three == self.two
        self.two[(0, 0)] = "empty"
        assert three != self.two

    def test_del(self):
        assert self.two[0, 0] != "empty"
        del self.two[0, 0]
        assert self.two[0, 0] == "immune"

    def test_eq(self):
        assert self.two != "two"

    def test_show(self):
        self.two.show()

    def test_repr(self):
        assert repr(self.two) == "<board: two>"


class TestPathing:
    def setup(self):
        path = os.path.dirname(__file__)
        self.test = udebs.battleStart(path + "/test.xml")
        self.test.controlTravel(self.test["unit1"], (0, 0))
        self.test.controlTravel(self.test["unit2"], (4, 3))
        self.test.controlTravel(self.test["immune"], (2, 2))

    def test_getPath(self):
        empty = self.test["empty"]
        unit1 = self.test["unit1"]
        notempty = self.test["notempty"]
        unit2 = self.test["unit2"]

        test = self.test.get_path(unit1, unit2, notempty)
        assert (0, 0, "map") in test
        assert (4, 3, "map") in test
        assert len(test) == 5
        test = self.test.get_path((0, 1), (0, 1), empty)
        assert len(test) == 1
        self.test.controlTravel(unit1, (1, 2, "two"))
        assert self.test.get_path((0, 0, "two"), (1, 2, "two"), notempty) == []
        assert len(self.test.get_path(empty, empty, empty)) == 0
        assert self.test.get_path(unit1, empty, empty) == []

    def test_distance(self):
        unit1 = self.test["unit1"]
        empty = self.test["empty"]
        unit2 = self.test["unit2"]
        notempty = self.test["notempty"]
        assert self.test.get_distance(empty, unit1, "x") == float("inf")
        assert self.test.get_distance(unit1, empty, "x") == float("inf")
        assert self.test.get_distance(unit1, empty, "empty") == float("inf")
        assert self.test.get_distance(unit1, unit2, 'x') == 4
        assert self.test.get_distance(unit1, unit2, 'y') == 3
        assert self.test.get_distance(unit1, unit2, "z") == 7
        assert self.test.get_distance(unit1, unit2, "hex") == 7
        assert self.test.get_distance(unit1, unit2, 'p1') == 7
        assert self.test.get_distance(unit1, unit2, "p2") == 5
        assert self.test.get_distance(unit1, unit2, 'pinf') == 4
        assert self.test.get_distance(unit1, unit2, notempty) == 4

        with raises(ValueError):
            self.test.get_distance(unit1, unit2, "not a unit")

    def test_testBlock(self):
        empty = self.test["empty"]
        unit1 = self.test["unit1"]
        unit2 = self.test["unit2"]
        notempty = self.test["notempty"]
        assert self.test.test_block(empty, unit1, empty) is False
        assert self.test.test_block(unit1, unit2, notempty)
        assert self.test.test_block(unit1, empty, notempty) is False

    def test_getFill(self):
        unit1 = self.test["unit1"]
        unit2 = self.test["unit2"]
        empty = self.test["empty"]
        notempty = self.test["notempty"]
        sideways = self.test["sideways"]

        test = self.test.get_fill(unit1, callback=notempty)
        assert (2, 2, "map") not in test
        test = self.test.get_fill(unit2, callback=sideways)
        assert all([i[0] == 4 for i in test])
        assert len(self.test.get_fill(empty, callback=empty)) == 0
        test = self.test.get_fill((0, 0, "two"), callback=empty, distance=1)
        assert len(test) == 3
        assert len(self.test.get_fill(empty, empty)) == 0


class TestDirectPathing:
    def setup(self):
        path = os.path.dirname(__file__)
        self.test = udebs.battleStart(path + "/test.xml")
        self.one = self.test.map["one"]
        self.two = self.test.map["two"]
        self.map = self.test.map['map']

    def test_getAdjacent(self):
        test = list(self.two.get_adjacent({(0, 0, "two")}, callback=self.test["empty"], state=self.test))
        assert len(test) == 4
        assert len(test[0]) == 1
        test2 = list(self.two.get_adjacent({(0, 0, "two")}, callback=self.test["empty"], state=self.test))
        assert len(test2) == 4
        assert test2[0] == {(0, 0, "two")}

    def test_testLoc(self):
        assert self.two.test_loc((0, 0)) is False
