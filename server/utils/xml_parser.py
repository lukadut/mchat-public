from bs4 import BeautifulSoup
from lxml.html import etree as HTMLTree
from lxml import etree as XMLTree
import re


def parse_request_content_to_xml(request):
    if request.status_code != 200:
        raise Exception("Invalid http response code " + request.status_code)
    content = request.content.decode("utf-8")
    content = remove_html_namespace(content)
    fixed_html = str(BeautifulSoup(content, "lxml"))
    xml_tree = HTMLTree.fromstring(fixed_html)
    return xml_tree


def remove_html_namespace(content_string):
    content_string = re.sub("<html.+xmlns.+>", "<html>", content_string)
    return content_string


def parse_file_to_xml(file_name):
    xml_tree = XMLTree.parse(file_name)
    return xml_tree
