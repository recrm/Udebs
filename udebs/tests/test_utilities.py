import udebs


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

    def test_register(self):
        @udebs.register({"args": ["$1", "$2"]})
        def ADDITION1(one, two):
            return one + two

        def ADDITION2(one, two):
            return one + two

        udebs.interpret.register(ADDITION2, ["$1", "$2"])

        @udebs.interpret.register(["$1"])
        class SUBTRACTION:
            def __init__(self):
                self.one = 7

            def __call__(self, two):
                return self.one - two

        udebs.interpret.register(SUBTRACTION, ["$1"], name="sub1")

        main_map = udebs.battleStart()
        assert main_map.castSingle("ADDITION1 1 1") == 2
        assert main_map.castSingle("ADDITION2 1 3") == 4
        assert main_map.castSingle("SUBTRACTION 4") == 3
        assert main_map.castSingle("sub1 4") == 3
