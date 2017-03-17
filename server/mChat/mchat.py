import json
import requests
import config
import utils
from lxml import etree as XMLTree


class MChat:

    def __init__(self):
        self.config_xpath_root = "./chatpage"
        self.mchat_address_xpath = self.config_xpath_root + "/address"
        self.mchat_add_xpath = self.config_xpath_root + "/add/data"
        self.mchat_read_address_xpath = self.config_xpath_root + "/read/address"
        self.mchat_read_header_xpath = self.config_xpath_root + "/read/header"
        self.mchat_archive_address_xpath = self.config_xpath_root + "/archive/address"
        self.mchat_message_xpath = self.config_xpath_root + "/chatmessage/message"
        self.mchat_messageid_xpath = self.config_xpath_root + "/chatmessage/messageid"
        self.mchat_avatar_xpath = self.config_xpath_root + "/chatmessage/avatar"
        self.mchat_user_xpath = self.config_xpath_root + "/chatmessage/user"
        self.mchat_time_xpath = self.config_xpath_root + "/chatmessage/time"
        self.mchat_content_xpath = self.config_xpath_root + "/chatmessage/content"
        self.mchar_validators_xpath = self.config_xpath_root + "/errors/element"

    def replace_last(self,s, old, new, occurrence):
        li = s.rsplit(old, occurrence)
        return new.join(li)

    def node_to_string(self, node):
        elements_with_functions = node.xpath(".//*[@onclick]")
        for element in elements_with_functions:
            del element.attrib["onclick"]
        spoilers = node.xpath(".//div[contains(@class,'quotetitle')]/input[@value='Pokaż']/parent::*/parent::*")
        for spoiler in spoilers:
            spoiler.set("class","mChatSpoiler")
        node = self.ionic_url_fix(node)
        string = XMLTree.tostring(node, pretty_print=True, encoding='utf8').decode("utf-8")
        return string.strip()

    def ionic_url_fix(self,xml):
        hyperlinks = xml.xpath('.//a[@href]')
        for hyperlink in hyperlinks:
            href = hyperlink.attrib["href"]
            hyperlink.set("onclick","window.open('" + href + "', '_system', 'location=yes'); return false;")
        return xml

    def get_mchat_read_page(self, forum, session_cookies, messageid=0):
        address = config.get_config_node(forum, self.mchat_read_address_xpath).text
        address = address.replace('{{messageid}}', str(messageid))

        timeout = config.get_timeout(forum)
        if type(session_cookies) is dict:
            cookies = session_cookies
        else:
            cookies = json.loads(session_cookies)
        headers = json.loads(config.get_config_node(forum, './header').text)
        try:
            request_response = requests.request('GET', address, timeout=timeout, cookies=cookies, headers=headers)
            if request_response.status_code == 403:
                return 403
            if request_response.content.decode("utf-8").strip() == "" and request_response.status_code==200:
                xml = XMLTree.fromstring("<html></html>")
                return xml
            xml = utils.xml_parser.parse_request_content_to_xml(request_response)
            return xml
        except Exception as e:
            print(e)
            print("Cannot connect to {}".format(address))
            return None

    def get_mchat_archive_page(self, forum, session_cookies, read_messages=0):
        timeout = config.get_timeout(forum)
        if type(session_cookies) is dict:
            cookies = session_cookies
        else:
            cookies = json.loads(session_cookies)
        headers = json.loads(config.get_config_node(forum, "./header").text)
        address = config.get_config_node(forum, self.mchat_archive_address_xpath).text
        address = address.replace('{{readmessages}}', str(read_messages))
        try:
            request_response = requests.request('GET', address, timeout=timeout, cookies=cookies, headers=headers,
                                                )
            if request_response.status_code == 403:
                return 403
            if request_response.content.decode("utf-8").strip() == "":
                xml = XMLTree.fromstring("<html></html>")
                return xml
            xml = utils.xml_parser.parse_request_content_to_xml(request_response)
            return xml
        except Exception as e:
            print(e)
            print("Cannot connect to {}".format(address))
            return None

    def send_message(self, forum, session_cookies, message):
        address = config.get_config_node(forum, self.mchat_address_xpath).text

        timeout = config.get_timeout(forum)
        if type(session_cookies) is dict:
            cookies = session_cookies
        else:
            cookies = json.loads(session_cookies)
        headers = json.loads(config.get_config_node(forum, "./header").text)
        data = config.get_config_node(forum, self.mchat_add_xpath).text
        data = data.replace('{{message}}', message)
        data = json.loads(data)
        response = {}
        try:
            request_response = requests.request('POST', address, timeout=timeout, cookies=cookies, headers=headers,
                                                params=data)
            code = request_response.status_code
            if code == 200:
                response["state"] = "OK"
            elif code == 400:
                response["state"] = "ERROR"
                response["errors"] = {"message": "Flood"}
            elif code == 403:
                response["state"] = "ERROR"
                response["errors"] = {"message": "Invalid session"}
            elif code == 501:
                response["state"] = "ERROR"
                response["errors"] = {"message": "Empty message"}

        except Exception as e:
            response["state"] = "ERROR"
            response["errors"] = {"message": "Cannot send message"}
        return response

    def make_message_dict(self, forum, xpath, message, mess, key):
        xpath_ = config.get_config_node(forum, xpath)
        value = message.xpath(xpath_.text)
        if type(value) is list:
            mess[key] = value[0]
        else:
            mess[key] = value
        return mess

    def get_messages(self, xml, forum):
        response = {}
        if xml is None:
            response["state"] = "ERROR"
            response["errors"] = {"message": "Cannot connect to mChat"}
            return response
        if xml == 403:
            response["state"] = "ERROR"
            response["errors"] = {"message": "Invalid session"}
            return response
        response["state"] = "OK"
        data = []
        try:
            validators = config.get_config_nodes(forum, self.mchar_validators_xpath)
            for validator in validators:
                xpath = validator.text
                elements = xml.xpath(xpath)
                if len(elements) != 0:
                    response["state"] = "ERROR"
                    response["errors"] = {"message": validator.attrib["message"]}
                    return response
            messages = xml.xpath(config.get_config_node(forum, self.mchat_message_xpath).text)
            for message in messages:
                mess = {"avatar": None, "content": None, "messageid": None, "time": None, "user": None}

                mess = self.make_message_dict(forum, self.mchat_messageid_xpath, message, mess, "messageid")
                mess = self.make_message_dict(forum, self.mchat_avatar_xpath, message, mess, "avatar")
                avatar = mess['avatar'].replace("./", config.get_config_node(forum, "./homepage/address").text + "/")
                mess['avatar'] = avatar
                mess = self.make_message_dict(forum, self.mchat_time_xpath, message, mess, "time")
                mess = self.make_message_dict(forum, self.mchat_user_xpath, message, mess, "user")
                content =self.node_to_string(message.xpath(
                    config.get_config_node(forum, self.mchat_content_xpath).text)[0])
                content = content.replace('src="./', 'src="'+config.get_config_node(forum, "./homepage/address").text+'/')
                mess["content"] = content
                data.append(mess)
            response["data"] = sorted(data, key=lambda k: k['messageid'])
        except Exception as e:
            print(e)
            response["state"] = "ERROR"
            response["errors"] = {"message": "Cannot get messages"}

        return response
