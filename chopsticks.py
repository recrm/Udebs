#!/usr/bin/env python3
import sys
import csv
import itertools
import copy
import udebs
from udebs import state

class Chopsticks(state.State):
    def pState(self, state):
        """Gets current state of game."""
        player = 1 if state.getStat("one", "ACT") == 2 else 2
    
        value = [
            state.getStat("one-left", "FIN"),
            state.getStat("one-right", "FIN"),
            state.getStat("two-left", "FIN"),
            state.getStat("two-right", "FIN"),
            player,
        ]
        
        return "".join(str(i) for i in value)

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

if __name__ == "__main__":
    sys.setrecursionlimit(10000)
    field = udebs.battleStart("xml/chopsticks.xml")
    env = Chopsticks(field, "bruteForceLoop")
    value = env.result()
    print("final", value.value)
    print("states checked", len(env.storage))
