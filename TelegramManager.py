import json
import time
from threading import Lock, Thread

import requests

from Classes import AddressInfo
from MonitorFiberMap import (
    getAddressInfo, getCitiesList, getProvinceList, getRegionList,
    getSteetsList, getSteetsNumberList, reloadPageInfo)

URL = "https://api.telegram.org/bot{}/"
last_update_id = 0

dictUserCode = {}

def get_url(url):
    response = requests.get(url)
    content = response.content.decode("utf8")
    return content


def get_json_from_url(url):
    content = get_url(url)
    js = json.loads(content)
    return js

def get_updates():
    global last_update_id

    url = URL + "getUpdates?offset={}".format(last_update_id)
    js = get_json_from_url(url)

    if(js["ok"] == True):
        leng = len(js["result"])
        if(leng > 0):
            last_update_id = js["result"][leng - 1]["update_id"] 
            last_update_id = last_update_id + 1
        
            #Salvataggio dell'ultimo update_id per impedire la rilettura dell'ultimo messaggio al riavvio del Bot
            #f = open("myfile.txt", "w")
            #f.write(str(last_update_id))
            #f.close()
    
    return js

def send_message(text, chat_id):
    url = URL + "sendMessage?text={}&chat_id={}".format(text, chat_id)
    get_url(url)
 
def dict_to_inline_keyboard(dict,columns):
    
    maxColumnIndex = columns - 1

    keyboard = {
            "inline_keyboard": []#[[]]
        }

    colIndex = 0
    rowIndex = -1

    for id,name in dict.items():
        val = {"text": name,"callback_data":str(id)}
                    
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

def cycle_master():
    while 1 == 1:
        listCodes = []
        listAlm = []
        for val in dictUserCode.values():
            for vall in val:
                if(vall not in listCodes):
                    listCodes.append(vall)

        for code in listCodes:
            alm = reloadPageInfo(code,1)
            listAlm.append(alm)

        time.sleep(10)

if __name__ == '__main__':
    
    tokenFile = open("TOKEN.txt", "r")
    token = tokenFile.read().strip('\n')

    URL = URL.format(token)
    cycleCheckData = Thread(target=cycle_master, args=())
    cycleCheckData.start()

    while 1 == 1:
        js_update = get_updates()

        for update in js_update["result"]:
            #TO DO: Metti in una funz
            if "message" in update:
                if(update["message"]["text"] == "/regioni"):
                    region_list = getRegionList()
                    keyboard = dict_to_inline_keyboard(region_list,2)
                    
                    chatId = update["message"]["chat"]["id"]
                    data = {
                        "chat_id": chatId,
                        "text" : "Regioni:",
                        "reply_markup": json.dumps(keyboard)
                    }

                    urlResponse = URL + "sendMessage"
                    response = requests.post(url=urlResponse,
                            data=data).json()

            if "callback_query" in update:
               
                #update["callback_query"]["message"]["reply_markup"]["inline_keyboard"]
                chatId = update["callback_query"]["message"]["chat"]["id"]
                text = update["callback_query"]["message"]["text"]
                id = update["callback_query"]["data"]
                chatId = update["callback_query"]["message"]["chat"]["id"]
                keyboard = {}
                colCount = 2
                textRet = ""
                data = {
                    "chat_id": chatId,
                    "text" : textRet,
                    "reply_markup": json.dumps(keyboard)
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
                    textRet = "Confermi l'indirizzo: {} {} {} {} {} {} ?".format(AddresInfo.region,AddresInfo.city,AddresInfo.province,AddresInfo.ppn,AddresInfo.street,AddresInfo.number)                    
                    keyboard = {
                            "inline_keyboard": [[{"text": "SI","callback_data":AddresInfo.code},{"text": "NO","callback_data":"NO"}]]
                        }

                if("Confermi l'indirizzo" in text):
                    colCount = 2
                    presente = False

                    if(id == "NO"):
                        textRet = "Peccato :<"
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
                            textRet = "Aggiunto!!"
                        else:
                            textRet = "Già presente!!"
                if(text != "Numero:"):
                    keyboard = dict_to_inline_keyboard(list,colCount)
                    
                data["reply_markup"] = json.dumps(keyboard)
                data["text"] = textRet

                urlResponse = URL + "sendMessage"
                response = requests.post(url=urlResponse, data=data).json()
        time.sleep(2)
