import utils.xml_parser as parser
import os

__configs={}

__path = ".\\config\\"

def read_files():
    for xml_files in os.listdir(__path):
        if xml_files.endswith(".xml"):
            __configs[str(xml_files)[:-4]]=parser.parse_file_to_xml(__path + xml_files)

def get_config(forum_name):
    if forum_name in __configs:
        return __configs[forum_name]
    else:
        return __configs["default"]

def get_config_node(forum_name,xpath):
    try:
        cfg = get_config(forum_name)
        node = cfg.find(xpath)
        return node
    except Exception as e:
        print(e)
        return None

def get_config_nodes(forum_name, xpath):
    try:
        cfg = get_config(forum_name)
        node = cfg.xpath(xpath)
        return node
    except Exception as e:
        print(e)
        return None

def get_timeout(forum_name):
    timeout = get_config_node(forum_name,"./timeout").text
    try:
        timeout = int(timeout)
    except Exception as e:
        timeout = 5
    return timeout



read_files()