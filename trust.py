#!/usr/bin/env python3
import udebs
import itertools
import random
import itertools
from collections import Counter

class Random(udebs.Player):
    def __call__(self, state):
        return random.choice(["cheat", "cooperate"])

class Human(udebs.Player):
    def __call__(self, state):
        x = input("what do you play? ")
        while x not in ["cheat", "cooperate"]:
            x = input("try again")

        return x

class AlwaysTrust(udebs.Player):
    def __call__(self, state):
        return "cooperate"

class AlwaysCheat(udebs.Player):
    def __call__(self, state):
        return "cheat"

class Grudger(udebs.Player):
    def __call__(self, state):
        if state.getStat("computer", "score") != state.getStat("human", "score"):
            self.grudged = True

        if getattr(self, "grudged", False):
            return "cheat"

        return "cooperate"

class Forgiver(udebs.Player):
    def __init__(self, *args, **kwargs):
        self.previous = "cooperate"
        self.score = 0
        super().__init__(*args, **kwargs)

    def __call__(self, state):
        score = state.getStat("computer", "score") + state.getStat("human", "score")
        if score - self.score == 2:
            self.previous = "cheat"
        if score - self.score == 6:
            self.previous = "cooperate"
        if score - self.score == 5:
            if self.previous == "cheat":
                self.previous = "cooperate"
            else:
                self.previous = "cheat"

        self.score = score
        return self.previous

class CheatFirst(udebs.Player):
    def __call__(self, state):
        if getattr(self, "cheated", False):
            return "cooperate"

        self.cheated = True
        return "cheat"

class TrustFirst(udebs.Player):
    def __call__(self, state):
        if getattr(self, "cheated", False):
            return "cheat"

        self.cheated = True
        return "cooperate"

udebs.lookup("LOOKUP", {
    "cooperate": {
        "cooperate": 2,
        "cheat": -1,
    },
    "cheat": {
        "cooperate": 3,
        "cheat": 0,
    },
    "timer": 10,
})

def meta(players, spaces, strategies):
    while True:
        results = tourney(players, spaces).most_common()

        windex, winner = results[0][0].split("_")
        lindex, loser = results[-1][0].split("_")
        runnerx, runner = results[-2][0].split("_")

        explore = random.choice(strategies)

        yield results

        players[int(lindex)] = players[int(windex)]
        players[int(runnerx)] = random.choice(strategies)

def tourney(players, spaces):
    scores = Counter()
    for args in itertools.combinations(enumerate(players), len(spaces)):
        for (index, player), role in zip(args, spaces):
            player(role)

        main_map = udebs.battleStart("xml/trust.xml")
        for i in main_map.gameLoop():
            pass

        for (index, player), role in zip(args, ["human", "computer"]):
            scores[str(index) + "_" + player.__name__] += main_map.getStat(role, "score")

    return scores

if __name__ == "__main__":
    scores = Counter()

    strategies = [Random, AlwaysTrust, AlwaysCheat, Grudger, CheatFirst, TrustFirst, Forgiver]

    players = [
        Random,
        Random,
        Random,
        AlwaysTrust,
        AlwaysTrust,
        AlwaysTrust,
        AlwaysCheat,
        AlwaysCheat,
        AlwaysCheat,
        Grudger,
        Grudger,
        Grudger,
        Forgiver,
        Forgiver,
        Forgiver,
    ]

    spaces = ["HUMAN", "COMPUTER"]

    for results in meta(players, spaces, strategies):
        for x, y in results:
            print(x, y)
        test = input()
        if test == "n":
            break
