from udebs import *

battle = battleStart('rpg.xml')

battle.controlStat('treasure', 'LVL', 1)

for i in range(50):
    battle.controlMove('treasure', 'party', 'get_item')
    

