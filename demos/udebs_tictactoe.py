#!/usr/bin/env python3
import udebs
import json
from udebs.treesearch import State
from udebs.treesearch.utilities import cache, count_recursion, Result

game_config = """
<udebs>

<config>
    <logging>False</logging>
    <name>tictactoe</name>
    <immutable>True</immutable>
</config>

<map>
    <dim>
        <x>3</x>
        <y>3</y>
    </dim>
</map>

<definitions>
    <stats>
        <ACT />
    </stats>
    <strings>
        <token />
    </strings>
</definitions>

<entities>
    <player />

    <tick>
        <require>
            <i>score = (ENDSTATE)</i>
            <i>$score != None</i>
        </require>
        <effect>EXIT $score</effect>
    </tick>

    <xPlayer immutable="False">
        <group>player</group>
        <ACT>2</ACT>
        <token>x</token>
    </xPlayer>

    <oPlayer immutable="False">
        <group>player</group>
        <ACT>1</ACT>
        <token>o</token>
    </oPlayer>

    <x />
    <o />

    <placement>
        <require>
            <i>$caster.STAT.ACT &gt;= 2</i>
            <i>$target.NAME == empty</i>
        </require>
        <effect>
            <i>#($caster.STAT.token) RECRUIT $target</i>
            <i>$caster ACT -= 2</i>
            <i>ALL.player ACT += 1</i>
        </effect>
    </placement>

</entities>
</udebs>
"""


# Setup Udebs
@udebs.register(["self"])
def ENDSTATE(state):
    def rows(game_map):
        """Iterate over possible win conditions in game map."""
        size = len(game_map)

        for i_ in range(size):
            yield game_map[i_]
            yield [j[i_] for j in game_map]

        yield [game_map[i_][i_] for i_ in range(size)]
        yield [game_map[size - 1 - i_][i_] for i_ in range(size)]

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


class TicTacToe(State):
    def legalMoves(self):
        """Create a list of legal moves in current state space."""
        player = "xPlayer" if self.getStat(self["xPlayer"], "ACT") == 2 else "oPlayer"
        for loc, value in self.map["map"].items():
            if value == "empty":
                yield player, loc, "placement"

    def hash(self):
        """Return an immutable representation of a game map."""
        mappings = {
            "empty": "0",
            "x": "1",
            "o": "2"
        }

        map_ = self.map["map"]
        row = []
        for y in range(map_.y):
            buf = ''
            for x in range(map_.x):
                buf += mappings[map_[(x, y)]]
            row.append(buf)

        def sym_y(x_):
            return list(reversed(x_))

        def sym_90(x_):
            return ["".join(reversed(i_)) for i_ in zip(*x_)]

        syms = [row]
        for i in range(3):
            syms.append(sym_90(syms[-1]))

        syms.append(sym_y(syms[0]))
        for i in range(3):
            syms.append(sym_90(syms[-1]))

        return min(int("".join(i), 3) for i in syms)

    @cache
    @count_recursion
    def result(self, maximizer=True):
        value = self.endState()
        if value is not None:
            return Result(value, 0)

        f_ = max if maximizer else min
        result = f_(c.result(not maximizer) for c, e in self.substates())
        value, turns = result.value, result.turns + 1
        return Result(value, turns)

    def tree(self, maximizer=True):
        """Compile all results into a tree."""
        # If node is solvable return solution
        value = self.result(maximizer)
        if int(value) != 0:
            return value

        # Collect all possible outputs
        completed = set()
        storage = {}
        for substate, entry in self.substates():
            child_hash = substate.hash()
            if child_hash not in completed:
                completed.add(child_hash)
                sub_result = substate.tree(not maximizer)

                # Remove any options that don't block opponents auto win.
                if not isinstance(sub_result, dict):
                    if sub_result.turns == 1:
                        continue

                name = f"{entry[0][0]}_{entry[1][0]}_{entry[1][1]}"
                storage[name] = sub_result

        # Flatten inevitable ties
        for k, v in storage.items():
            if isinstance(v, dict) or int(v) != 0:
                return storage
        else:
            return value


def deserialize(node):
    if isinstance(node, dict):
        return {k: deserialize(v) for k, v in node.items()}
    return int(node)


if __name__ == "__main__":
    # Create state analysis engine
    game = udebs.battleStart(game_config, field=TicTacToe)

    with udebs.Timer():
        tree = game.tree()

    # Save tree
    with open("../tictactoe.json", "w+") as f:
        json.dump(deserialize(tree), f)
