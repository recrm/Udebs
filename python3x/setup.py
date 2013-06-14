import sys
from cx_Freeze import setup, Executable

setup(
    name = "Zanar2",
    version = '0.1',
    description = "Simple RPG tech Demo",
    executables = [Executable('zanar2.py')]
)
