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
        udebs.placeholder("TEST")
        assert "TEST" in interpret.variables.modules["other"]

    def test_Player(self):
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
