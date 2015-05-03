import copy
import re
from udebs import main
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
    if env.hex != False:
        hexmap = e.SubElement(config, 'hex')
        hexmap.text = str(env.hex)
    if env.logging != True:
        logging = e.SubElement(config, 'logging')
        logging.text = str(env.logging)
    if env.compile != True:
        compile_ = e.SubElement(config, 'compile')
        compile_.text = str(env.compile)
    if env.revert != 1:
        revert = e.SubElement(config, 'revert')
        revert.text = str(env.revert - 1)
    if env.version != 1:
        version = e.SubElement(config, 'version')
        version.text = str(env.version)
    if env.inheritance != True:
        inheritance = e.SubElement(config, 'version')
        inheritance.text = str(env.inheritance)

    #map
    maps = e.SubElement(root, 'maps')
    for map_ in env.map.values():
        node = e.SubElement(maps, map_.name)
        if map_.name in env.rmap:
            node.attrib['rmap'] = ''
        if map_.name != 'empty':
            node.attrib['empty'] = map_.empty
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

    if env.log != []:
        log = e.SubElement(var, 'log')
        for item in env.log:
            node = e.SubElement(log, 'i')
            node.text = item

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
            value = getattr(entity, stat)

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
def battleStart(xml_file, debug=False):
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
    field = main.Instance()

    #Config
    config = root.find("config")
    if config is not None:

        name = config.findtext("name")
        if name is not None:
            field.name = name

        revert = config.findtext("revert")
        if revert is not None:
            field.revert = int(revert) + 1

        comp = config.findtext("compile")
        if comp is not None:
            field.compile = eval(comp)

        logichex = config.findtext("hex")
        if logichex is not None:
            if logichex != "diag":
                field.hex = eval(logichex)
            else:
                field.hex = logichex

        logging = config.findtext('logging')
        if logging is not None:
            field.logging = eval(logging)

        version = config.findtext('version')
        if version is not None:
            field.version = int(version)

        inheritance = config.findtext('inheritance')
        if inheritance is not None:
            field.inheritance = eval(inheritance)

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
        name = field_map.tag

        empty = "empty"
        field_empty = field_map.find('empty')
        if field_map.get('empty') is not None:
            empty = field_map.get('empty')

        dim_map = field_map.find("dim")
        if dim_map is not None:
            dim = (
                int(dim_map.find('x').text),
                int(dim_map.find('y').text)
            )

        else:
            dim = []
            for row in field_map:
                dim.append(re.split("\W*,\W*", row.text))
            dim = [list(i) for i in zip(*dim)]

        new_map = main.Board(name, dim, empty)

        #Add to field
        if field_map.get('rmap') is not None:
            field.rmap.add(new_map.name)

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

        log = var.find('log')
        if log is not None:
            for item in log:
                field.log.append(item.text)

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
    main.Entity(field, "empty", True)

    #Create all entity type objects.
    def addObject(item):
        new_entity = main.Entity(field, item.tag)
        if item.get('immutable') is not None:
            new_entity.immutable = True

        for stat in field.stats:
            elem = item.find(stat)
            add_attr = int(elem.text) if elem is not None else 0
            setattr(new_entity, stat, add_attr)

        for string in field.strings:
            value = item.findtext(string)
            add_attr = value if value is not None else ""
            setattr(new_entity, string, add_attr)

        for lst in field.lists:
            new_list = getattr(new_entity, lst)
            find_list = item.find(lst)
            if find_list is not None:
                if len(find_list) == 0:
                    find_list = [find_list]
                for value in find_list:
                    if field.compile and lst in {"effect", "require"}:
                        require = (lst == "require")
                        value.text = main.Script(value.text, require, debug, version=field.version)
                    new_list.append(value.text)
            setattr(new_entity, lst, new_list)

    entities = root.find("entities")
    if entities is not None:
        for item in entities:
            addObject(item)

    #Final cleanup
    field.controlLog("INITIALIZING", field.name)
    if 'tick' not in field:
        field.controlLog("warning, no tick is defined.\n")

    if field.revert > 1:
        field.state.append(copy.deepcopy(field))

    return field
