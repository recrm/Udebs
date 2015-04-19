import udebs
import random
import sys

xml = """
<udebs>

<definitions>
    <strings>
        <beats />
    </strings>
    <stats>
        <lives />
    </stats>
</definitions>

<config>
    <version>2</version>
    <logging>False</logging>
</config>

<entities>
    <rps>
        <effect>
            <i>print "You have" user.STAT.lives lives</i>
            <i>print "Your opponent has" computer.STAT.lives lives</i>
            <i>user = CHOICE.human</i>
            <i>computer = CHOICE.computer</i>
            <i>print "computer plays" $computer</i>
            <i>winner =
                (if ($user.STAT.beats == $computer)
                    user
                    computer)</i>
            <i>losser =
                (if ($winner == $user)
                    computer
                    user)</i>
            <i>CAST $winner victory</i>
            <i>CAST $losser defeat</i>
            <i>INIT gameover</i>
        </effect>
    </rps>

    <gameover>
        <require>(user.STAT.lives * computer.STAT.lives) == 0</require>
        <effect>
            <i>print "The game is over"</i>
            <i>EXIT</i>
        </effect>
    </gameover>

    <victory>
        <effect>print $target "wins!!!"</effect>
    </victory>

    <defeat>
        <effect>
            <i>$target CHANGE lives -1</i>
            <i>print $target "has lost a life."</i>
        </effect>
    </defeat>

    <rock>
        <beats>scissors</beats>
    </rock>

    <paper>
        <beats>rock</beats>
    </paper>

    <scissors>
        <beats>paper</beats>
    </scissors>

    <character>
        <lives>5</lives>
    </character>

    <user>
        <group>character</group>
    </user>

    <computer>
        <group>character</group>
    </computer>

</entities>

</udebs>
"""

def choice(target, state):
    print("going into choice")
    if target == "human":
        choice = input("What will you play? ")
        while choice not in state.getGroup('action'):
            choice = input("That is not a valid action. Try again. ")
    else:
        choice = random.choice(['rock', 'paper', 'scissors'])

    return choice

def exit():
    sys.exit()

module = {
    "CHOICE": {
        "f": "choice",
        "args": ["$1", "self"],
    },
    "EXIT": {
        "f": "exit",
    },
}
udebs.importModule(module, {"choice": choice, "exit": exit})

game = udebs.battleStart(xml)

while True:
    game.controlInit("rps")
    print()
