#!/usr/bin/env python3
import itertools
import udebs

class Chopsticks(udebs.State):
    def pState(self, state):
        """Gets current state of game."""
        one = "".join(str(i) for i in sorted([
            state.getStat("one-left", "FIN"),
            state.getStat("one-right", "FIN"),
        ]))

        two = "".join(str(i) for i in sorted([
            state.getStat("two-left", "FIN"),
            state.getStat("two-right", "FIN"),
        ]))

        turn = state.getStat("one", "ACT")

        player = 1 if turn == 2 else 2
        return "{}-{}-{}".format(one, two, player)
        
    def legalMoves(self, state):
        def t(player, hand):
            return "{}-{}".format(player, hand)

        player = "one" if state.getStat("one", "ACT") == 2 else "two"
        other = "one" if player == "two" else "two"

        for attacker, target in itertools.product(["left", "right"], repeat=2):
            yield (t(player, attacker), t(other, target), "attack")

        yield (t(player, "left"), t(player, "right"), "split")
        yield (t(player, "right"), t(player, "left"), "split")

    def endState(self, state):
        # test for one win
        one_l = state.getStat("one-left", "FIN")
        one_r = state.getStat("one-right", "FIN")
        
        if one_l + one_r == 0:
            return -1

        # test for two win
        two_l = state.getStat("two-left", "FIN")
        two_r = state.getStat("two-right", "FIN")

        if two_l + two_r == 0:
            return 1
        
        return None

if __name__ == "__main__":
    field = udebs.battleStart("xml/chopsticks.xml")
    env = Chopsticks(field, algorithm="bruteForceLoop")
    value = env.result()
    print("final", value.value)
    print("states checked", len(env.storage))
