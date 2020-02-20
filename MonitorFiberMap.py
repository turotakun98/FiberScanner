import requests
from bs4 import BeautifulSoup
import json
import Classes

AddressInfoes = set()


''' ------------------------------ FUNCTIONS ------------------------------ '''


def getRegionList():
    regionUrl = 'https://fibermap.it/api/region/list'
    r = requests.get(regionUrl)
    
    regionList = {}
    
    jsonData = r.json()
    columnsData = jsonData["data"]

    for colsData in columnsData:
        colData = colsData["data"]
        for columnData in colData:
            regionsData = columnData["data"]
            for regionData in regionsData:
                idRegion = regionData["id"]
                nameRegion = regionData["name"]
                regionList[idRegion] = nameRegion
        
    return regionList
      
def getProvinceList(idRegion):
    provincesUrl = 'https://fibermap.it/api/region/{}/provinces'.format(idRegion)
    r = requests.get(provincesUrl)
    
    jsonData = r.json()
    provinceList = jsonToDict(jsonData)
    return provinceList

def getCitiesList(idProvince):
    citiesUrl = 'https://fibermap.it/api/province/{}/cities'.format(idProvince)
    r = requests.get(citiesUrl)
    jsonData = r.json()
    citiesList = jsonToDict(jsonData)
    return citiesList

def getSteetsList(idCity):
    streetsUrl = 'https://fibermap.it/api/city/{}/streets'.format(idCity)
    r = requests.get(streetsUrl)
    jsonData = r.json()
    streetsList = jsonToDict(jsonData)
    return streetsList

def getSteetsNumberList(idStreet):
    streetNumbersUrl = 'https://fibermap.it/api/street/{}/street-numbers'.format(idStreet)
    r = requests.get(streetNumbersUrl)
    jsonData = r.json()
    streetNumbersList = jsonToDict(jsonData)
    return streetNumbersList

def getAddressInfo(idNumber):
    AddressUrl = 'https://fibermap.it/api/street-number/{}/services'.format(idNumber)
    r = requests.get(AddressUrl)
    jsonData = r.json()
        
    val = jsonData["data"]
    
    #for val in colData:
    id = val["code"]
    region = val["region"]
    province = val["province"]
    shortProvince = val["shortProvince"]
    city = val["city"]
    ppn = val["ppn"]
    street = val["street"]
    number = val["number"]
    AddresInfo = Classes.AddressInfo(region,city,shortProvince,province,ppn,street,number,id)
        
    return AddresInfo

    
    return streetNumbersList

def jsonToDict(jsonData):
    colData = jsonData["data"]
    List = {}

    for val in colData:
        id = val["id"]
        name = val["name"]
        List[id] = name
        
    return List


def getPageInfo(url):
        link = url[0]
        r = requests.get('https://fibermap.it/api/street-number/' + link + '/services')
        jsonData = r.json()
        data = jsonData["data"]

        region = data["region"]
        city = data["city"]
        shortProvince = data["shortProvince"]
        province = data["province"]
        ppn = data["ppn"]
        street = data["street"]
        number = data["number"]
        code = data["code"]

        services = data["service"]
        message = ""

        for service in services:            
            types = service["types"]
            for type in types:
                typeName = type["name"]
                typeAvailable = type["available"]
                typeMaxSpeed = type["maxSpeed"]
                
                message += "{}, Disponibile: {}, Vel. Max: {} \n \n".format(typeName, typeAvailable, typeMaxSpeed)
        
        return message

def reloadPageInfo(url,mode):
    link = url

    try:
        allarmedCodes = set()

        r = requests.get('https://fibermap.it/api/street-number/' + link + '/services')
        jsonData = r.json()
        data = jsonData["data"]
        
        region = data["region"]
        city = data["city"]
        shortProvince = data["shortProvince"]
        province = data["province"]
        ppn = data["ppn"]
        street = data["street"]
        number = data["number"]
        code = data["code"]

        found = False
        for addressInfo in AddressInfoes:
            if(addressInfo.code == code):
                address = addressInfo
                found = True
                break
        
        if(found == False):
            address = Classes.AddressInfo(region,city,shortProvince,province,ppn,street,number,code)
            AddressInfoes.add(address)


        services = data["service"]

        for service in services:
            if(service["name"] == "Fibra Ottica"):
                types = service["types"]
                for type in types:
                    typeName = type["name"]
                    typeAvailable = type["available"]
                    typeMaxSpeed = type["maxSpeed"]

                    alarm = address.InsUpdFiberInfo(typeName,typeAvailable,typeMaxSpeed)
                    
                    if(alarm == True):
                        allarmedCodes.add(code)

        
        if(mode == 1):
            return allarmedCodes

        elif(mode == 2):
            return address

    except Exception as e:
        print("Connection to URL <" + link + "> failed:" + str(e))
        return
