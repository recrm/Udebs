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
        player = "one" if state.getStat("one", "ACT") == 2 else "two"
    
        value = [
            state.getStat("one-left", "FIN"),
            state.getStat("one-right", "FIN"),
            state.getStat("two-left", "FIN"),
            state.getStat("two-right", "FIN"),
            1 if player == "one" else 2,
        ]
        
        return int("".join(str(i) for i in value))

    def legalMoves(self, state):
        player = "one" if state.getStat("one", "ACT") == 2 else "two"
        other = "one" if player == "two" else "two"

        for pair in itertools.product(["left", "right"], repeat=2):
            yield ("{}-{}".format(player, pair[0]), "{}-{}".format(other, pair[1]), "attack")

        yield (player + "-left", player + "-right", "split")
        yield (player + "-right", player + "-left", "split")

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
    field = udebs.battleStart("xml/chopsticks.xml")
    env = Chopsticks(field, "bruteForceLoop")
    value = env.result()
    print("final", value.value)
