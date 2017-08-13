#!/usr/bin/env python3
import udebs

class TicTacToe(udebs.state.State):
    def legalMoves(self, state):
        """Create a list of legal moves in current state space."""
        player = "xPlayer" if state.getStat("xPlayer", "ACT") == 2 else "oPlayer"

        for loc in state.map["map"]:
            if state.map["map"][loc] == "empty":
                yield player, loc, "placement"

    def endState(self, state):
        value = {"o": -1, "t": 0, "x": 1, "": None}
        return value[state.getStat("player", "leaf")]

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

    return "t" if tie else ""

if __name__ == "__main__":
    module = {"ENDGAME": {
        "f": "endgame",
        "args": ["self"],
    }}
    udebs.importModule(module, {"endgame": endgame})
    game = udebs.battleStart("xml/tictactoe.xml")

    # Setup state
    moves = [
    #    (0,0),
    #    (1,0),
    ]

    player = "xPlayer"
    for i in moves:
        game.controlMove(player, i, "placement")
        player = ("xPlayer" if player == "oPlayer" else "oPlayer")

    print(game.map["map"].map)

    # Create state analysis engine
    analysis = TicTacToe(game, "alphaBeta")
    final = analysis.result()
    print("final", final.value)
