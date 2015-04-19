#python3 -m cProfile -o output river.py && python3 udebs/profile.py > output.txt
"""This is just a quick script to help me profile Udebs."""

import pstats
import os

p = pstats.Stats('output')
p.strip_dirs().sort_stats('time', 'cumulative').print_stats()
os.remove('output')
