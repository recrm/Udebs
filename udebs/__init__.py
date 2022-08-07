try:
    from udebs.loadxml import battleStart, battleWrite
except ModuleNotFoundError:
    pass

from udebs.interpret import register, importModule
from udebs.utilities import *
from udebs.errors import *
from udebs.instance import Instance
from udebs.entity import Entity
from udebs.board import Board
