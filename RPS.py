#!/usr/bin/env python3
import udebs
import random
import sys

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
    <version>2</version>
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
            <i>INIT gameover</i>
        </effect>
    </tick>
    
    <rps>
        <effect>
            <i>print "You have" user.STAT.lives lives</i>
            <i>print "Your opponent has" computer.STAT.lives lives</i>
            <i>user = (CHOICE_H)</i>
            <i>computer = (CHOICE_C)</i>
            <i>print you played $user</i>
            <i>print your opponent played $computer</i>
            <i>user lives += LOOKUP.$user.$computer</i>
            <i>computer lives += LOOKUP.$computer.$user</i>
        </effect>
    </rps>

    <gameover>
        <require>(user.STAT.lives * computer.STAT.lives) &lt;= 0</require>
        <effect>
            <i>print The game is over</i>
            <i>EXIT</i>
        </effect>
    </gameover>

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

class Random(udebs.Player):
    def __call__(self, state):
        return random.choice(["rock", "paper", "scissors", "cooperate"])

class Human(udebs.Player):
    def __call__(self, state):
        x = input("what do you play? ")
        while x not in ["rock", "paper", "scissors", "cooperate"]:
            x = input("try again")

        return x

if __name__ == "__main__":
    Random("CHOICE_C")
    Human("CHOICE_H")
    udebs.lookup("LOOKUP", {
        "rock": {"paper": -1},
        "paper": {"scissors": -1},
        "scissors": {"rock": -1},
    })

    game = udebs.battleStart(xml)
    for i in game.gameLoop():
        pass
