from udebs import interpret
import udebs
from pytest import raises
import os

class TestBattleStart:
    def test_alternate(self):
        tests = [["one", "two"], "three", ["four", "five", "six"]]
        test = list(udebs.alternate(*tests))
        assert len(test) == 3

    def test_timer(self):
        with udebs.Timer() as f:
            for i in range(3):
                assert i > -1

        assert f.time > 0

    def test_placeholder(self):
        """Not function is depricated"""
        udebs.placeholder("TEST")
        assert "TEST" in interpret.variables.modules["other"]

    def test_Player(self):
        """Not function is depricated"""
        udebs.Player("TEST")
        assert "TEST" in interpret.variables.modules["other"]

        path = os.path.dirname(__file__)
        env = udebs.battleStart(path + "/test.xml", log=True)

        with raises(udebs.UdebsExecutionError):
            env.castSingle("(TEST)")

    def test_lookup(self):
        udebs.lookup("LOOKUP", {"one": {"two": {"three": 4}}})
        path = os.path.dirname(__file__)
        env = udebs.battleStart(path + "/test.xml", log=True)
        assert env.castSingle("LOOKUP one two three") == 4
        test = env.castSingle("LOOKUP one three")
        assert test == 0

    def test_register(self):

        @udebs.register({"args": ["$1", "$2"]})
        def ADDITION1(one, two):
            return one + two

        def ADDITION2(one, two):
            return one + two

        udebs.register(ADDITION2, ["$1", "$2"])

        @udebs.register(["$1"])
        class SUBTRACTION:
            def __init__(self):
                self.one = 7

            def __call__(self, two):
                return self.one - two

        udebs.register(SUBTRACTION, ["$1"], name="sub1")

        main_map = udebs.battleStart()
        assert main_map.castSingle("ADDITION1 1 1") == 2
        assert main_map.castSingle("ADDITION2 1 3") == 4
        assert main_map.castSingle("SUBTRACTION 4") == 3
        assert main_map.castSingle("sub1 4") == 3



