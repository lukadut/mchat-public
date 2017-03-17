import requests
import utils.xml_parser
import config
import json
import re

class Login:

    def __init__(self):
        self.config_xpath_root = "./loginpage"
        self.login_address_xpath = self.config_xpath_root + "/address"
        self.validators_xpath = self.config_xpath_root + "/validate/element"
        self.request_xpath = self.config_xpath_root + "/request"
        self.response_ok_validators_xpath = self.config_xpath_root + "/response/ok/element"
        self.response_error_validators_xpath = self.config_xpath_root + "/response/errors/element"

    def get_login_page(self, forum):
        address = config.get_config_node(forum, self.login_address_xpath).text
        timeout = config.get_timeout(forum)
        headers = json.loads(config.get_config_node(forum, "./header").text)
        try:
            cookies = "{"
            request_response = requests.request('GET', address, timeout=timeout, headers=headers)
            xml = utils.xml_parser.parse_request_content_to_xml(request_response)

            for cookie in request_response.cookies:
                cookies += '"{}":"{}",'.format(cookie.name, cookie.value)
            cookies += '}'
            cookies = cookies.replace(",}", "}")

            return {"xml": xml, "cookies": json.loads(cookies)}
        except Exception as e:
            print(e)
            print("Cannot connect to {}".format(address))
            return None

    def validate_get(self, forum, xml):
        response = {}

        if xml is None:
            response["state"] = "ERROR"
            response["errors"] = {"message": "Cannot connect to login webpage"}
            return response
        try:
            validators = config.get_config_nodes(forum, self.validators_xpath)
            for validator in validators:
                xpath = validator.text
                elements = xml.xpath(xpath)
                attribs = validator.attrib
                captcha = {}
                if (attribs["required"] == "true" and attribs["type"] == "ok" and len(elements) == 0) \
                        or (attribs["required"] == "false" and attribs["type"] == "error" and len(elements) > 0):
                    response["state"] = "ERROR"
                    response["errors"] = {"message": validator.attrib["message"]}
                    if "captcha" in attribs:
                        captcha.update({attribs["captcha"]: elements[0]})
                    response["captcha"] = captcha
                else:
                    response["state"] = "OK"
        except Exception as e:
            print(e)
            response["state"] = "ERROR"
            response["errors"] = {"message": "Cannot get login page"}

        return response

    def get_postlogin_page(self, forum, data):
        get_login_page_xml_and_cookies = self.get_login_page(forum)
        get_login_page_xml = get_login_page_xml_and_cookies["xml"]
        get_login_page_response = self.validate_get(forum,get_login_page_xml)
        if(get_login_page_response['state']!="OK"):
            return None

        anonymous_session = get_login_page_xml_and_cookies["cookies"]

        address = config.get_config_node(forum, self.login_address_xpath).text
        request_template = config.get_config_node(forum, self.request_xpath).text
        timeout = config.get_timeout(forum)

        matchs = re.findall('\{\{.+?\}\}', request_template)
        for match in matchs:
            request_template = request_template.replace(match, data[match[2:-2]])
        request_template = json.loads(request_template)

        try:
            cookies = "{"
            request_response = requests.request('POST', address, timeout=timeout, data=request_template, cookies=anonymous_session)
            for cookie in request_response.cookies:
                cookies += '"{}":"{}",'.format(cookie.name, cookie.value)
            cookies += '}'
            cookies = cookies.replace(",}", "}")
            temp_cookies=json.loads(cookies)
            header = json.loads(config.get_config_node(forum, './header').text)
            get_after_post_request = requests.request('GET',config.get_config_node(forum, './homepage/address').text + '/index.php?sid='+temp_cookies['phpbb3_pk6g2_sid'],headers=header,cookies=temp_cookies)

            cookies = '{'
            for cookie in get_after_post_request.cookies:
                cookies += '"{}":"{}",'.format(cookie.name, cookie.value)
            cookies += '}'
            cookies = cookies.replace(",}", "}")
            xml = utils.xml_parser.parse_request_content_to_xml(request_response)
            return {"xml": xml, "cookies": cookies}
        except Exception as e:
            print(e)
            print("Cannot connect to {}".format(address))
            return None

    def validate_post(self, forum, xml_and_cookies):
        response = {"state": "OK"}
        if xml_and_cookies is None:
            response["state"] = "ERROR"
            response["errors"] = {"message": "Cannot connect to login webpage"}
            return response
        xml = xml_and_cookies["xml"]
        cookies = xml_and_cookies["cookies"]
        try:
            validators = config.get_config_nodes(forum, self.response_error_validators_xpath)
            captcha = {}
            for validator in validators:
                xpath = validator.text
                elements = xml.xpath(xpath)
                attribs = validator.attrib
                if (len(elements) != 0):
                    response["state"] = "ERROR"
                    response["errors"] = {"message": validator.attrib["message"]}
                    if "captcha" in attribs:
                        print("captcha.update", attribs["captcha"], elements[0])
                        captcha.update({attribs["captcha"]: elements[0]})
                        response["captcha"] = captcha
            if response["state"] == "OK":
                validators = config.get_config_nodes(forum, self.response_ok_validators_xpath)
                for validator in validators:
                    xpath = validator.text
                    elements = xml.xpath(xpath)
                    if (len(elements) == 0):
                        response["state"] = "ERROR"
                        response["errors"] = {"message": "Invalid login or password"}
            if response["state"] == "OK":
                response["cookies"] = cookies

        except Exception as e:
            print(e)
            response["state"] = "ERROR"
            response["errors"] = {"message": "Cannot get postlogin page"}
        return response
