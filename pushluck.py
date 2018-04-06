#!/usr/bin/env python3
import udebs
import collections
from joblib import Parallel, delayed
import sys
import itertools
import json

def batches(boats, dmaps, death, iterations=1000):
    game = udebs.battleStart("xml/pushluck.xml", script=None)
    deck = {
        "boat": 27 - boats,
        "dmap": 9 - dmaps,
        "skull": 9 - death,
        "chest": 0,
        "key": 0,
        "map": 0,
    }

    for key, value in deck.items():
        game.callSingle("{} amount REPLACE {}".format(key, value))

    scores = collections.Counter()

    for i in range(iterations):
        game.castAction("deck", "shuffle")
        game.castMove("hand", "deck", "draw")
        skulls = game.getStat("hand", "skulls")

        if skulls > 3:
            skulls = 3

        scores[skulls] +=1

    return (boats, dmaps, death), scores

if __name__ == "__main__":
    funct = delayed(batches)
    products = itertools.product(range(28), range(10), range(3))
    gen = (funct(*i, iterations=1000) for i in products)
    data = Parallel(n_jobs=-1, verbose=5)(gen)

    results = {}
    for state, scores in data:
        key = "::".join(str(i) for i in state)
        results[key] = {
            "hand": {
                "boats": state[0],
                "dmaps": state[1],
                "skulls": state[2],
            },
            "skulls_proba": dict(scores),
        }

    with open("results/pushluck.json", "w+") as f:
        json.dump(results, f)
