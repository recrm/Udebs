#!/usr/bin/env python3
import udebs
import json

class TicTacToe(udebs.State):
    endgames = {"o": -1, "t": 0, "x": 1, "": None}
    
    def legalMoves(self, state):
        """Create a list of legal moves in current state space."""
        player = "xPlayer" if state.getStat("xPlayer", "ACT") == 2 else "oPlayer"

        for loc in state.map["map"]:
            if state.map["map"][loc] == "empty":
                yield player, loc, "placement"

    def endState(self, state):
        return self.endgames[state.getStat("player", "leaf")]
    
    def name(self):
        player, (x, y, _), _ = self.entry
        return player[0] + "_" + str(x) + "_" + str(y)

# Setup Udebs
def endgame(state):
    def rows(gameMap):
        """Iterate over possible win conditions in game map."""
        size = len(gameMap)

        for i in range(size):
            yield gameMap[i]
            yield [j[i] for j in gameMap]

        yield [gameMap[i][i] for i in range(size)]
        yield [gameMap[size - 1 - i][i] for i in range(size)]

    # Check for a win
    tie = True
    for i in rows(state.map["map"].map):
        value = set(i)
        if "empty" in value:
            tie = False
        elif len(value) == 1:
            return i[0]

    if tie:
        return "t"

if __name__ == "__main__":
    module = {"ENDGAME": {
        "f": "endgame",
        "args": ["self"],
    }}
    udebs.importModule(module, {"endgame": endgame})
    game = udebs.battleStart("xml/tictactoe.xml")

    # Setup state
    moves = [
    ]

    # Play Startup Moves.
    player = "xPlayer"
    for i in moves:
        game.controlMove(player, i, "placement")
        player = ("xPlayer" if player == "oPlayer" else "oPlayer")

    # Print starting state.
    for row in game.map["map"].map:
        print(*(i if i != "empty" else "-" for i in row))

    # Create state analysis engine
    analysis = TicTacToe(game, "bruteForce")
    final = analysis.result(len(moves) % 2)
    print("final", final.value)
    print("states checked", len(analysis.storage))
    
    # Save tree
    with open("results/tictactoe.json", "w+") as f:
        json.dump(analysis.tree(), f)
