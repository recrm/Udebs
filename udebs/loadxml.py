import copy
import re
import sys
import logging
from udebs import board, entity, instance, interpret
from xml.etree import ElementTree

#This is a pretty printing algorithm I stole from the internet.
def indent(elem, level=0):
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

#creates an xml file from instance object.
def battleWrite(env, location, pretty=False):
    """
    Writes an instance object to file.

    env - Instance object to write.
    location - Variable to pass to xml.etree.write.
    """
    e = ElementTree
    root = e.Element('udebs')

    # Definitions
    definitions = e.SubElement(root, 'definitions')
    for dtype in ['stats', 'lists', 'strings']:
        middle = e.SubElement(definitions, dtype)
        for item in getattr(env, dtype):
            if item in {'group', 'effect', 'require', 'increment'}:
                continue
            final = e.SubElement(middle, item)
            if item in env.rlist:
                final.attrib['rlist'] = ''

    #Config variables.
    config = e.SubElement(root, 'config')
    if env.name != 'Unknown':
        name = e.SubElement(config, 'name')
        name.text = env.name
    if env.logging != True:
        logging = e.SubElement(config, 'logging')
        logging.text = str(env.logging)
    if env.revert != 0:
        revert = e.SubElement(config, 'revert')
        revert.text = str(env.revert)
    if env.version != 1:
        version = e.SubElement(config, 'version')
        version.text = str(env.version)
    if env.seed != None:
        seed = e.SubElement(config, 'seed')
        seed.text = str(env.seed)

    # Time variables
    var = e.SubElement(root, 'time')
    if env.time != 0:
        time = e.SubElement(var, 'time')
        time.text = str(env.time)
    if env.increment != 1:
        time = e.SubElement(var, 'increment')
        time.text = str(env.increment)
    if env.cont != True:
        time = e.SubElement(var, 'cont')
        time.text = str(env.cont)
    if env.next != None:
        time = e.SubElement(var, 'next')
        time.text = str(env.next)

    #map
    maps = e.SubElement(root, 'maps')
    for map_ in env.map.values():
        node = e.SubElement(maps, map_.name)
        if map_.name in env.rmap:
            node.attrib['rmap'] = ''
        if map_.empty != 'empty':
            node.attrib['empty'] = map_.empty
        if map_.type != False:
            node.attrib['type'] = map_.type

        scan = [list(i) for i in zip(*map_._map)]
        for row in scan:
            middle = e.SubElement(node, 'row')
            text = ''
            for item in row:
                text = text + ', ' + item
            middle.text = text[2:]

    #entities
    stats = env.stats.union(env.strings, env.lists)
    entities = e.SubElement(root, 'entities')
    for entity in env.values():
        if entity.name == 'empty':
            continue
        elif isinstance(entity.name, interpret.UdebsStr):
            continue

        entity_node = e.SubElement(entities, entity.name)

        if entity.immutable:
            entity_node.attrib['immutable'] = ''

        for stat in stats:
            value = entity[stat]

            if stat == 'group':
                value = [i for i in value if i != entity.name]
            if value in [0, '', []]:
                continue

            stat_node = e.SubElement(entity_node, stat)
            if not stat in env.lists:
                stat_node.text = str(value)
            elif len(value) == 1:
                stat_node.text = str(value[0])
            else:
                for item in value:
                    entry_node = e.SubElement(stat_node, 'i')
                    entry_node.text = str(item)

    # Special
    special = e.SubElement(root, 'special')
    for entity in env.values():
        if not isinstance(entity.name, interpret.UdebsStr):
            continue

        entry_node = e.SubElement(special, 'i')
        entry_node.text = str(entity.name)

    # Delay
    delay = e.SubElement(root, "delays")
    if delay is not None:
        for ent in env.delay:
            d = e.SubElement(delay, "delay")
            for i in ("ticks", "script"):
                tmp = e.SubElement(d, i)
                tmp.text = str(ent[i])

            storage = e.SubElement(d, "storage")
            for key, value in ent["env"]["storage"].items():
                tmp = e.SubElement(storage, key)
                tmp.text = str(value)

    # Final Cleanup
    if pretty:
        indent(root)

    for node in root[:]:
        if node.text is None:
            root.remove(node)

    e.ElementTree(root).write(location)
    return True

#Creates and instance object from xml file.
def battleStart(xml_file, debug=False, script="init", name=None, revert=None, log=None, version=None, seed=None):
    """
    Creates an instanance object from given xml file.

    xml_file - String representing file to look in.
    debug - Boolean that gets passed to the interpret.interpret function.
    """
    try:
        tree = ElementTree.parse(xml_file)
        root = tree.getroot()
    except IOError:
        root = ElementTree.fromstring(xml_file)

    #ENV
    field = instance.Instance()

    def fillsimple(root, stat, f, overwrite=None):
        if overwrite is not None:
            setattr(field, stat, f(overwrite))
        else:
            tmp = root.findtext(stat)
            if tmp is not None:
                if f is not None:
                    tmp = f(tmp)

                setattr(field, stat, tmp)

    #Definition
    defs = root.find("definitions")
    if defs is not None:
        for i in ("stats", "strings"):
            def_stats = defs.find(i)
            if def_stats is not None:
                for stat in def_stats:
                    getattr(field, i).add(stat.tag)

        def_lists = defs.find("lists")
        if def_lists is not None:
            for stat in def_lists:
                field.lists.add(stat.tag)
                if stat.get('rlist') is not None:
                    field.rlist.add(stat.tag)

    #Config
    config = root.find("config")
    if config is not None:
        fillsimple(config, "name", None, name)
        fillsimple(config, "revert", int, revert)
        fillsimple(config, "logging", eval, log)
        fillsimple(config, "version", int, version)
        fillsimple(config, "seed", int, seed)

    # Time variables
    time = root.find("time")
    if time is not None:
        fillsimple(time, "time", int)
        fillsimple(time, "increment", int)
        fillsimple(time, "cont", eval)
        fillsimple(time, "next", eval)

    #Maps
    def addMap(field_map):
        options = {"name": field_map.tag}

        #Attributes
        for att in ("empty", "rmap", "type"):
            if field_map.get(att) is not None:
                options[att] = field_map.get(att)

        #dimensions.
        dim_map = field_map.find("dim")
        if dim_map is not None:
            options['dim'] = (
                int(dim_map.find('x').text),
                int(dim_map.find('y').text)
            )

        else:
            dim = []
            for row in field_map:
                dim.append(re.split("\W*,\W*", row.text))
            options['dim'] = [list(i) for i in zip(*dim)]

        #Add to field
        field.map[new_map.name] = board.Board(options)

    field_maps = root.find("maps")
    if field_maps is not None:
        [addMap(i) for i in field_maps]

    field_map = root.find("map")
    if field_map is not None:
        addMap(field_map)

    #Entities
    entity.Entity(field, {"name": "empty", "immutable": True})

    #Create all entity type objects.
    def addObject(item):
        options = {"name": item.tag}
        if item.get('immutable') is not None:
            options["immutable"] = True

        for stat in field.stats:
            elem = item.find(stat)
            if elem is not None:
                options[stat] = int(elem.text)

        for string in field.strings:
            value = item.findtext(string)
            if value is not None:
                options[string] = value

        for lst in field.lists:
            new_list = []
            find_list = item.find(lst)
            if find_list is not None:
                if len(find_list) == 0:
                    find_list = [find_list]
                for value in find_list:
                    if lst in {"effect", "require"}:
                        value.text = interpret.Script(value.text, field.version, debug)
                    new_list.append(value.text)
            options[lst] = new_list

        entity.Entity(field, options)

    entities = root.find("entities")
    if entities is not None:
        for item in entities:
            addObject(item)

    #Special
    special = root.find("special")
    if special is not None:
        for i in special:
            tmp = interpret.UdebsStr(i.text)
            field.getEntity(tmp)

    # Delay TODO

    #Final cleanup
    if field.logging:
        logging.basicConfig(stream=sys.stdout, level=logging.INFO, format="%(message)s")

    logging.info("INITIALIZING {}".format(field.name))

    if field.seed:
        field.rand.seed(field.seed)

    if script and script in field:
        field.castInit(script)

    logging.info('')
    logging.info('Env time is now {}'.format(field.time))

    if field.revert:
        field.state.append(copy.deepcopy(field))

    return field
