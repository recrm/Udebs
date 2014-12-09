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
        compile_ = e.SubElement(config, 'revert')
        compile_.text = str(env.compile - 1)
    
    #map
    maps = e.SubElement(root, 'maps')
    for map_ in env.map.values():
        node = e.SubElement(maps, map_.name)
        if map_.name in env.rmap:
            node.attrib['rmap'] = ''
        scan = [list(i) for i in zip(*map_.map)]
        for row in scan:
            middle = e.SubElement(node, 'row')
            text = ''
            for item in row:
                text = text + ', ' + item
            middle.text = text[2:]
    
    var = e.SubElement(root, 'var')
    if env.time != 0:
        time = e.SubElement(var, 'time')
        time.text = str(env.time)
    
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
    
    if env.log != []:
        log = e.SubElement(var, 'log')
        for item in env.log:
            node = e.SubElement(log, 'i')
            node.text = item

    #entities
    entities = e.SubElement(root, 'entities')
    for entry in env:   
        entity = env[entry]
        stats = env.stats.union(env.strings, env.lists)
        entity_node = e.SubElement(entities, entity.name)
        for stat in stats:
            value = getattr(entity, stat)
            if value in [0, '', list()]:
                continue
            stat_node = e.SubElement(entity_node, stat)
            if stat in env.lists:
                for item in value:
                    entry_node = e.SubElement(stat_node, 'i')
                    entry_node.text = str(item)
            else:
                stat_node.text = str(value)
            
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
    tree = e.ElementTree(root)
    tree.write(location)
    
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
    field = main.instance()
    
    config = root.find("config")
    if config is not None:
        
        name = config.findtext("name")
        if name is not None:
            field.name = name
            
        revert = config.findtext("revert")
        if revert is not None:
            field.revert = eval(revert) + 1
        
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
        
    def addMap(field_map):
        new_map = main.board()
        new_map.name = field_map.tag
        if field_map.get('empty') is not None:
            new_map.empty = map_.get('empty')
        
        dim_map = field_map.find("dim")
        if dim_map is not None:
            x = int(dim_map.find('x').text)
            y = int(dim_map.find('y').text)
            for element in range(y):
                new_map._map.append([new_map.empty for i in range(x)])
        else:
            temp = []
            for row in field_map:
                temp.append(re.split("\W*,\W*", row.text))
            new_map.map = [list(i) for i in zip(*temp)]
        return new_map
    
    #VAR
    field_maps = root.find("maps")
    if field_maps is not None:
        for map_ in field_maps:
            new_map = addMap(map_)
            field.map[new_map.name] = new_map
            if map_.get('rmap') is not None:
                field.rmap.add(map_.tag)
            
    else:
        field_map = root.find("map")
        if field_map is not None:
            new_map = addMap(field_map)
            field.map[new_map.name] = new_map
            
    var = root.find('var')
    if var is not None:
        time = var.find('time')
        if time is not None:
            field.time = int(time.text)
            
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
        
        log = var.find('log')
        if log is not None:
            for item in log:
                field.log.append(item.text)
    
    #Set empty 
    empty = main.entity(field)
    empty.immutable = True
    empty.record()
    
    #Create all entity type objects.
    def addObject(item):
        new_entity = main.entity(field, item.tag)
        new_entity.name = item.tag
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
                        require = True if lst == "require" else False
                        value.text = main.script(value.text, require, debug)
                    new_list.append(value.text)
            setattr(new_entity, lst, new_list)
        
        new_entity.update()
        new_entity.record()
        
        return new_entity
                        
    entities = root.find("entities")
    if entities is not None:
        for item in entities:
            new_entity = addObject(item)
    
    field.controlLog("INITIALIZING", field.name)
    if 'tick' not in field:
        field.controlLog("warning, no tick is defined.")
    
    if field.revert > 1:
        field.state.append(copy.copy(field))
    print()    
    return field


