import json
import time
from threading import Lock, Thread
import requests
import sys
from flask import Flask
from flask import request
from flask import Response
import subprocess
import re

# import urllib.parse
from Classes import AddressInfo
from MonitorFiberMap import (
    getAddressInfo, getCitiesList, getProvinceList, getRegionList,
    getSteetsList, getSteetsNumberList, reloadPageInfo, getPageInfo)

URL = "https://api.telegram.org/bot{}/"
last_update_id = 0

dictUserCode = {}

app = Flask(__name__)

# Return the content of the page from the given a URL


def get_url(url):
    response = requests.get(url)
    content = response.content.decode("utf8")
    return content

# Return the json object of a page from the given URL


def get_json_from_url(url):
    content = get_url(url)
    js = json.loads(content)
    return js

# Check new messages (call to Telegram API)


def get_updates():
    global last_update_id

    url = URL + "getUpdates?offset={}".format(last_update_id)
    js = get_json_from_url(url)

    if(js["ok"] == True):
        leng = len(js["result"])
        if(leng > 0):
            last_update_id = js["result"][leng - 1]["update_id"]
            last_update_id += 1

            # Salvataggio dell'ultimo update_id per impedire la rilettura dell'ultimo messaggio al riavvio del Bot
            # f = open("myfile.txt", "w")
            # f.write(str(last_update_id))
            # f.close()

    return js

# Send a message to the specified chat_id (call to Telegram API)


def send_message(text, chat_id):
    url = URL + "sendMessage?text={}&chat_id={}".format(text, chat_id)
    get_url(url)


def set_Webhook(url):
    url = URL + "setWebhook?url={}".format(url)
    get_url(url)

 # Convert a dictiornary to an inline keyboard


def dict_to_inline_keyboard(dict, columns):

    maxColumnIndex = columns - 1

    keyboard = {
        "inline_keyboard": []
    }

    colIndex = 0
    rowIndex = -1

    for id, name in dict.items():
        val = {"text": name, "callback_data": str(id)}

        if(colIndex != maxColumnIndex and rowIndex > -1):
            colIndex = colIndex + 1
            keyboard["inline_keyboard"][rowIndex].append(val)
        else:
            colIndex = 0
            rowIndex = rowIndex + 1

            button = []
            button.append(val)

            keyboard["inline_keyboard"].append(button)

    return keyboard

# Thread scanning for updates (call to Fibermap API)


def cycle_master():
    try:

        while True:
            listCodes = []
            listAlm = []

            # Get a unique code list
            for val in dictUserCode.values():
                for vall in val:
                    if(vall not in listCodes):
                        listCodes.append(vall)

            for code in listCodes:
                alm = reloadPageInfo(code, 1)
                listAlm.append(alm)

            # TODO: Send the message with the notification of status change (FiberScanner#1)
            time.sleep(100)
    except:
        # TODO: Send to admin's chat the error message (FiberScanner#2)
        print("Unexpected error:", sys.exc_info()[0])
        time.sleep(100)

from collections import namedtuple

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':

        messageReceived = request.get_json()

        if "message" in messageReceived:
            if(messageReceived["message"]["text"] == "/regioni"):
                region_list = getRegionList()
                keyboard = dict_to_inline_keyboard(region_list, 2)

                chatId = messageReceived["message"]["chat"]["id"]
                data = {
                    "chat_id": chatId,
                    "text": "Regioni:",
                    "reply_markup": json.dumps(keyboard)
                }

                urlResponse = URL + "sendMessage"
                response = requests.post(
                    url=urlResponse, data=data).json()

            elif("/addinline" in messageReceived["message"]["text"]):
                fulltext = messageReceived["message"]["text"]
                fulladdress = fulltext.replace("/addinline", "")
                addresslist = fulladdress.split(",")

                regioni = getRegionList()
                regione = addresslist[0].upper().strip()

                # TODO FIX COME MAI NON VA??? TIPS: Fatti te un algoritmo di ricerca per prestazioni e ritornare ID (FiberScanner#4)
                # if(regione in regioni.values()):
                #     aaa = ""
                #     province = getProvinceList()
                #     if(addresslist[1].upper().strip() in province):
                #         città = getCitiesList()
                #         if(addresslist[2].upper().strip() in città):
                #             vie = getSteetsList()
                #             if(addresslist[3].upper().strip() in vie):
                #                 numeri = getSteetsNumberList()
                #                 if(addresslist[4].upper().strip() in numeri):
                #                     aaa = ""

        if "callback_query" in messageReceived:

            chatId = messageReceived["callback_query"]["message"]["chat"]["id"]
            text = messageReceived["callback_query"]["message"]["text"]
            id = messageReceived["callback_query"]["data"]
            messageId = messageReceived["callback_query"]["message"]["message_id"]
            keyboard = {}
            colCount = 2
            textRet = ""
            data = {
                "chat_id": chatId,
                "text": textRet,
                "reply_markup": json.dumps(keyboard),
                "parse_mode": "html"
            }

            list = {}

            if(text == "Regioni:"):
                idRegion = int(id)
                list = getProvinceList(idRegion)
                textRet = "Province:"

            if(text == "Province:"):
                list = getCitiesList(id)
                colCount = 2
                textRet = "Città:"

            if(text == "Città:"):
                list = getSteetsList(id)
                colCount = 2
                textRet = "Via:"

            if(text == "Via:"):
                colCount = 2
                list = getSteetsNumberList(id)
                textRet = "Numero:"

            if(text == "Numero:"):
                colCount = 2
                AddresInfo = getAddressInfo(id)
                textRet = "Confermi l'indirizzo: {} {} {} {} {} {} ?".format(
                    AddresInfo.region, AddresInfo.city, AddresInfo.province, AddresInfo.ppn, AddresInfo.street, AddresInfo.number)
                keyboard = {
                    "inline_keyboard": [[{"text": "SI", "callback_data": AddresInfo.code}, {"text": "NO", "callback_data": "NO"}]]
                }

            if("Confermi l'indirizzo" in text):
                colCount = 2
                presente = False

                if(id == "NO"):
                    textRet = "<b>Peccato :&lt;</b>"
                else:
                    if(chatId in dictUserCode):
                        if id not in dictUserCode[chatId]:
                            dictUserCode[chatId].append(id)
                        else:
                            presente = True
                    else:
                        codes = [id]
                        dictUserCode[chatId] = codes
                    if(not presente):
                        tmpMess = getPageInfo(codes)
                        textRet = tmpMess + "<b>Aggiunto!!</b>"

                    else:
                        tmpMess = getPageInfo(codes)
                        textRet = tmpMess + "<b>Già presente!!</b>"
            if(text != "Numero:"):
                keyboard = dict_to_inline_keyboard(list, colCount)

            data["reply_markup"] = json.dumps(keyboard)
            data["text"] = textRet

            urlResponse = URL + "sendMessage"
            response = requests.post(url=urlResponse, data=data).json()

        return Response('Ok', status=200)
    else:
        return '<h1>Fibermap Bot</h1>'


def execCommand(cmd):
    # os.popen('ssh -R 80:localhost:5000 ssh.localhost.run').read()
    popen = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    for stdout_line in iter(popen.stdout.readline, ""):
        yield stdout_line

    popen.stdout.close()
    return_code = popen.wait()

    if return_code:
        raise subprocess.CalledProcessError(return_code, cmd)


if __name__ == '__main__':

    Thread(target=app.run).start()

    link = ''
    for path in execCommand(["ssh", "-R", "80:localhost:5000", "ssh.localhost.run"]):
        link = str(path)
        break

    pattern = r'(?<= or)(.*)(?=\\r)'
    links = re.findall(pattern, link)
    serverUrl = []

    if links:
        serverUrl = links[0].strip()
        print('URL TUNNELING: ' + serverUrl)

    # Get the Telegram bot's Token specified in the file "TOKEN.txt"
    tokenFile = open("TOKEN.txt", "r")
    token = tokenFile.read().strip('\n')
    URL = URL.format(token)

    # Get the public URL of the server specified in the file "URL.txt"
    if not serverUrl:
        serverUrlFile = open("URL.txt", "r")
        serverUrl = serverUrlFile.read().strip('\n')

    # Call to the telegram API to set the Webhook from the given server URL
    set_Webhook(serverUrl)

    cycleCheckData = Thread(target=cycle_master, args=())
    cycleCheckData.start()