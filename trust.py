#!/usr/bin/env python3
import udebs
import random
import sys
import itertools

if __name__ == "__main__":

    options = ["cheat", "cooperate"]

    udebs.lookup("LOOKUP", {
        "cooperate": {
            "cooperate": 1,
            "cheat": -1,
        },
        "cheat": {
            "cooperate": 3,
        },
        "timer": 10,
    })

    players = [{
        "f": udebs.copyPlayer,
        "kwargs": {"default": "cooperate"},
        "name": "copy",
        "score": 0,
    }, {
        "f": udebs.constantPlayer,
        "kwargs": {"constant": "cooperate"},
        "name": "always cooperate",
        "score": 0
    }, {
        "f": udebs.constantPlayer,
        "kwargs": {"constant": "cheat"},
        "name": "always cheat",
        "score": 0,
    }, {
        "f": udebs.randomPlayer,
        "kwargs": {},
        "name": "random",
        "score": 0,
    }, {
        "f": udebs.grudgerPlayer,
        "kwargs": {"default": "cooperate", "trigger": "cheat"},
        "name": "grudger",
        "score": 0,
    }]

    for x, y in itertools.combinations_with_replacement(players, 2):
        x["f"]("CHOICE_C", options, **x["kwargs"])
        y["f"]("CHOICE_H", options, **y["kwargs"])

        game = udebs.battleStart("xml/trust.xml")
        for i in game.gameLoop():
            pass

        x["score"] += game.getStat("computer", "score")
        y["score"] += game.getStat("human", "score")

    for i in players:
        print(i["name"], i["score"])
