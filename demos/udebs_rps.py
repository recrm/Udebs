#!/usr/bin/env python3
import udebs
import random

xml = """
<udebs>

<definitions>
    <stats>
        <lives />
        <power />
    </stats>
    <strings>
        <choice />
    </strings>
</definitions>

<config>
    <logging>False</logging>
    <auto_entity>False</auto_entity>
</config>

<entities>
    <rock>
        <power>0</power>
    </rock>
    <paper>
        <power>1</power>
    </paper>
    <scissors>
        <power>2</power>
    </scissors>
    
    <tick>
        <effect>
            <i>print You have #user.STAT.lives lives</i>
            <i>print Your opponent has #computer.STAT.lives lives</i>
            <i>#user choice REPLACE #(HUMAN)</i>
            <i>#computer choice REPLACE #(RANDOM)</i>
            <i>print you played #user.STAT.choice</i>
            <i>print your opponent played #computer.STAT.choice</i>
            <i>#user CAST #computer #death</i>
            <i>#computer CAST #user #death</i>
            <i>print ""</i>
        </effect>
    </tick>

    <death>
        <require>((($caster.STAT.choice STAT power) - ($target.STAT.choice STAT power)) % 3) == 1</require>
        <effect>
            <i>$target lives -= 1</i>
            <i>print $target has lost a life</i>
            <i>CAST $target #game_over</i>
        </effect>
    </death>

    <game_over>
        <require>$target.STAT.lives &lt;= 0</require>
        <effect>
            <i>print $target has 0 lives and died</i>
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


if __name__ == "__main__":
    print("""Welcome to rock paper scissors

    Simply type in your selection when prompted!
    """)
    game = udebs.battleStart(xml)
    for i in game.gameLoop():
        pass
