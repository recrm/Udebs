#!/usr/bin/env python3
import udebs
import collections
from joblib import Parallel, delayed

def state(game):
    hand = game.getStat("hand", "cards")
    count = collections.Counter(hand)
    return (count["chest"] + count["key"] + count["boat"], count["map"], count["skull"])

def batches(boats, maps, death):
    print("starting batch")
    udebs.lookup("LOOKUP", {
        "boat": 27 - boats,
        "map": 9 - maps,
        "skull": 9 - death,
        "chest": 0,
        "key": 0,
    })

    game = udebs.battleStart("xml/pushluck.xml")

    test = game.getStat("hand", "cards")
    test2 = game.getStat("deck", "cards")
    print(test)
    print(test2)

    print(game.cont)


    scores = []
    final = []

    for i in range(100):
        if game.callSingle("hand.STAT.cards LISTSTAT death") < 3:

            scores.append(state(game))

            while game.controlTime():
                scores.append(state(game))

            final.append(scores[-1])

        else:
            scores.append("wipe")
            final.append("wipe")

        # reset game
        game.controlInit("init")
        game.resetState()

    return scores, final

if __name__ == "__main__":

    batches(2, 2, 2)

#    with Parallel(n_jobs=1) as p:
#        gen = (delayed(batches)(2,2,2) for i in range(1))
#        data = p(gen)

#    final_scores = collections.Counter(i for sublist in data for i in sublist[0])
#    final_deaths = collections.Counter(i for sublist in data for i in sublist[1])

#    total = sum(final_scores.values())
#    del final_scores["wipe"]


#    print("total", total)

#    probabilities = {}
#    for key, value in final_scores.items():
#        probabilities[key] = final_deaths[key] / final_scores[key]

#    with open("results.txt", "w+") as f:
#        for key, value in sorted(probabilities.items()):
#            print(key,
#                final_scores[key],
#                final_deaths[key],
#                "{:.2f}".format(final_scores[key] / total),
#                "{:.2f}".format(value),
#            )
