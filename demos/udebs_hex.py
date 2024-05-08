#!/usr/bin/env python3
import itertools
import math
import sys
from collections import Counter

import udebs
from udebs.treesearch import AlphaMontyCarlo

try:
    import pygame
except ImportError:
    print("This udebs demo requires pygame to be installed.")
    sys.exit()

hexes = 13

game_config = f"""
<udebs>

<config>
    <name>hex</name>
    <immutable>True</immutable>
    <logging>False</logging>
</config>

<definitions>
    <stats>
        <ACT />
    </stats>
    <strings>
        <STONE />
        <walla />
        <wallb />
    </strings>
</definitions>

<map type='hex'>
    <dim>
        <x>{hexes}</x>
        <y>{hexes}</y>
    </dim>
</map>

<entities>

    <player />

    <w><STONE>o</STONE></w>
    <b><STONE>*</STONE></b>

    <white immutable="False">
        <STONE>w</STONE>
        <ACT>2</ACT>
        <group>player</group>
    </white>

    <black immutable="False">
        <STONE>b</STONE>
        <ACT>1</ACT>
        <group>player</group>
    </black>

    <!-- scripts -->
    <init>
        <effect>
            <i>#(#white.STAT.STONE) MOVE (FILL (0 0) `(DISTANCE.y == 0))</i>
            <i>#(#white.STAT.STONE) MOVE (FILL (0 {hexes - 1}) `(DISTANCE.y == 0))</i>
            <i>#(#black.STAT.STONE) MOVE (FILL (0 0) `(DISTANCE.x == 0))</i>
            <i>#(#black.STAT.STONE) MOVE (FILL ({hexes - 1} 0) `(DISTANCE.x == 0))</i>

            <i>#empty MOVE (0 0)</i>
            <i>#empty MOVE (0 {hexes - 1})</i>
            <i>#empty MOVE ({hexes - 1} {hexes - 1})</i>
            <i>#empty MOVE ({hexes - 1} 0)</i>

            <i>#white walla REPLACE ({int(hexes / 2)} 0 map)</i>
            <i>#white wallb REPLACE ({int(hexes / 2)} {hexes - 1} map)</i>
            <i>#black walla REPLACE (0 {int(hexes / 2)} map)</i>
            <i>#black wallb REPLACE ({hexes - 1} {int(hexes / 2)} map)</i>
        </effect>
    </init>

    <turn>
        <require>$caster.STAT.ACT &gt;= 2</require>
        <effect>
            <i>$caster ACT -= 2</i>
            <i>ALL.player ACT += 1</i>
        </effect>
    </turn>

    <check_win>
        <effect>CAST $target #win</effect>
    </check_win>

    <win>
        <require>PATH `($target.NAME == $caster.NAME) $caster.STAT.walla $caster.STAT.wallb</require>
        <effect>
            <i>print game over</i>
            <i>EXIT $caster.NAME</i>
        </effect>
    </win>

    <place>
        <require>$target.NAME == empty</require>
        <effect>#($caster.STAT.STONE) MOVE $target</effect>
    </place>

    <placement>
        <group>
            <i>place</i>
            <i>turn</i>
            <i>check_win</i>
        </group>
    </placement>

    <ai>
        <require>
            <i>loc = #(Cplayer)</i>
            <i>CAST $loc #placement</i>
        </require>
    </ai>

</entities>

</udebs>
"""


class Hexagon:
    def __init__(self, a, b, ts2):
        rad = math.cos(math.pi / 6)
        self.center = (int(ts2 * (2 * a + b + 1.5)), int(ts2 * (1.5 * b / rad + 1.5)))
        self.points = []

        length = ts2 / rad
        for i in range(6):
            angle = i * math.pi / 3
            x2 = self.center[0] + length * math.sin(angle)
            y2 = self.center[1] + length * math.cos(angle)
            self.points.append((int(x2), int(y2)))

        self.square = pygame.Rect(0, 0, int(ts2 * 1.5), int(ts2 * 1.5))
        self.square.center = self.center


def event_update(main_map2, main_surface2, main_font2):
    # redraw the board
    main_surface2.fill((0, 0, 0))
    for x2, y2 in itertools.product(range(hexes), range(hexes)):
        hexagon = Hexagon(x2, y2, ts)
        pygame.draw.polygon(main_surface2, (255, 255, 255), hexagon.points, 0)
        pygame.draw.polygon(main_surface2, (0, 0, 0), hexagon.points, 1)

        unit = main_map2.getName(main_map.getEntity((x2, y2, 'map')))
        if unit != 'empty':
            char = main_map2.getStat(main_map[unit], "STONE")
            main_surface2.blit(main_font2.render(char, True, (0, 0, 0)), hexagon.square)

    pygame.display.update()


class Hex(AlphaMontyCarlo):
    wwalla = {(i, 0, "map") for i in range(hexes)}
    wwallb = {(i, hexes - 1, "map") for i in range(hexes)}
    bwalla = {(0, i, "map") for i in range(hexes)}
    bwallb = {(hexes - 1, i, "map") for i in range(hexes)}

    def shuffle(self, map_, stone):
        def wrapped(value):
            new = [i for i in value if map_[i] == stone]
            self.rand.shuffle(new)
            return new

        return wrapped

    def legalMoves(self):
        player2 = "white" if self.time % 2 == 0 else "black"
        for i, v in self.getMap().items():
            if v == "empty":
                if 0 not in i:
                    if hexes - 1 not in i:
                        yield player2, i, "place"

    # ---------------------------------------------------
    #                    Solvers                       -
    # ---------------------------------------------------
    def simulate(self, white=True, iterations=100):
        clone = self.copy()
        _map = clone.getMap()
        wshuffle = clone.shuffle(_map, "w")
        bshuffle = clone.shuffle(_map, "b")

        choices = list(i[1] for i in clone.legalMoves())
        half = len(choices) / 2

        policy = Counter()
        wins = 0
        for __ in range(iterations):
            # Play out a random game
            clone.rand.shuffle(choices)
            for i, loc2 in enumerate(choices):
                _map[loc2] = "w" if i <= half else "b"

            # detect who won and record winning path
            path = _map.getPath(self.wwalla, self.wwallb, sort=wshuffle)
            if not path:
                path = _map.getPath(self.bwalla, self.bwallb, sort=bshuffle)
                if not white:
                    wins += 1
            else:
                if white:
                    wins += 1

            policy.update(path)

        total = sum(policy.values())
        return wins / iterations, {i: v / total for i, v in policy.items()}


class Cplayer:
    def __init__(self, iterations=100, think_time2=30):
        self.tree = None
        self.iterations = iterations
        self.think_time = think_time2

    def __call__(self, state):
        # Check for reusable portions of previous trees.
        if self.tree is None:
            self.tree = state.copy(Hex())
            self.tree.init()
        else:
            map_ = state.getMap()
            self.tree = self.tree.select(lambda x2: map_[x2.entry[1]] != "empty")

        # Run monty carlo search algorithm several times.
        self.tree.think(self.think_time)

        def selector(x2):
            return x2.n / x2.prior if x2.prior > 0 else 0

        # Print out some useful data
        print("loc", "n_searches", "prior", "weight")
        test = sorted(self.tree.children, key=selector, reverse=True)
        for i in test[:10]:
            if i.n > 0:
                print(i.entry[1], i.n, round(i.prior, 3), round(1 - (i.v / i.n), 3))

        # select a node
        self.tree = self.tree.select(selector)

        # return location
        return self.tree.entry[1]


if __name__ == "__main__":
    print("""Welcome to Hex: a simple Hex ai build with udebs!
    controls:

    Human plays as white and goes first. Click on the hex you want to place a stone in.
    By default the cpu is allowed to "think" for 10 seconds before making a move. This can be changed
    by giving the program an integer command line argument.
    """)

    try:
        think_time = int(sys.argv[1])
    except IndexError:
        think_time = 10

    # definitions
    ts = 15

    # Setup pygame
    pygame.init()
    main_font = pygame.font.SysFont(None, 40)
    main_surface = pygame.display.set_mode((ts * hexes * 3, ts * hexes * 2), 0, 32)
    pygame.display.set_caption('A simple hex AI')
    mainClock = pygame.time.Clock()

    # Setup udebs
    comp = Cplayer(iterations=100, think_time2=think_time)
    udebs.register_raw(comp, {"args": ["self"]}, name="Cplayer")
    main_map = udebs.battleStart(game_config)

    # game loop
    event_update(main_map, main_surface, main_font)

    player = "human"
    while main_map:
        loc = None

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                main_map.exit()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse = pygame.mouse.get_pos()
                for x, y in itertools.product(range(1, hexes - 1), range(1, hexes - 1)):
                    if Hexagon(x, y, ts).square.collidepoint(*mouse):
                        loc = (x, y)
                        break

        if player == "computer":
            print("computer is thinking")
            if main_map.castAction("black", "ai"):
                main_map.controlTime()
                event_update(main_map, main_surface, main_font)
                player = "human"

        elif player == "human" and loc:
            if main_map.castMove("white", (loc[0], loc[1]), 'placement'):
                main_map.controlTime()
                event_update(main_map, main_surface, main_font)
                player = "computer"

        mainClock.tick(15)

    input("press button to quit")
    pygame.quit()
