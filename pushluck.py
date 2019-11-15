import udebs
from collections import Counter
import copy
from functools import partial

class Pushluck(udebs.State):
    def pState(self, s):
        hand = s.getStat("hand", "cards")
        d = Counter(hand)
        remaining = s.getStat("hand", "draws") - len(hand)
        return (d["map"], d["dmap"], d["chest"], d["key"], d["boat"], d["skull"], remaining)

    def legalMoves(self, s):
        d = Counter(s.getStat("deck", "cards"))
        tot = sum(d.values())
        for card in d:
            yield ("hand", card, "drawsingle", d[card] / tot)

    def endState(self, s):
        h = partial(s.getStat, "hand")
        if h("skulls") >= h("lives"):
            return 0

        if h("draws") >= len(h("cards")):
            return None

        return h("score")

def ev(state, storage=None):
    new_state = copy.deepcopy(state)
    obj = Pushluck(new_state, storage=storage, algorithm="expectationValue", debug=False)
    result = obj.result()
    return result.value - state.getStat("hand", "score"), obj.storage

if __name__ == "__main__":
    storage = {}
    main_map = udebs.battleStart("xml/pushluck.xml")

    print()
    main_map.controlTime()
    result, storage = ev(main_map, storage)
    print("\nev of next card is:", result)
