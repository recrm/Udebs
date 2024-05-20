try:
    # Web version of python doesn't support elementtree
    from udebs.loadxml import battleStart, battleWrite
except ModuleNotFoundError:
    pass

from udebs.interpret import register
from udebs.utilities import *
from udebs.errors import *
from udebs.instance import Instance
from udebs.entity import Entity
from udebs.board import Board
from udebs.modules import basic
