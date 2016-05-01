import udebs
import os
from nose.tools import *
class TestBoardClass():
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
        assert "unit1" == self.two[(0,0)]

    @raises(IndexError)
    def test_get2(self):
        self.two[(3,3)]

    @raises(IndexError)
    def test_get3(self):
        self.one[(-1, 0)]

    @raises(TypeError)
    def test_get4(self):
        self.one[False]

    def test_find(self):
        assert self.two.find("unit2") == (1,0, "two")
        assert not self.one.find("unit1")
        p = self.two.find("unit2")
        assert "unit2" == self.two[p]

    def test_insert(self):
        self.one[(0,0)] = "unit1"
        assert self.one[(0,0)] == "unit1"
        assert self.one[(1,0)] == "empty"


class TestPathing():
    def setup(self):
        path = os.path.dirname(__file__)
        self.test = udebs.battleStart(path + "/test.xml")
        self.test.controlTravel("unit1", (0,0))
        self.test.controlTravel("unit2", (4,3))
        self.test.controlTravel("immune", (2,2))

    def test_distance(self):
        assert self.test.getDistance("unit1", "unit2", 'x') == 4
        assert self.test.getDistance("unit1", "unit2", 'y') == 3
        assert self.test.getDistance("unit1", "unit2", 'p1') == 7
        assert self.test.getDistance("unit1", "unit2", 'pinf') == 4
        print(self.test.getDistance("unit1", "unit2", "notempty"))
        assert self.test.getDistance("unit1", "unit2", "notempty") == 7

    def test_adjacent(self):
        test = []
        for i in self.test.getAdjacent((4,2), "notempty"):
            test.extend(i)

        assert len(test) == 29

    def test_testBlock(self):
        assert self.test.testBlock("unit1", "unit2", "notempty")

    def test_testPath(self):
        test = self.test.getPath("unit1", "unit2", "notempty")
        assert (0, 0, "map") in test
        assert (4, 3, "map") in test
        assert len(test) == 8
        test = self.test.getPath((0,1), (0,1), "empty")
        assert len(test) == 1

        #Fixed bug in program.
        test = self.test.get

    def test_getFill(self):
        test = self.test.getFill("unit1", "notempty")
        assert (2,2,"map") not in test

        test = self.test.getFill("unit2", "sideways")
        assert all([i[0] == 4 for i in test])


#    @raises(IndexError)
#    def test_get2(self):
#        self.two[(3,3)]
