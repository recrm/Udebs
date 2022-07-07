try:
    from udebs.loadxml import battleStart, battleWrite
except ModuleNotFoundError:
    pass

from udebs.interpret import importModule, importFunction
from udebs.utilities import *
from udebs.errors import *
from udebs.instance import Instance
