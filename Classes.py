class AddressInfo:
    def __init__(self, region, city, shortProvince, province, ppn, street, number, code):
        self.region = region
        self.city = city
        self.shortProvince = shortProvince
        self.province = province
        self.ppn = ppn
        self.street = street
        self.number = number
        self.code = code
        self.fiberTypes = set()

    def InsUpdFiberInfo(self, typeName, typeAvailable, typeMaxSpeed):
        found = False
        alarm = False

        for fiberType in self.fiberTypes:
            if(fiberType.typeName == typeName):
                found = True

                if(fiberType.typeAvailable != typeAvailable):
                    alarm = True
                
                fiberType.updateInfo(typeName, typeAvailable,typeMaxSpeed)

        if(found == False):
            newFiberType = FiberType(typeName, typeAvailable, typeMaxSpeed) 
            self.fiberTypes.add(newFiberType)
            return False

        return alarm

        

class FiberType:
    def __init__(self, typeName, typeAvailable,typeMaxSpeed):
        self.typeName = typeName
        self.typeAvailable = typeAvailable
        self.typeMaxSpeed = typeMaxSpeed

    def updateInfo(self, typeName, typeAvailable,typeMaxSpeed):
        self.typeName = typeName
        self.typeAvailable = typeAvailable
        self.typeMaxSpeed = typeMaxSpeed




class UserCode:
    def __init__(self, userID, code):
        self.userID = userID
        self.Code = code