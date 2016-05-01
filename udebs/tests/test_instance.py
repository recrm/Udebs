#class TestInstanceGets():
#    def setUp(self):
#        self.env = udebs.battleStart("./udebs/test/test.xml")

#    def test_getObject(self):
#        assert Equal(len(self.env.getObject()), 5)
#        assert Is(self.env.getObject("unit1"), self.env.data["unit1"])
#        with assert Raises(udebs.main.UndefinedEntityError):
#            self.env.getObject("error")

#    def test_testTarget(self):
#        test = self.env.getObject("unit1")
#        t = self.env.getTarget
#        assert Equal(t(test), test)
#        assert Equal(t("unit1"), test)
#        assert Equal(t((0,0,"two")), test)
#        assert Equal(t(["unit1", "unit1"], multi=True), [test, test])
#        assert Equal(t((0,0)).loc, (0,0, 'map'))

#    def test_getStat(self):
#        assert Equal(self.env.getStat("unit1", "ACT"), 15)
#        self.env.map["one"].insert("move1", (0,0))
#        assert Equal(self.env.getStat("unit1", "ACT"), 20)
#        assert Equal(len(self.env.getStat("unit1", "equipment")), 3)
#        with assert Raises(udebs.main.UndefinedStatError):
#            self.env.getStat('unit1', "Not Defined")

#    def test_controlTravel(self):
#        self.env.controlTravel("unit1", (0,0, "one"))
#        assert Equal(self.env.getMap((0,0, "one")), "unit1")
#        assert Equal(self.env.getMap((0,0, "two")), "empty")

#        self.env.controlTravel("unit1", 'bump')
#        assert Equal(self.env.getMap((0,0, "one")), "empty")
#        assert False(self.env.getLocation("unit1"))

#        self.env.controlTravel("unit1", (0,0))
#        assert Equal(self.env.getMap((0,0, 'map')), "unit1")
#        assert Equal(self.env.getMap((0,0)), "unit1")
