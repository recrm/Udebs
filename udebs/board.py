from collections.abc import MutableMapping
from typing import Self
from abc import ABC, abstractmethod

from udebs.entity import FullEntity


class Location:
    def __init__(self, loc):
        self.loc = loc

    def __iter__(self):
        yield self

    def __str__(self):
        return f"<LOC {self.loc}>"

    def __repr__(self):
        return str(self)


FullLocation = Location | list[Location] | FullEntity


class Board(MutableMapping, ABC):
    def __init__(self, name, empty, *args, overwrite_map=None, **kwargs):
        self.name = name
        self.empty = empty
        if overwrite_map is None:
            self.map = self.populate_map(empty, *args, **kwargs)
        else:
            self.map = overwrite_map

    def __eq__(self, other) -> bool:
        if not type(self) is type(other):
            return False

        if self.name == other.name:
            if self.map == other.map:
                return True

        return False

    def __copy__(self) -> Self:
        return self.copy()

    def __repr__(self) -> str:
        return "<board: " + self.name + ">"

    def show(self) -> None:
        print(self.map)

    def test_loc(self, loc: tuple) -> bool:
        """
        Test to see if given location is a prt of this map.

        loc - Starting loc

        """
        if loc:
            try:
                self[loc]
                return True
            except IndexError:
                pass

        return False

    @abstractmethod
    def populate_map(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def copy(self) -> Self:
        raise NotImplementedError

    @abstractmethod
    def travel(self, obj: str, location: tuple):
        raise NotImplementedError
