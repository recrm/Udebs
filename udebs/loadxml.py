import copy
import re
import sys
import logging
from udebs import board, entity, instance, interpret
from xml.etree import ElementTree

#creates an xml file from instance object.
def battleWrite(env, location, pretty=False):
    """
    Writes an instance object to file.

    env - Instance object to write.
    location - Variable to pass to xml.etree.write.
    """
    e = ElementTree
    root = e.Element('udebs')

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

    #Variables
    var = e.SubElement(root, 'var')
    if env.time != 0:
        time = e.SubElement(var, 'time')
        time.text = str(env.time)

    #Delay has changed, this is probobly broken.
    if env.delay != []:
        delay = e.SubElement(var, 'delay')
        for item in env.delay:
            node = e.SubElement(delay, 'i')
            node.attrib.update(item)
            for key, value in node.attrib.items():
                if isinstance(value, entity):
                    if not value.immutable:
                        node.attrib[key] = str(value.name)
                    else:
                        node.attrib[key] = str(value.loc)
                else:
                    node.attrib[key] = str(value)

    #entities
    stats = env.stats.union(env.strings, env.lists)
    entities = e.SubElement(root, 'entities')
    for entity in env.values():
        if entity.name == 'empty':
            continue

        entity_node = e.SubElement(entities, entity.name)

        if entity.immutable:
            entity_node.attrib['immutable'] = ''

        for stat in stats:
            value = entity[stat]

            if stat == 'group':
                value = [i for i in value if i != entity.name]
            if value in [0, '', list()]:
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

    if pretty:
        indent(root)

    e.ElementTree(root).write(location)
    return True

#Creates and instance object from xml file.
def battleStart(xml_file, debug=False, script="init"):
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

    #Config
    config = root.find("config")
    if config is not None:

        name = config.findtext("name")
        if name is not None:
            field.name = name

        revert = config.findtext("revert")
        if revert is not None:
            field.revert = int(revert)

        log = config.findtext('logging')
        if log is not None:
            field.logging = eval(log)

        version = config.findtext('version')
        if version is not None:
            field.version = int(version)

        seed = config.findtext('seed')
        if seed is not None:
            field.seed = int(seed)

    if field.logging:
        logging.basicConfig(stream=sys.stdout, level=logging.INFO, format="%(message)s")

    #Definition
    defs = root.find("definitions")
    if defs is not None:
        def_stats = defs.find("stats")
        if def_stats is not None:
            for stat in def_stats:
                field.stats.add(stat.tag)

        def_lists = defs.find("lists")
        if def_lists is not None:
            for stat in def_lists:
                field.lists.add(stat.tag)
                if stat.get('rlist') is not None:
                    field.rlist.add(stat.tag)

        def_strings = defs.find("strings")
        if def_strings is not None:
            for stat in def_strings:
                field.strings.add(stat.tag)

    #Maps
    def addMap(field_map):
        options = {"name": field_map.tag}

        #Attributes
        if field_map.get('empty') is not None:
            options["empty"] = field_map.get('empty')

        if field_map.get('rmap') is not None:
            options["rmap"] = field_map.get('rmap')

        if field_map.get('type') is not None:
            options["type"] = field_map.get('type')

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
        new_map = board.Board(options)
        field.map[new_map.name] = new_map

    field_maps = root.find("maps")
    if field_maps is not None:
        for map_ in field_maps:
            addMap(map_)

    field_map = root.find("map")
    if field_map is not None:
        addMap(field_map)

    #Var (Rarely used).
    var = root.find('var')
    if var is not None:
        time = var.find('time')
        if time is not None:
            field.time = int(time.text)

        #Delay has changed, this is probobly broken.
        delay = var.find('delay')
        if delay is not None:
            for item in delay:
                for key in item.attrib:
                    if key == 'DELAY':
                        item.attrib[key] = int(item.attrib[key])
                    if key in {'CASTER', 'TARGET', 'MOVE'}:
                        try:
                            index = item.attrib[key].index(',')
                            x = int(item.attrib[key][1:index])
                            y = int(item.attrib[key][index+2:-1])
                            item.attrib[key] = (x,y)
                        except ValueError:
                            pass
                field.delay.append(item.attrib)

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

    #Final cleanup
    logging.info("INITIALIZING {}".format(field.name))

    if field.seed:
        field.rand.seed(field.seed)

    if script and script in field:
        field.controlInit(script)

    if field.revert:
        field.state.append(copy.deepcopy(field))

    return field
