import logging
import os
import sys

from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin

import config
from mChat import login, mchat

app = Flask(__name__, static_url_path='/static')
CORS(app)
login = login.Login()
mchat = mchat.MChat()

logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-10.105s] %(message)-s")

# logging.basicConfig(format=FORMAT)
logger = logging.getLogger("app")
logger.setLevel(logging.INFO)
fileHandler = logging.FileHandler("{0}/{1}.log".format(os.path.dirname(os.path.abspath(__file__)), "log"))
fileHandler.setFormatter(logFormatter)
logger.addHandler(fileHandler)

consoleHandler = logging.StreamHandler(sys.stdout)
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)


@app.route('/login', methods=['POST'])
@cross_origin()
def post_login():
    response = {}
    try:
        forum = request.json["forum"]
        data = {"login": request.json["login"],
                "password": request.json["password"]}
        xml_and_cookies = login.get_postlogin_page(forum, data)
        response = login.validate_post(forum, xml_and_cookies)
    except Exception as error:
        logger.exception(error)
        response["state"] = "ERROR"
        response["errors"] = {"message": "Invalid arguments"}
    return jsonify(**response)


@app.route('/mchatmessages', methods=['POST'])
@cross_origin()
def mchat_messages():
    response = {}
    try:
        forum = request.json["forum"]
        session_cookies = request.json["cookies"]
        messageid = 0
        if "messageid" in request.json:
            messageid = request.json["messageid"]
        xml = mchat.get_mchat_read_page(forum, session_cookies, messageid=messageid)
        response = mchat.get_messages(xml, forum)
    except Exception as error:
        logger.exception(error)
        response["state"] = "ERROR"
        response["errors"] = {"message": "Invalid arguments"}
    return jsonify(**response)


@app.route('/mchatarchive', methods=['POST'])
@cross_origin()
def mchat_archive():
    response = {}
    try:
        forum = request.json["forum"]
        session_cookies = request.json["cookies"]
        if "readmessages" in request.json:
            read_messages = request.json["readmessages"]
        xml = mchat.get_mchat_archive_page(forum, session_cookies, read_messages=read_messages)
        response = mchat.get_messages(xml, forum)
    except Exception as error:
        logger.exception(error)
        response["state"] = "ERROR"
        response["errors"] = {"message": "Invalid arguments"}
    return jsonify(**response)


@app.route('/mchatadd', methods=['POST'])
@cross_origin()
def mchat_add():
    response = {}
    try:
        forum = request.json["forum"]
        session_cookies = request.json["cookies"]
        message = request.json["message"]
        response = mchat.send_message(forum, session_cookies, message)

    except Exception as error:
        logger.exception(error)
        response["state"] = "ERROR"
        response["errors"] = {"message": "Invalid arguments"}
    return jsonify(**response)


if __name__ == '__main__':
    print("run")
    app.run()
