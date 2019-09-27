import copy
import functools
from multiprocessing import Pool
import itertools
from udebs.utilities import Timer
import udebs

def legalMoves(state):
    """Create a list of legal moves in current state space."""
    player = "xPlayer" if state.getStat("xPlayer", "ACT") == 2 else "oPlayer"
    opp = "o" if player[0] == "x" else "x"
    
    map_ = state.map["map"]

    # Get initialized list
    init = []
    half = int(state.getMap().x / 2)
    init.append(half)
    for i in range(1, half + 1):
        init.append(half + i)
        init.append(half - i)
    
    locs = []
    for x in init:
        for y in range(map_.y - 1, -1, -1):
            loc = (x, y)
            if map_[loc] == "empty":
                # We will use this later
                winp = win(state, loc, player[0])
                
                # if value is a winning or blocking move force.
                if winp >= 4 or win(state, loc, opp) >= 4:
                    yield player, loc, "placement"
                    return
                
                locs.append((loc, winp))
                break

    # now we prioritize the remaining
    # Highest priority goes to those squares that produce triples
    # Lowest priority goes to those that are below opponent winning moves.
    high = []
    mid = []
    low = []

    for loc, winp in locs:
        if win(state, (loc[0], loc[1] -1), opp) >= 4:
            low.append(loc)
        elif winp >= 3:
            high.append(loc)
        else:
            mid.append(loc)
    
    for loc in itertools.chain(high, mid, low):
        yield player, loc, "placement"

def win(state, loc, value):
    map_ = state.getMap()
    maxim = 0
    
    for direc in ((1,0), (0,1), (1,1)):
        count = -1
        for i in (1, -1):
            new = value
            centre = loc
            while new == value:
                count +=1
                centre = centre[0] + (direc[0] * i), centre[1] + (direc[1] * i)
                try:
                    new = map_[centre]
                except IndexError:
                    break
        
        if count > maxim:
            maxim = count

    return maxim
                
def endState(state):
    if state.previous is None:
        return None
    
    name = state.previous[0].name[0]
    loc = state.previous[1].loc
    if win(state, loc, name) >= 4:
        if name == "x":
            return 1
        elif name == "o":
            return -1
        
    map_ = state.getMap()
    for square in map_.values():
        if square == "empty":
            return None
        
    return 0
    
def pState(state):
    map_ = state.getMap()
    one = []
    two = []
    
    for y in range(map_.y):
        buf = ''
        for x in range(map_.x):
            entry = map_[x,y]
            if not isinstance(entry, str):
                entry = entry.name
            if entry == "empty":
                entry = "e"
            buf += entry
        one.append(buf)
        two.append(buf[::-1])
    
    one, two = "|".join(one), "|".join(two)
    return one if one < two else two
    
class Node:
    def __init__(self, current, maximizer=True, alpha=-float("inf"), beta=float("inf")):
        self.value = endState(current)
        self.children = substates(current, legalMoves)
        self.results = []
        self.maximizer = maximizer
        self.alpha = alpha
        self.beta = beta
        self.state = current
        self.pState = pState(current)

class ResultException(Exception):
    def __init__(self, map_):
        self.map = map_
    def __repr__(self):
        self.map.show()
        return "stopped doing this map"

def substates(state, legalMoves, time=1):
    """Iterate over substates to a state."""
    stateNew = None
    for move in legalMoves(state):
        if stateNew is None:
            stateNew = copy.copy(state)
            
        if stateNew.castMove(*move[:3], time=time):
            yield stateNew
            stateNew = None

def alphaBetaTree(current, storage = None):
    if storage is None:
        storage = {}

    stack = []

    while True:
        # Check to see if this node has allready been done
        if current.pState not in storage:
            if len(current.results) == 0:
                result = current.value

            elif current.maximizer:
                result = max(current.results)
                if result > current.alpha:
                    current.alpha = result

            else:
                result = min(current.results)
                if result < current.beta:
                    current.beta = result

            # Check if we should decend
            if current.value is None and current.alpha < current.beta:
                child = next(current.children, None)
                if child is not None:
                    stack.append(current)
                    current = Node(child, not current.maximizer, current.alpha, current.beta)
                    continue

            storage[current.pState] = result
        else:
            result = storage[current.pState]
        
        if len(stack) == 0:
            return result

        current = stack.pop()
        current.results.append(result)

if __name__ == "__main__":
    moves = [
    ]

    players = [
        "xPlayer",
        "oPlayer",
    ]

    def boardy(state):
        return state.getMap().y - 1

    module = {"BOARDY": {
        "f": "boardy",
        "args": ["self"],
    }}
    udebs.importModule(module, {"boardy": boardy})
    main_map = udebs.battleStart("xml/connect4.xml")
    for i in udebs.alternate(players, moves, "placement"):
        if not main_map.castMove(*i, time=1):
            print("broken")
            print(i)
            break

    main_map.getMap().show()
    
    storage = {}
    with Timer():
        analysis = alphaBetaTree(Node(main_map, True, alpha=-1, beta=1), storage=storage)
    print(analysis, len(storage))