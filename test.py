import udebs

main_map = udebs.battleStart("test.xml")

main_map.controlMove('empty', 'empty', 'init', 4)
main_map.controlTime(4)

main_map.controlMove('token1', 'spark1', 'everything')

print(main_map.getStat('token', 'ACT') == 17, 1)
print(len(main_map.getStat((0,5), 'movelist')) == 7, 2)
print(main_map.getStat(main_map.objects['token'], 'sprite') == 'K', 3)

print(main_map.getMap((0,5)) == 'token1', 4)
print(main_map.getMap((9,9)) == False, 5)
print(main_map.getMap((0,4)) == 'empty', 6)



print(main_map.getDistance('token1', 'spark1', 'x') == 0, 7)
print(main_map.getDistance(main_map.objects['token1'], 'empty', 'hex') == float('inf'), 8)
print(main_map.getDistance((0,5), 'spark1', 'travel') == 5, 9)

print(len(main_map.getFill((0,3), 'travel')) == 22, 10)

print(main_map.getListStat('token', 'movelist', 'ACT') == 8, 12)
print(main_map.getListGroup('token', 'movelist', 'all_group') == 'spark', 13)
print(len(main_map.getGroup('all_group')) == 4, 14)

