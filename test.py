import udebs.xml

test = udebs.xml.read("xml/rpg.xml")
test.controlTime(5)
udebs.xml.write(test, "output.xml", True)

#Stuff I want to do

#Multi layered Maps
#immutable entities.
#Seperate into several files

