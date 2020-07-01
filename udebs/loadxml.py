import copy
import re
import sys
import logging
from . import board, entity, instance, interpret
from xml.etree import ElementTree
from collections import deque


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
    if env.auto_entity is not True:
        add_leaf(config, "auto_entity", str(env.auto_entity))

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

        elif isinstance(item.name, interpret.UdebsStr):
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
                add_leaf(storage, key, str(value))

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


# Creates and instance object from xml file.
def battleStart(xml_file=None, debug=False, script="init", name=None, revert=None, log=None, version=None, seed=None,
                immutable=None, field=None, auto_entity=None):
    """
    Creates an instance object from given xml file.

    xml_file - String representing file to look in.
    debug - Boolean that gets passed to the interpret.interpret function.
    """
    if xml_file is None:
        xml_file = "<udebs />"

    try:
        tree = ElementTree.parse(xml_file)
        root = tree.getroot()
    except IOError:
        root = ElementTree.fromstring(xml_file)

    # ENV
    if field is None:
        field = instance.Instance()

    # Definition
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
                    field.rlist.append(stat.tag)

    def fill_simple(root2, stat2, f, overwrite=None):
        if overwrite is not None:
            setattr(field, stat2, overwrite)
        else:
            tmp = root2.findtext(stat2)
            if tmp is not None:
                if f is not None:
                    tmp = f(tmp)

                setattr(field, stat2, tmp)

    # Config
    config = root.find("config")
    if config is not None:
        fill_simple(config, "name", None, name)
        fill_simple(config, "revert", int, revert)
        fill_simple(config, "logging", eval, log)
        fill_simple(config, "version", int, version)
        fill_simple(config, "seed", int, seed)
        fill_simple(config, "immutable", eval, immutable)
        fill_simple(config, "auto_entity", eval, auto_entity)

    # Time variables
    time = root.find("var")
    if time is not None:
        fill_simple(time, "time", int)
        fill_simple(time, "increment", int)
        fill_simple(time, "cont", eval)
        fill_simple(time, "next", eval)
        fill_simple(time, "value", eval)

    # Maps
    def addMap(field_map2):
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

        # Add to field
        field.map[options2["name"]] = board.Board(**options2)
        if "rmap" in options2:
            field.rmap.append(options2["name"])

    field_maps = root.find("maps")
    if field_maps is not None:
        [addMap(i) for i in field_maps]

    field_map = root.find("map")
    if field_map is not None:
        addMap(field_map)

    # Entities
    field["empty"] = entity.Entity(field, name="empty", immutable=True)

    # Create all entity type objects.
    entities = root.find("entities")
    if entities is not None:
        for item in entities:
            options = {"name": item.tag}

            immutable = item.get("immutable")
            if immutable is None:
                options["immutable"] = field.immutable
            elif immutable == "False":
                options["immutable"] = False
            else:
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

            # set loc
            if not options["immutable"]:
                for map_ in field.map.values():
                    for loc in map_:
                        if map_[loc] == options["name"]:
                            options["loc"] = loc
                            break

            field[options["name"]] = entity.Entity(field, **options)

    # Special
    special = root.find("special")
    if special is not None:
        for i in special:
            field.getEntity(interpret.UdebsStr(i.text))

    # Delay
    delays = root.find("delays")
    if delays is not None:
        for delay in delays:
            callback = delay.findtext("script")
            time = int(delay.findtext("ticks"))
            storage = {node.tag: field[node.text] for node in delay.find("storage")}
            field.controlDelay(callback, time, storage)

    # Random
    rand = root.find("random")
    if rand is not None:
        field.rand.setstate(eval(rand.text))
    elif field.seed:
        field.rand.seed(field.seed)

    # Final cleanup
    logging.basicConfig(**{
        "stream": sys.stdout,
        "level": logging.INFO if field.logging else logging.WARNING,
        "format": "%(message)s",
    })

    if field.logging:
        logging.info(f"INITIALIZING {field.name}")
        logging.info(f"Env time is now {field.time}")

    if script in field:
        field.castInit(script)
    elif field.logging:
        logging.info("")

    if field.revert:
        field.state = deque(maxlen=field.revert + 1)
        field.state.append(copy.copy(field))

    return field
