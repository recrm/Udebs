#!/usr/bin/env python3
import itertools
import udebs
import pandas as pd

class Chopsticks(udebs.State):
    def pState(self, state):
        """Gets current state of game."""
        onel = state.getStat("one-left", "FIN")
        oner = state.getStat("one-right", "FIN")
        twol = state.getStat("two-left", "FIN")
        twor = state.getStat("two-right", "FIN")
        turn = state.getStat("one", "ACT")

        return "{},{}-{},{}-{}".format(
            *sorted([onel, oner]),
            *sorted([twol, twor]),
            1 if turn == 2 else 2
        )

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

    def name(self):
        one, two, turn = self.pStatew.split("-")
        if turn == "1":
            return "-".join([one, two])

        return "-".join([two, one])

    def graph(self, storage=set(), completed=set()):
        """Gets the state graph of a game."""

        name = self.name()
        completed.add(self.pStatew)
        for substate in self.substates():
            if substate.result() == None:
                storage.add((name, substate.name()))
                if substate.pStatew not in completed:
                    substate.graph()

        return storage

if __name__ == "__main__":
    field = udebs.battleStart("xml/chopsticks.xml")
    env = Chopsticks(field, algorithm="bruteForceLoop")
    value = env.result()
    print("final", value.value)
    print("states checked", len(env.storage))

    # Remove all nodes that don't result in the game ending
    edges = [{"Source": sname, "Target": tname} 
             for sname, tname  in env.graph()]

    print("edges saved", len(edges))

    # Save results to dataframe
    pd.DataFrame(edges).to_csv("results/chopsticks3.csv", index=False)    
