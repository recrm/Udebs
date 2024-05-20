import random
from typing import Self
import json

from udebs.board import Board
from udebs.interpret import register


class CardStack(Board):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._len = 0

    def populate_map(self, empty, players, spaces):
        data = {}
        for player in players:
            data[player] = {}
            for space in spaces:
                data[player][space] = []

        return data

    def __getitem__(self, key: tuple) -> list[str]:
        player, space = key[0], key[1]
        if len(self.map[player][space]) == 0:
            return self.empty

        return self.map[player][space][-1]

    def __setitem__(self, key: tuple, value: str) -> None:
        if value == self.empty:
            return

        player, space = key[0], key[1]
        self.map[player][space].append(value)
        self._len += 1

    def __delitem__(self, key: tuple) -> None:
        player, space = key[0], key[1]
        if len(key) > 2 and key[2] != self.name:
            self.map[player][space].remove(key[2])
        else:
            self.map[player][space].pop()

        self._len -= 1

    def __iter__(self):
        for player, spaces in self.map.items():
            for space, values in spaces.items():
                for value in values:
                    yield player, space, value, self.name

    def __len__(self):
        return self._len

    def travel(self, obj, location):
        self[location[0], location[1]] = obj
        return (location[0], location[1], obj, self.name), None

    def copy(self) -> Self:
        new = {}
        for player, spaces in self.map.items():
            new[player] = {}
            for space, values in spaces.items():
                new[player][space] = values[:]

        return CardStack(self.name, overwrite_map=new)

    # ---------------------------------------------------
    #                    Methods                        -
    # ---------------------------------------------------
    def shuffle(self, loc, rand: random.Random):
        player, space = loc[0], loc[1]
        rand.shuffle(self.map[player][space])


@register({"args": ["self", "$1"]}, name="CARD_SHUFFLE")
def card_shuffle(state, loc):
    map_ = state.getMap(loc)
    map_.shuffle(loc.loc, state.rand)


@register({"args": ["self", "-$1", "$1", "$2"]}, name="DEAL")
def card_deal(state, deck, target, amount):
    for i in range(amount):
        caster = state.getEntity(deck)
        state.controlTravel(caster, target)


@register({"args": ["self", "$1"]}, name="SIZE")
def card_size(state, loc):
    return len(state.getMap(loc).map[loc.loc[0]][loc.loc[1]])


@register({"args": ["self", "$1"]}, name="SPACE")
def card_space(state, loc):
    return state.getMap(loc).map[loc.loc[0]][loc.loc[1]]
