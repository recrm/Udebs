import pstats
p = pstats.Stats('output')
p.strip_dirs().sort_stats('time', 'cumulative').print_stats()
