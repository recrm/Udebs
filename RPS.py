import udebs
import random
import sys

xml = """
<udebs>

<definitions>
    <strings>
        <beats />
        <played />
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
            <i>user played REPLACE CHOICE.user</i>
            <i>computer played REPLACE CHOICE.computer</i>
            <i>print "computer plays" computer.STAT.played</i>
            <i>user CAST computer victory</i>
            <i>computer CAST user victory</i>
            <i>user CAST computer tie</i>
            <i>INIT gameover</i>
        </effect>
    </rps>

    <victory>
        <require>($caster.STAT.played STAT beats) == $target.STAT.played</require>
        <effect>
            <i>print $caster "wins!!!"</i>
            <i>$target lives CHANGE -1</i>
            <i>print $target "has lost a life"</i>
        </effect>
    </victory>

    <tie>
        <require>$target.STAT.played == $caster.STAT.played</require>
        <effect>print "There was a tie"</effect>
    </tie>

    <gameover>
        <require>(user.STAT.lives * computer.STAT.lives) &lt;= 0</require>
        <effect>
            <i>print "The game is over"</i>
            <i>EXIT</i>
        </effect>
    </gameover>

    <!-- Game unit groups -->
    <action/>

    <character>
        <lives>5</lives>
    </character>

    <!-- Legal actions -->
    <rock>
        <beats>scissors</beats>
        <group>action</group>
    </rock>

    <paper>
        <beats>rock</beats>
        <group>action</group>
    </paper>

    <scissors>
        <beats>paper</beats>
        <group>action</group>
    </scissors>

    <!-- Players -->
    <user>
        <group>character</group>
    </user>

    <computer>
        <group>character</group>
    </computer>

</entities>

</udebs>
"""

game = None

def choice(target):
    if target == "user":
        choice = input("What will you play? ")
        while choice not in game.getGroup('action'):
            choice = input("That is not a valid action. Try again. ")
    else:
        choice = random.choice(['rock', 'paper', 'scissors'])

    return choice

def exit():
    sys.exit()

module = {
    "CHOICE": {
        "f": "choice",
        "args": ["$1"],
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
