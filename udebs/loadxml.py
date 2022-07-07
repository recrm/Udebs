import re
from udebs import instance
from xml.etree import ElementTree


# This is a pretty printing algorithm I stole from the internet.
def _indent(elem, level=0):
    """A simple pretty print function for xml."""
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            _indent(elem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


# creates an xml file from instance object.
def battleWrite(env, location, pretty=False):
    """
    Writes an instance object to file.

    env - Instance object to write.
    location - Variable to pass to xml.etree.write.
    """
    e = ElementTree
    root = e.Element('udebs')

    def add_leaf(root2, node2, value2):
        new = e.SubElement(root2, node2)
        new.text = value2

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

    # Config variables.
    config = e.SubElement(root, 'config')
    if env.name != 'Unknown':
        add_leaf(config, "name", env.name)
    if env.logging is not True:
        add_leaf(config, "logging", str(env.logging))
    if env.revert != 0:
        add_leaf(config, "revert", str(env.revert))
    if env.version != 1:
        add_leaf(config, "version", str(env.version))
    if env.seed is not None:
        add_leaf(config, "seed", str(env.seed))
    if env.immutable is not True:
        add_leaf(config, "immutable", str(env.immutable))

    # Time variables
    var = e.SubElement(root, 'var')
    if env.time != 0:
        add_leaf(var, "time", str(env.time))
    if env.increment != 1:
        add_leaf(var, "increment", str(env.increment))
    if env.cont is not True:
        add_leaf(var, "cont", str(env.cont))
    if env.value is not None:
        add_leaf(var, "value", str(env.value))

    # map
    maps = e.SubElement(root, 'maps')
    for map_ in env.map.values():
        node = e.SubElement(maps, map_.name)
        if map_.name in env.rmap:
            node.attrib['rmap'] = ''
        if map_.empty != 'empty':
            node.attrib['empty'] = map_.empty
        if map_.type is not False:
            node.attrib['type'] = map_.type
        for row in (list(i) for i in zip(*map_.map)):
            add_leaf(node, "row", ", ".join(row))

    # entities
    stats = env.stats.union(env.strings, env.lists)
    entities = e.SubElement(root, 'entities')
    special = e.SubElement(root, 'special')
    for item in env.values():
        if item.name == 'empty':
            continue

        elif item.name[-1] == ")":
            add_leaf(special, "i", str(item.name))
            continue

        entity_node = e.SubElement(entities, item.name)

        if item.immutable:
            entity_node.attrib['immutable'] = ''

        for stat in stats:
            value = getattr(item, stat)

            if value in [0, '', []]:
                continue

            stat_node = e.SubElement(entity_node, stat)
            if stat not in env.lists:
                stat_node.text = str(value)
            elif len(value) == 1:
                stat_node.text = str(value[0])
            else:
                for elem in value:
                    add_leaf(stat_node, "i", str(elem))

    # Delay
    delay = e.SubElement(root, "delays")
    if delay is not None:
        for ent in env.delay:
            d = e.SubElement(delay, "delay")
            add_leaf(d, "ticks", str(ent["ticks"]))
            add_leaf(d, "script", str(ent["script"]))

            storage = e.SubElement(d, "storage")
            for key, value in ent["env"]["storage"].items():
                add_leaf(storage, str(key), str(value))

    # rand
    add_leaf(root, "random", str(env.rand.getstate()))

    # Final Cleanup
    if pretty:
        _indent(root)

    for node in root[:]:
        if node.text is None:
            root.remove(node)

    e.ElementTree(root).write(location)
    return True


def _parse_map(field_map2):
    options2 = {"name": field_map2.tag}

    # Attributes
    for att in ("empty", "rmap", "type"):
        if field_map2.get(att) is not None:
            options2[att] = field_map2.get(att)

    # dimensions.
    dim_map = field_map2.find("dim")
    if dim_map is not None:
        options2['dim'] = (
            int(dim_map.find('x').text),
            int(dim_map.find('y').text)
        )

    else:
        dim = []
        for row in field_map2:
            dim.append(re.split(r"\W*,\W*", row.text))
        options2['dim'] = [list(j) for j in zip(*dim)]

    return options2


# Creates and instance object from xml file.
def battleStart(xml_file=None, field=instance.Instance, **overwrite):
    """
    Creates an instance object from given xml file.

    xml_file - String representing file to look in.
    debug - Boolean that gets passed to the interpret.interpret function.
    script - Override the script that runs after initialization
    **overwrite - other overrides passed to the script.
    """
    if xml_file is None:
        xml_file = "<udebs />"
    try:
        tree = ElementTree.parse(xml_file)
        root = tree.getroot()
    except IOError:
        root = ElementTree.fromstring(xml_file)

    options = {}

    # Definition
    defs = root.find("definitions")
    if defs is not None:
        for i in ("stats", "strings"):
            options[i] = set()
            def_stats = defs.find(i)
            if def_stats is not None:
                for stat in def_stats:
                    options[i].add(stat.tag)

        def_lists = defs.find("lists")
        if def_lists is not None:
            options["lists"] = set()
            options["rlist"] = []
            for stat in def_lists:
                options["lists"].add(stat.tag)
                if stat.get('rlist') is not None:
                    options["rlist"].append(stat.tag)

    # Config
    config = root.find("config")
    if config is not None:
        for value, f in [("name", str), ("revert", int), ("logging", eval), ("version", int), ("seed", int),
                         ("immutable", eval)]:
            tmp = config.findtext(value)
            if tmp is not None:
                options[value] = f(tmp)

    # var variables
    time = root.find("var")
    if time is not None:
        for value, f in [("time", int), ("increment", int), ("cont", eval), ("next", eval), ("value", eval)]:
            tmp = time.findtext(value)
            if tmp is not None:
                options[value] = f(tmp)

    # Maps
    options["map"] = []
    field_maps = root.find("maps")
    if field_maps is not None:
        options["map"].extend([_parse_map(i) for i in field_maps])

    field_map = root.find("map")
    if field_map is not None:
        options["map"].append(_parse_map(field_map))

    # Create all entity type objects.
    options["entities"] = []
    entities = root.find("entities")
    if entities is not None:
        for item in entities:
            stats = {"name": item.tag}
            immutable = item.get("immutable")
            if immutable is not None:
                if immutable == "False":
                    stats["immutable"] = False
                else:
                    stats["immutable"] = True

            for elem in item:
                if len(list(elem)) > 0:
                    stats[elem.tag] = [i.text for i in elem]
                else:
                    stats[elem.tag] = elem.text

            options["entities"].append(stats)

    # Special
    options["special"] = []
    special = root.find("special")
    if special is not None:
        for i in special:
            options["special"].append(i.text)

    # Delay
    delays = root.find("delays")
    if delays is not None:
        options["delay"] = []
        for delay in delays:
            callback = delay.findtext("script")
            time = int(delay.findtext("ticks"))
            storage = {node.tag: node.text for node in delay.find("storage")}
            options["delay"].append({"callback": callback, "ticks": time, "storage": storage})

    # Random
    rand = root.find("random")
    if rand is not None:
        options["rand"] = eval(rand.text)

    return field(**options)
