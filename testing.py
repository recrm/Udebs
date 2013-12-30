import udebs
import unittest
import sys

xml_test = """
<udebs>
<config>
    <compile>False</compile>
    <hex>True</hex>
    <name>testing</name>
    <logging>False</logging>
</config>
<definitions>
    <stats>
        <ACT />
    </stats>
    <strings>
        <DESC />
    </strings>
    <lists>
        <equipment slist="equip" />
        <inventory rlist='' />
    </lists>
</definitions>
<maps>
    <one rmap=''>
        <dim>
            <x>4</x>
            <y>4</y>
        </dim>
    </one>
    <two>
        <row>unit1, unit2</row>
        <row>empty, empty</row>
    </two>
    <map>
        <dim>
            <x>4</x>
            <y>4</y>
        </dim>
    </map>
        
</maps>
<var>
    <time>4</time>
    <log>
        <i>This is a log entry</i>
        <i>This is another log entry</i>
    </log>
</var>
<entities>
    <unit1>
        <group>
            <i>group1</i>
        </group>
        <ACT>5</ACT>
        <inventory>
            <i>move1</i>
        </inventory>
    </unit1>
    <unit2 />
    <move1>
        <ACT>5</ACT>
        <equipment>1</equipment>
    </move1>
    <group1>
        <ACT>5</ACT>
        <equipment>1</equipment>
    </group1>
</entities>
</udebs>




"""

class TestBattleStart(unittest.TestCase):

    def setUp(self):
        self.test1 = udebs.battleStart(xml_test)
        
    def test_config(self):
        self.assertFalse(self.test1.django)
        self.assertTrue(self.test1.hex)
        self.assertFalse(self.test1.compile)
        self.assertFalse(self.test1.logging)
        self.assertEqual(self.test1.name, "testing")
        
    def test_definitions(self):
        self.assertIn("ACT", self.test1.stats)
        self.assertIn("DESC", self.test1.strings)
        self.assertIn("equipment", self.test1.lists)
        self.assertIn("inventory", self.test1.rlist)
        self.assertIn("equipment", self.test1.slist)
        self.assertEqual("equip", self.test1.slist["equipment"])
        total = sum([len(self.test1.lists), len(self.test1.stats), len(self.test1.strings)])
        #four defined stats + four built in stats.
        self.assertEqual(total, 8)
        
    def test_map(self):
        self.assertEqual(len(self.test1.map), 3)
        self.assertIsInstance(self.test1.map['two'], udebs.board)
        self.assertEqual(self.test1.map['one'].x(), 4)
        self.assertEqual(self.test1.map['two'].y(), 2)
        
    def test_var(self):
        self.assertEqual(self.test1.time, 4)
        self.assertEqual(len(self.test1.log), 2)
        #delay not tested yet.
        
    def test_entity(self):
        #four defined plus one built in.
        self.assertEqual(len(self.test1.data), 5)
        self.assertEqual(len(self.test1.data["unit1"].group), 2)
        
        stats = self.test1.strings.union(self.test1.stats, self.test1.lists)
        for value in self.test1.data.values():
            for stat in stats:
                self.assertTrue(hasattr(value, stat))
                
class TestBattleWrite(unittest.TestCase):
    def setUp(self):
        self.env1 = udebs.battleStart(xml_test)
        udebs.battleWrite(self.env1, "/tmp/udebs_testing.xml", True)
        self.env2 = udebs.battleStart("/tmp/udebs_testing.xml")
        
    def test_equal(self):
        self.assertEqual(self.env1.django, self.env2.django)
        self.assertEqual(self.env1.compile, self.env2.compile)
        self.assertEqual(self.env1.hex, self.env2.hex)
        self.assertEqual(self.env1.name, self.env2.name)
        self.assertEqual(self.env1.lists, self.env2.lists)
        self.assertEqual(self.env1.stats, self.env2.stats)
        self.assertEqual(self.env1.strings, self.env2.strings)
        self.assertEqual(self.env1.slist, self.env2.slist)
        self.assertEqual(self.env1.rlist, self.env2.rlist)
        self.assertEqual(self.env1.rmap, self.env2.rmap)
        self.assertEqual(self.env1.time, self.env2.time)
        self.assertEqual(self.env1.delay, self.env2.delay)
        self.assertEqual(self.env1.map.keys(), self.env2.map.keys())
        self.assertEqual(self.env1.log, self.env2.log)
        #test maps
        self.assertEqual(len(self.env1.map), len(self.env2.map))
        for map_ in self.env1.map.keys():
            self.assertEqual(
                self.env1.map[map_].map,
                self.env2.map[map_].map 
            )
        
        
    #need to test entity, and map objects.
        
#battleWrite not tested yet.

class TestBoardClass(unittest.TestCase):
    def setUp(self):
        self.test1 = udebs.battleStart(xml_test)
        self.one = self.test1.map["one"]
        self.two = self.test1.map["two"]
    
    def test_size(self):
        self.assertEqual(self.one.y(), 4)
        self.assertEqual(self.two.x(), 2)
        self.assertEqual(self.one.size(), 16)
    
    def test_get(self):
        self.assertEqual("unit1", self.two.get((0,0)))
        self.assertFalse(self.two.get((3,3)))
        self.assertFalse(self.one.get((-1, 0)))
        self.assertFalse(self.one.get(False))
        
    def test_find(self):
        self.assertEqual(self.two.find("unit2"), (1,0, "two"))
        self.assertFalse(self.one.find("unit1"))
        p = self.two.find("unit2")
        self.assertEqual("unit2", self.two.get(p))
    
    def test_insert(self):
        self.one.insert("unit1", (0,0))
        self.assertEqual(self.one.get((0,0)), "unit1")
        self.assertEqual(self.one.get((1,0)), "empty")
        with self.assertRaises(Exception):
            self.two.insert("unit1", (3,3))
        with self.assertRaises(Exception):
            self.two.insert("unit1", (-1,0))
            
class TestEntityClass(unittest.TestCase):
    def setUp(self):
        self.env = udebs.battleStart(xml_test)
        self.unit = self.env.data["unit1"]
        
    def test_init(self):
        new = udebs.entity(self.env)
        self.assertIn(new.name, new.group)
        stats = self.env.strings.union(self.env.stats, self.env.lists)
        for stat in stats:
            self.assertTrue(hasattr(new, stat))
                        
    def test_update(self):
        self.assertEqual(self.unit.loc, (0,0,"two"))
        store = self.unit.loc
        self.unit.loc = False
        self.unit.update(self.env)
        self.assertEqual(store, self.unit.loc)
        
    def test_record(self):
        new = udebs.entity(self.env)
        new.name = "new"
        new.record(self.env)
        self.assertIn("new", self.env.data)

class TestInstanceClass(unittest.TestCase):
    def setUp(self):
        self.env = udebs.battleStart(xml_test)
        
    def test_getObject(self):
        self.assertEqual(len(self.env.getObject()), 5)
        self.assertIs(self.env.getObject("unit1"), self.env.data["unit1"])
        with self.assertRaises(udebs.UndefinedEntityError):
            self.env.getObject("error")
            
    def test_getStat(self):
        self.assertEqual(self.env.getStat("unit1", "ACT"), 15)
        self.env.map["one"].insert("move1", (0,0))
        self.assertEqual(self.env.getStat("unit1", "ACT"), 20)
        self.assertEqual(len(self.env.getStat("unit1", "equipment")), 3)
        with self.assertRaises(udebs.UndefinedStatError):
            self.env.getStat('unit1', "Not Defined")
            
    def test_testTarget(self):
        test = self.env.getObject("unit1")
        t = self.env.getTarget
        self.assertEqual(t(test), test)
        self.assertEqual(t("unit1"), test)
        self.assertEqual(t((0,0,"two")), test)
        self.assertEqual(t(["unit1"]), [test])
        self.assertEqual(t((0,0)).loc, (0,0, 'map'))
       
    def test_controlTravel(self):
        self.env.controlTravel("unit1", (0,0, "one"))
        self.assertEqual(self.env.getMap((0,0, "one")), "unit1")
        self.assertEqual(self.env.getMap((0,0, "two")), "empty")
        
        self.env.controlTravel("unit1", 'bump')
        self.assertEqual(self.env.getMap((0,0, "one")), "empty")
        self.assertFalse(self.env.getLocation("unit1"))
        
        self.env.controlTravel("unit1", (0,0))
        self.assertEqual(self.env.getMap((0,0, 'map')), "unit1")
        self.assertEqual(self.env.getMap((0,0)), "unit1")
            
        
        
        
        
if __name__ == '__main__':
    unittest.main()
