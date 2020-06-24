#!/usr/bin/env python3
import udebs
import random

xml = """
<udebs>

<definitions>
    <stats>
        <lives />
    </stats>
    <lists>
        <options />
    </lists>
</definitions>

<config>
    <logging>False</logging>
</config>

<entities>
    <tick>
        <options>
            <i>rock</i>
            <i>paper</i>
            <i>scissors</i>
        </options>
        <effect>
            <i>INIT rps</i>
            <i>INIT game_over</i>
        </effect>
    </tick>

    <rps>
        <effect>
            <i>print "You have" user.STAT.lives lives</i>
            <i>print "Your opponent has" computer.STAT.lives lives</i>
            <i>user = (HUMAN)</i>
            <i>computer = (RANDOM)</i>
            <i>print you played $user</i>
            <i>print your opponent played $computer</i>
            <i>user lives += LOOKUP.$user.$computer</i>
            <i>computer lives += LOOKUP.$computer.$user</i>
            <i>print ""</i>
        </effect>
    </rps>

    <game_over>
        <require>(user.STAT.lives * computer.STAT.lives) &lt;= 0</require>
        <effect>
            <i>print "You have" user.STAT.lives lives</i>
            <i>print "Your opponent has" computer.STAT.lives lives</i><i>print The game is over</i>
            <i>EXIT</i>
        </effect>
    </game_over>

    <!-- Players -->
    <user>
        <lives>5</lives>
    </user>

    <computer>
        <lives>5</lives>
    </computer>

</entities>

</udebs>
"""


@udebs.register([])
def RANDOM():
    return random.choice(["rock", "paper", "scissors"])


@udebs.register([])
def HUMAN():
    x = input("what do you play? ")
    while x not in ["rock", "paper", "scissors"]:
        x = input("Try again? ")

    return x


@udebs.register(["$1", "$2"])
def LOOKUP(one, two):
    data = {
        "rock": {"paper": -1},
        "paper": {"scissors": -1},
        "scissors": {"rock": -1},
    }
    return data.get(one, {}).get(two, 0)


if __name__ == "__main__":
    print("""Welcome to rock paper scissors

    Simply type in your selection when prompted!
    """)
    game = udebs.battleStart(xml)
    for i in game.gameLoop():
        pass
