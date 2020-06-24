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
    <seed>4643</seed>
    <name>life</name>
    <immutable>True</immutable>
</config>

<definitions>
    <stats>
        <NBR />
        <LIFE />
    </stats>

    <lists>
        <save />
    </lists>
</definitions>

<maps>
    <map type="diag">
        <dim>
            <x>50</x>
            <y>50</y>
        </dim>
    </map>
</maps>

<entities>

    <!-- Objects -->
    <cell immutable="False" />

    <change>
        <effect>
            <i>neighbors = FILL.$target.empty.false.1</i>
            <i>DELAY `(tick save GETS $neighbors) 0</i>
        </effect>
    </change>

    <!-- Life -->
    <life>
        <group>change</group>
        <require>$target.STAT.LIFE == 0</require>
        <effect>
            <i>$target LIFE REPLACE 1</i>
            <i>DELAY `($neighbors NBR += 1) 0</i>
        </effect>
    </life>

    <auto_life>
        <group>life</group>
        <require>$target.STAT.NBR == 3</require>
    </auto_life>

    <random_life>
        <group>life</group>
        <require>DICE.4 == 0</require>
        <effect>tick save GETS $target.LOC</effect>
    </random_life>

    <!-- Death -->
    <death>
        <group>change</group>
        <require>
            <i>$target.STAT.LIFE == 1</i>
            <i>($target.STAT.NBR &lt; 2) or ($target.STAT.NBR &gt; 3)</i>
        </require>
        <effect>
            <i>$target LIFE REPLACE 0</i>
            <i>DELAY `($neighbors NBR -= 1) 0</i>
        </effect>
    </death>

    <!-- Scripts -->
    <init>
        <effect>
            <i>all = (FILL (1 1) empty)</i>
            <i>cell RECRUIT $all</i>
            <i>CAST $all random_life</i>
        </effect>
    </init>

    <tick immutable="False">
        <effect>
            <i>all = (dedup $move.STAT.save)</i>
            <i>CAST $all death</i>
            <i>CAST $all auto_life</i>
            <i>tick CLEAR save</i>
        </effect>
    </tick>
</entities>
</udebs>
"""


def redraw_board(surface2, ts2):
    surface2.fill((0, 0, 0))
    for target in main_map.mapIter():
        if main_map.getStat(target, "LIFE"):
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
    for main_map in field.gameLoop():
        redraw_board(surface, ts)
        mainClock.tick(10)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                main_map.exit()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    main_map.increment = 0 if main_map.increment == 1 else 1

                if event.key == pygame.K_DELETE:
                    main_map.next = udebs.battleStart(game_config, seed=seed)
                    main_map.next.increment = main_map.increment

                elif main_map.increment == 0:
                    # Step back one step
                    if event.key == pygame.K_LEFT:
                        test = main_map.getRevert(1)
                        if test:
                            main_map.next = test
                            main_map.next.increment = 0

                    # Step forward one step
                    if event.key == pygame.K_RIGHT:
                        main_map.controlTime(1)
