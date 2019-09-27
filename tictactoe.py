#!/usr/bin/env python3
import udebs
import json
import pandas as pd

class TicTacToe(udebs.State):
    algorithm = "bruteForce"

    def legalMoves(self, state):
        """Create a list of legal moves in current state space."""
        if self.endState(state) != None:
            return

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

    def tree(self):
        """Gets the state tree of a game."""
        # If node is solvable return solution
        if int(self.result()) != 0:
            return self.result()

        # Collect all possible outputs
        completed = set()
        storage = {}
        for substate in self.substates():
            if substate.pStatew not in completed:
                completed.add(substate.pStatew)
                subresult = substate.tree()

                # Remove any options that don't block oponents autowin.
                if not isinstance(subresult, dict):
                    if subresult.turns == 1:
                        continue

                storage[substate.pStatew, entryName(substate)] = subresult

        # Flatten inevitable ties
        for k, v in storage.items():
            if isinstance(v, dict) or int(v) != 0:
                return storage
        else:
            return self.result()

def initialMoves(game, moves):
    player = "xPlayer"
    for move in moves:
        game.castMove(player, move, "placement", time=1)
        player = ("xPlayer" if player == "oPlayer" else "oPlayer")

def entryName(self):
    if self.entry is not None:
        player, (x, y, _), _ = self.entry
        return player[0] + "_" + str(x) + "_" + str(y)

    return "root"

def stateName(value):
    pState, entry = value
    
    buf = ""
    for i in sorted(pState):
        for row in i:
            for col in row:
                if col == "empty":
                    buf += "_"
                else:
                    buf += col
            buf += ","
        return buf[:-1] + "|" + entry
        
if __name__ == "__main__":
    game = udebs.battleStart("xml/tictactoe.xml")

    # Setup state
    initialMoves(game, [
    ])

    # Print starting state.
    for row in game.map["map"].map:
        print(*(i if i != "empty" else "-" for i in row))

    # Create state analysis engine
    analysis = TicTacToe(game)
    final = analysis.result()
    print("final", final.value, final.turns)
    print("states checked", len(analysis.storage))

    tree = analysis.tree()

    # deserialize result objects
    def deserialize(tree):
        if not isinstance(tree, dict):
            return str(int(tree)) + "-" + str(tree.turns)
        
        return {stateName(k): deserialize(v) for k, v in tree.items()}
    
    named_tree = deserialize(analysis.tree())
    
    
    # Save tree
    with open("results/tictactoe2.json", "w+") as f:
        json.dump(named_tree, f)
        
        
    # Make edges graph
    
    # deserialize result objects
    def create_edges(entry, connections, edges=[]):
        if not isinstance(connections, dict):
            return edges
        
        else:
            for k, v in connections.items():
                target, move = k.split("|")

                edge = {
                    "Source": entry,
                    "Target": target,
                }
                
                if edge not in edges:
                    edges.append(edge)

                create_edges(target, v)
            
        return edges
    
    def create_nodes(tree, nodes=[]):
        if not isinstance(tree, dict):
            return nodes
        
        for k, v in tree.items():
            name = k.split("|")[0]
            nodes.append({
                "Id": name,
                "Level": len([i for i in name if i in "xo"]),
            })
            
            create_nodes(v)
            
        return nodes
    
    edges = create_edges("___,___,___", named_tree)
    nodes = create_nodes(named_tree) + [{"Id": "___,___,___", "Level": 0}]
    
    new_nodes = []
    for i in nodes:
        if i not in new_nodes:
            new_nodes.append(i)
    
    pd.DataFrame(edges).to_csv("results/tictactoe.csv", index=False)
    pd.DataFrame(new_nodes).to_csv("results/nodes.csv", index=False)           
        
        
