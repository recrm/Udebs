#!/usr/bin/env python3
import sys

import udebs

try:
    import pygame
except ImportError:
    print("This udebs demo requires pygame to be installed.")
    sys.exit()

game_config = """
<udebs>

<config>
    <revert>10</revert>
    <logging>False</logging>
    <name>life</name>
    <immutable>True</immutable>
</config>

<definitions>
    <stats>
        <NBR />
        <LIFE />
    </stats>
</definitions>

<maps>
    <map type="diag">
        <dim>
            <x>100</x>
            <y>100</y>
        </dim>
    </map>
</maps>

<entities>

    <!-- Objects -->
    <cell immutable="False" />
    <cells />

    <!-- Life -->
    <base_life>
        <require>$target.STAT.LIFE.false == 0</require>
        <effect>
            <i>$target LIFE REPLACE 1</i>
            <i>DELAY `(#(CONSTANT #(FILL $target None false 1).NAME $target.NAME) NBR += 1) 0</i>
        </effect>
    </base_life>

    <auto_life>
        <group>base_life</group>
        <require>$target.STAT.NBR.False == 3</require>
    </auto_life>

    <random_life>
        <group>base_life</group>
        <require>DICE.4 == 0</require>
    </random_life>

    <!-- Death -->
    <base_death>
        <require>$target.STAT.LIFE.False == 1</require>
        <effect>
            <i>$target LIFE REPLACE 0</i>
            <i>DELAY `(#(CONSTANT #(FILL $target None false 1).NAME $target.LOC) NBR -= 1) 0</i>
        </effect>
    </base_death>

    <auto_death>
        <group>base_death</group>
        <require>
            <i>nbr = $target.STAT.NBR.false</i>
            <i>`($nbr &lt; 2) OR `($nbr > 3)</i>
        </require>
    </auto_death>

    <!-- Scripts -->
    <init>
        <effect>
            <i>all = FILL.(1 1)</i>
            <i>#cell RECRUIT $all</i>
            <i>#$all group GETS cells</i>
            <i>CAST #$all #random_life</i>
        </effect>
    </init>

    <tick>
        <effect>CAST ALL.cells `(
            IF $target.STAT.LIFE.false 
            `(CAST $target #auto_death) 
            `(CAST $target #auto_life)
        )</effect>
    </tick>

    <reset>
        <effect>
            <i>all = ALL.cells</i>
            <i>$all NBR REPLACE 0</i>
            <i>$all LIFE REPLACE 0</i>
            <i>CAST $all #random_life</i>
        </effect>
    </reset>

    <clear>
        <effect>
            <i>all = ALL.cells</i>
            <i>$all NBR REPLACE 0</i>
            <i>$all LIFE REPLACE 0</i>
        </effect>
    </clear>

    <manual_change>
        <effect>IF $target.STAT.LIFE.false `(CAST $target #base_death) `(CAST $target #base_life)</effect>
    </manual_change>

</entities>
</udebs>
"""


def redraw_board(board, surface2, ts2):
    surface2.fill((0, 0, 0))
    for target in board.getMap():
        target = board.getEntity(target)
        if board.getStat(target, "LIFE"):
            rect = pygame.Rect(target.loc[0] * ts2, target.loc[1] * ts2, ts2, ts2)
            pygame.draw.rect(surface2, (100, 200, 100, 127), rect)

    pygame.display.update()


@udebs.register(["$1"])
def dedup(lst):
    return list(set(lst))


if __name__ == "__main__":
    print("""Welcome to Conway's game of life!!
    controls:

    Run this program with an integer argument to change the seed of the initial state.

    - spacebar - Pauses and unpause the game.
    - delete - Resets the game to it's starting state.
    - arrow right - While paused moves simulation ahead one generation.
    - arrow left - While paused moves simulation back one generation.
    """)

    try:
        seed = int(sys.argv[1])
    except IndexError:
        seed = None

    # State variables
    ts = 10
    field = udebs.battleStart(game_config, seed=seed)

    # Setup pygame
    pygame.init()
    pygame.display.set_caption("Conway's game of life.")
    surface = pygame.display.set_mode((ts * field.getMap().x, ts * field.getMap().y), 0, 32)
    mainClock = pygame.time.Clock()

    # game loop
    for main_map in field.gameLoop(1):
        redraw_board(main_map, surface, ts)
        # mainClock.tick(10)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                main_map.exit()
                pygame.quit()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    main_map.increment = not main_map.increment

                elif event.key == pygame.K_DELETE:
                    main_map.next = main_map.resetState()

                # Step back one step
                elif event.key == pygame.K_LEFT and main_map.increment == 0:
                    main_map.next = main_map.getRevert(1)

                # Step forward one step
                elif event.key == pygame.K_RIGHT and main_map.increment == 0:
                    main_map.controlTime(1)
