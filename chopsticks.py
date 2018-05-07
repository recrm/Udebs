#!/usr/bin/env python3
import itertools
import udebs

class Chopsticks(udebs.State):
    def pState(self, state):
        """Gets current state of game."""
        one = frozenset([
            state.getStat("one-left", "FIN"),
            state.getStat("one-right", "FIN"),
        ])

        two = frozenset([
            state.getStat("two-left", "FIN"),
            state.getStat("two-right", "FIN"),
        ])

        return (one, two, state.getStat("one", "ACT"))

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
        one = (state.getStat("one-left", "FIN") +
            state.getStat("one-right", "FIN"))

        if one == 0:
            return -1

        two = (state.getStat("two-left", "FIN") +
            state.getStat("two-right", "FIN"))

        if two == 0:
            return 1

        return None

    def name(self):
        one = "".join(str(i) for i in self.pState[0])
        two = "".join(str(i) for i in self.pState[1])
        player = 1 if self.pState[2] == 2 else 2
        return "{}-{}-{}".format(one, two, player)

if __name__ == "__main__":
    field = udebs.battleStart("xml/chopsticks.xml")
    env = Chopsticks(field, "bruteForceLoop")
    value = env.result()
    print("final", value.value)
    print("states checked", len(env.storage))
