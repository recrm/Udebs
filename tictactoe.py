#!/usr/bin/env python3
import udebs
import json

class TicTacToe(udebs.State):
    algorithm = "bruteForce"
    
    def legalMoves(self, state):
        """Create a list of legal moves in current state space."""
        player = "xPlayer" if state.getStat("xPlayer", "ACT") == 2 else "oPlayer"

        for loc in state.map["map"]:
            if state.map["map"][loc] == "empty":
                yield player, loc, "placement"

    def endState(self, state):
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
                if i[0] == "x":
                    return 1
                elif i[0] == "o":
                    return -1

        if tie:
            return 0
    
    def name(self):
        if self.entry is not None:
            player, (x, y, _), _ = self.entry
            return player[0] + "_" + str(x) + "_" + str(y)

        return "root"

def initialMoves(game, moves):
    player = "xPlayer"
    for move in moves:
        game.controlMove(player, move, "placement")
        player = ("xPlayer" if player == "oPlayer" else "oPlayer")

    return len(moves) % 2

def checkTree(value):
    if isinstance(value, dict):
        return {i:checkTree(v) for i,v in value.items()}
    else:
        return "{}-{}".format(value.value, value.turns)

if __name__ == "__main__":
    game = udebs.battleStart("xml/tictactoe.xml")

    # Setup state
    offset = initialMoves(game, [
    ])

    # Print starting state.
    for row in game.map["map"].map:
        print(*(i if i != "empty" else "-" for i in row))

    # Create state analysis engine
    analysis = TicTacToe(game)
    final = analysis.result(offset)
    print("final", final.value, final.turns)
    print("states checked", len(analysis.storage))
    
    # Save tree
    with open("results/tictactoe.json", "w+") as f:
        json.dump(checkTree(analysis.tree()), f)
