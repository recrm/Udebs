import udebs
import random
import sys

xml = """
<udebs>

<config>
    <name>Gameboard</name>
    <version>2</version>
</config>


<!-- definitions -->
<definitions>
    <stats>
        <lvl />
    </stats>
</definitions>

<maps>
    <p_one>
        <dim>
            <x>5</x>
            <y>5</y>
        </dim>
    </p_one>
    
    <p_two>
        <dim>
            <x>5</x>
            <y>5</y>
        </dim>
    </p_two>
    
    <map rmap=''>
        <dim>
            <x>5</x>
            <y>5</y>
        </dim>
    </map>
</maps>

<entities>
    <!-- Immutable object -->
    
    <one immutable=''>
        <lvl>1</lvl>
    </one>
    
    <two immutable=''>
        <lvl>2</lvl>
    </two>
    
    <three immutable=''>
        <lvl>3</lvl>
    </three>
    
    <four immutable=''>
        <lvl>4</lvl>
    </four>
    
    <five immutable=''>
        <lvl>5</lvl>
    </five>
        
    <!-- Scripts -->
    <hori>
        <require>DISTANCE.x == 0</require>
    </hori>

    <init>
        <effect>
            <i>one MOVE (FILL (0 0) hori)</i>
            <i>two MOVE (FILL (1 0) hori)</i>
            <i>three MOVE (FILL (2 0) hori)</i>
            <i>four MOVE (FILL (3 0) hori)</i>
            <i>five MOVE (FILL (4 0) hori)</i>
        </effect>
    </init>
    
    <!-- Units -->
    <token />
    
</entities>
</udebs>
"""

#module = {
#    "CHOICE": {
#        "f": "choice",
#        "args": ["$1", "self"],
#    },
#    "EXIT": {
#        "f": "exit",
#    },
#}
#udebs.importModule(module, {"choice": choice, "exit": exit})

game = udebs.battleStart(xml)
game.controlInit("init")
game.controlInit("token MOVE (4 0 p_one)")

print(game.getStat("token", "lvl"))

#for _map in game.map:
#    print(_map._map)

#while True:
#    game.controlInit("rps")
#    print()
