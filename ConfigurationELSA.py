#!/usr/bin/env python
# -*- coding: utf-8 -*-
import csv
import sets
import time
import traceback
import unicodecsv
import datetime
import random
import sys
import threading
import time
import os
import rrdtool
import ow
import serial
import myuseful as useful



#mise a jour git
csvDir = "csv/"
rrdDir = 'rrd/'
ttyDir = '/dev/ttyS0'
class Configuration():

    def __init__(self):
	self.InfoSystem = InfoSystem()
	self.csvCodes = csvDir + 'codes.csv'
	self.csvRelations = csvDir + 'relations.csv'
	self.fieldcode = ['begin', 'type', 'idobject', 'code', 'user']
	self.fieldrelations = ['begin', 'g_id', 'idobject', 'type', 'deny', 'user']
        self.AllUsers = AllUsers(self)
	self.AllLanguages = AllLanguages(self)
        self.AllPieces = AllPieces(self)
        self.AllContainers = AllContainers(self)
	self.AllMessages = AllMessages(self)
	self.AllEquipments = AllEquipments(self)
	self.AllGroups = AllGroups(self)
	self.AllMeasures = AllMeasures(self)
	self.AllSensors = AllSensors(self)
	self.AllAlarms = AllAlarms(self)
	self.AllHalflings = AllHalflings(self)
	self.connectedUsers = AllConnectedUsers()
	self.isThreading = True
	self.UpdateThread = UpdateThread(self)
	self.RadioThread = RadioThread(self)

    def load(self):
	self.AllLanguages.load()
        self.AllUsers.load()
        self.AllPieces.load()
	self.AllEquipments.load()
	self.AllContainers.load()	
	self.AllMessages.load()
	self.AllGroups.load()
	self.AllMeasures.load()
	self.AllSensors.load()
	self.AllAlarms.load()
	self.AllHalflings.load()
	#doit toujours être appelé à la fin
	self.loadCodes()
	self.loadRelation()
	self.UpdateThread.start()
	self.RadioThread.start()
	
    def loadCodes(self):
	with open(self.csvCodes) as csvfile:
	    reader = csv.DictReader(csvfile, delimiter = "\t")
            for row in reader:
		keyObj = row['idobject']
		keyType = row['type']
		objects = self.findAllFromType(keyType)
		currObject = objects.elements[keyObj]
		currObject.code = row['code']
    
    def findAllFromObject(self,anObject):
        className = anObject.__class__.__name__
        if className == u"User":
            return self.AllUsers
        elif className == u"Equipment":
            return self.AllEquipments
        elif className == u"Language":
            return self.AllLanguages
	elif className == u"Piece":
	    return self.AllPieces 
	elif className == u"Group":
	    return self.AllGroups 
	elif className == u"Container":
	    return self.AllContainers 
	elif className == u"Measure":
	    return self.AllMeasures 
	elif className == u"Sensor":
	    return self.AllSensors 
	elif className == u"Alarm":
	    return self.AllAlarms 
        else:
            return None
	    
    def getObject(self, idObject,className):
	if className == u"WebUser" or className == u"u":
            return self.AllUsers.getItem(idObject)
        elif className == u"WebEquipment" or className == u"e":
            return self.AllEquipments.getItem(idObject)
        elif className == u"Language":
            return self.AllLanguages.getItem(idObject)
	elif className == u"WebPlace" or className == u"p":
	    return self.AllPieces.getItem(idObject)
	elif className == u"WebGroup" or className == u"g":
	    return self.AllGroups.getItem(idObject)
	elif className == u"WebContainer" or className == u"c":
	    return self.AllContainers.getItem(idObject)
	elif className == u"WebMeasure" or className == u"m":
	    return self.AllMeasures.getItem(idObject)
	elif className == u"WebSensor" or className == u"cpehm":
	    return self.AllSensors.getItem(idObject)
	elif className == u"WebAlarm" or className == u"a":
	    return self.AllAlarms.getItem(idObject)
        else:
            return None
    
    def getFieldsname(self,className):
        if className == u"WebUser":
            return self.AllUsers.fieldnames
        elif className == u"WebEquipment":
            return self.AllEquipments.fieldnames
        elif className == u"Language":
            return self.AllLanguages.fieldnames
	elif className == u"WebPlace":
	    return self.AllPieces.fieldnames  
	elif className == u"WebGroup":
	    return self.AllGroups.fieldnames  
	elif className == u"WebContainer":
	    return self.AllContainers.fieldnames  
	elif className == u"WebMeasure":
	    return self.AllMeasures.fieldnames  
	elif className == u"WebSensor":
	    return self.AllSensors.fieldnames 
	elif className == u"WebAlarm":
	    return self.AllAlarms.fieldnames
        else:
            return None
	    
    def getKeyColumn(self, anObject):
	obj = self.findAllFromObject(anObject)
	return obj.keyColumn
	
    def findAllFromType(self, aType):
        if aType == u"u":
            return self.AllUsers
        elif aType == u"e":
            return self.AllEquipments
        elif aType == u"l":
            return self.AllLanguages
	elif aType == u"p":
	    return self.AllPieces 
	elif aType == u"g":
	    return self.AllGroups
	elif aType == u"c":
	    return self.AllContainers
	elif aType == u"m":
	    return self.AllMeasures
	elif aType == u"cpehm":
	    return self.AllSensors
	elif aType == u"a":
	    return self.AllAlarms
        else:
            return None
	    
    def loadRelation(self):
	with open(self.csvRelations) as csvfile:
	    reader = csv.DictReader(csvfile, delimiter = "\t")
	    for row in reader:
		keyObj = row['idobject']
		keyGroup = row['g_id']
		keyType = row['type']
		objects = self.findAllFromType(keyType)
		currObject = objects.elements[keyObj]
		if row['deny'] =='0':		    
		    currObject.groups[keyGroup] = self.AllGroups.elements[keyGroup]
		elif row['deny'] == '1' :
		    currObject.removekey(keyGroup)
		    
    
    def createHierarchy(self):
	children = {}
	for k,group in self.AllGroups.elements.items():
	    if len(group.groups) > 0:
		for i,g in group.groups.items():
		    if i in children:
			del children[i]
		children[k] = group
	return children
    
    def hierarchyString(self, lang, g = None, myString = None):
	if myString is None:
	    myString = []
	for k,group in self.AllGroups.elements.items():
	    cond1 = ( g == None and len(group.groups) == 0 )
	    cond2 = ( g is not None and g.fields['g_id'] in group.groups )
	    if cond1 or cond2:
		myString.append(group.getName(lang))
		myString.append('IN')
		self.hierarchyString(lang,group,myString)
		myString.append('OUT')
	return myString
		
	
    def clearInOut(self,myList):
	i = 0
	tmp = []
	while i < len(myList):
	    if myList[i] == 'IN' and myList[i+1] == 'OUT':
		i+=2
	    else :
		tmp.append(myList[i])
		i+=1
	return tmp
	

class InfoSystem():
    
    def __init__(self):
	self.uptime = 0
	self.memTot = 0
	self.memFree = 0
	self.memAvailable = 0
	self.load1 = 0
	self.load5 = 0
	self.load15 = 0
	self.temperature = 0	
	
    def updateInfoSystem(self,now):
	try:
	    info = os.popen('cat /proc/uptime','r')
	    info = info.read()
	    info = info.split(' ')
	    self.uptime = int(float(info[0]))
	    rrdtool.update('rrd/systemuptime.rrd' , '%d:%d' % (now , self.uptime))
	    
	    info = os.popen('cat /sys/class/thermal/thermal_zone0/temp','r')
	    info = info.read()
	    self.temperature = float(info.split('\n')[0])/1000.0
	    rrdtool.update('rrd/temperaturecpu.rrd' , '%d:%f' % (now , self.temperature))
	    
	    info = os.popen('cat /proc/meminfo','r')
	    info = info.read()
	    info = info.split('\n')
	    self.memTot = info[0]
	    self.memFree = info[1]
	    self.memAvailable = info[2]
	    self.memTot = self.memTot.split(':')[1]
	    self.memFree = self.memFree.split(':')[1]
	    self.memAvailable = self.memAvailable.split(':')[1]
	    self.memTot = self.memTot.split(' ')[-2]
	    self.memFree = self.memFree.split(' ')[-2]
	    self.memAvailable = self.memAvailable.split(' ')[-2]
	    self.memTot = float(self.memTot)
	    self.memFree = float(self.memFree)
	    self.memAvailable = float(self.memAvailable)
	    self.memTot /= 1000.0
	    self.memFree /= 1000.0
	    self.memAvailable /= 1000.0
	    rrdtool.update('rrd/memoryinfo.rrd' , '%d:%f:%f:%f' % (now , self.memTot, self.memFree, self.memAvailable))
	    
	    info = os.popen('cat /proc/loadavg')
	    info = info.read()
	    info = info.split(' ')
	    self.load1 = float(info[0])
	    self.load5 = float(info[1])
	    self.load15 = float(info[2])
	    rrdtool.update('rrd/cpuload.rrd' , '%d:%f:%f:%f' % (now , self.load1, self.load5, self.load15))
	except:
	    traceback.print_exc()

class ConfigurationObject():

    def __init__(self):
        self.fields = {}
	self.names = {}
	self.groups = {}
        self.id = None
	self.created = None
	self.creator = None
	self.code = None
	
    def save(self,configuration,anUser=""):
        self.fields["begin"] = unicode(datetime.datetime.now().strftime("%H:%M:%S  -  %d/%m/%y"))
        self.fields["user"] = anUser.fields['u_id']
        allObjects = configuration.findAllFromObject(self)
	print allObjects.fileobject
        print allObjects.fieldnames
        with open(allObjects.fileobject,"a") as csvfile:
            writer = unicodecsv.DictWriter(csvfile, delimiter = '\t', fieldnames=allObjects.fieldnames, encoding="utf-8")
            writer.writerow(self.fields)
	self.saveName(configuration, anUser)
	if not self.code == '':
	    self.saveCode(configuration, anUser)	
        return self
	
    def saveName(self, configuration, anUser):
	allObjects = configuration.findAllFromObject(self)
	print self.fields
	print self.names    
	for key in self.names :
	    print key
	    print allObjects.fieldtranslate
	    with open(allObjects.filename,"a") as csvfile:
		writer = unicodecsv.DictWriter(csvfile, delimiter = '\t', fieldnames=allObjects.fieldtranslate, encoding="utf-8")
		writer.writerow(self.names[key])
	
    def saveCode(self, configuration,anUser):
	allObjects = configuration.findAllFromObject(self)
	print self.code	
	with open(configuration.csvCodes,"a") as csvfile:
	    tmpCode={}
	    tmpCode['begin'] = unicode(datetime.datetime.now().strftime("%H:%M:%S  -  %d/%m/%y"))
	    tmpCode['type'] = self.getType()
	    tmpCode['idobject'] = self.fields[allObjects.keyColumn]
	    tmpCode['code'] = self.code
	    tmpCode["user"] = anUser.fields['u_id']
            writer = unicodecsv.DictWriter(csvfile, delimiter = '\t', fieldnames = configuration.fieldcode, encoding="utf-8")
            writer.writerow(tmpCode)
	
    def saveGroups(self, configuration,anUser):
	print self.groups	
	allObjects = configuration.findAllFromObject(self)
	with open(configuration.csvRelations,"a") as csvfile:
	    for k,v in self.groups.items():
		tmpCode={}
		tmpCode['begin'] = unicode(datetime.datetime.now().strftime("%H:%M:%S  -  %d/%m/%y"))
		tmpCode['g_id'] = k
		tmpCode['idobject'] = self.fields[allObjects.keyColumn]
		tmpCode['type'] = self.getType()
		tmpCode["user"] = anUser.fields['u_id']
		tmpCode['deny'] = '0'
		writer = unicodecsv.DictWriter(csvfile, delimiter = '\t', fieldnames = configuration.fieldrelations, encoding="utf-8")
		writer.writerow(tmpCode)
	
    def initialise(self, fieldsname):
	for field in fieldsname:
	    self.fields[field]=''
	    
    def getImageDirectory(self):
	directory='static/img'
        if self.__class__.__name__ == u"User":
            return directory + '/u/user_'+self.fields['u_id']+'.'
        elif self.__class__.__name__  == u"Equipment":
            return directory + '/e/equipment_'+self.fields['e_id']+'.'
        elif self.__class__.__name__ == u"Piece":
            return directory + '/p/place_'+self.fields['p_id']+'.'  
	elif self.__class__.__name__ == u"Group":
            return directory + '/g/group_'+self.fields['g_id']+'.' 
	elif self.__class__.__name__ == u"Container":
            return directory + '/c/group_'+self.fields['c_id']+'.' 
        else:
            return None

    def setName(self,key,value,user,keyColumn):
	if value != '' and value is not None:
	    newName={}
	    newName["begin"] = unicode(datetime.datetime.now().strftime("%H:%M:%S  -  %d/%m/%y"))
	    newName['user'] = user.fields['u_id']
	    newName['lang'] = key
	    newName['name'] = value
	    newName[keyColumn] = self.fields[keyColumn]
	    self.names[key] = newName
	    
    def getName(self,lang):
	if lang in self.names :
	    return self.names[lang]['name']
	elif 'EN' in self.names : 
	    return self.names['EN']['name']
	elif 'FR' in self.names:
	    return self.names['FR']['name']
	elif 'DE' in self.names:
	    return self.names['DE']['name']
	elif len(self.names) > 0:
	    return self.names.values()[0]['name']
	elif 'default' in self.fields:
	    return self.fields['default']
	else:
	    print "Error Le nom n'existe pas pour cet objet"
	    return "Error"
	    
		
    def deleteGroup(self,groupid, configuration,anUser):
	print self.groups	
	allObjects = configuration.findAllFromObject(self)
	with open(configuration.csvRelations,"a") as csvfile:
	    tmpCode={}
	    tmpCode['begin'] = unicode(datetime.datetime.now().strftime("%H:%M:%S  -  %d/%m/%y"))
	    tmpCode['g_id'] = groupid
	    tmpCode['idobject'] = self.fields[allObjects.keyColumn]
	    tmpCode['type'] = self.getType()
	    tmpCode["user"] = anUser.fields['u_id']
	    tmpCode['deny'] = '1'
	    writer = unicodecsv.DictWriter(csvfile, delimiter = '\t', fieldnames = configuration.fieldrelations, encoding="utf-8")
	    writer.writerow(tmpCode)
	    
    def removekey(self, key):
	del self.groups[key]
	
    def containsGroup(self, oGroup):
	if len(self.groups) >0:
	    for k,v in self.groups.items():
		if v.containsGroup(oGroup):
		    return True
	return False

class UpdateThread(threading.Thread):

    def __init__(self,config):
        threading.Thread.__init__(self)
        self.config = config

    def run(self):
	ow.init("/dev/i2c-1")
        owDevices = ow.Sensor("/")
	time.sleep(60)
	while self.config.isThreading:
	    now = useful.get_timestamp()
	    self.config.InfoSystem.updateInfoSystem(now)
	    if not len(self.config.AllSensors.elements) == 0 :
		for k,sensor in self.config.AllSensors.elements.items():
		    if sensor.fields['channel'] == 'wire':
			try:
                            sensorAdress = '/'+str(sensor.fields['sensor'])
			    aDevice = ow.Sensor(sensorAdress)
			    if aDevice:
				owData = aDevice.__getattr__(sensor.fields['subsensor'])
				if owData:
				    if sensor.fields['formula']:
					value = float(owData)
					owData = str(eval(sensor.fields['formula']))
				    print (u"Sensor 1Wire-" + sensor.getName('EN')+u": " + sensor.fields['acronym'] + " = " + owData)
				    sensor.updateRRD(now,float(owData))
			except:
			    traceback.print_exc()
	    time.sleep(60)
	    
class RadioThread(threading.Thread):

    def __init__(self,config):
        threading.Thread.__init__(self)
        self.config = config

    def run(self):
        try:
	    elaSerial = serial.Serial(ttyDir,9600,timeout=0.01)
	    time.sleep(0.05)
	    #reset to manufacturer settings
	    elaSerial.write('[9C5E01]')
	    line = None
	    while self.config.isThreading:
		try:
		    data = elaSerial.read()
		    now = useful.get_timestamp()
		    if data == '[' :
			line = []
		    elif line != None:
			if data == ']' :
			    if len(line) == 10:
				RSS = int(line[0]+line[1],16)
				HEX = line[2]+line[3]+line[4]
				ADDRESS = int(HEX,16)
				VAL = int(line[5]+line[6]+line[7],16)
				READER = int(line[8]+line[9],16)
				if VAL >= 2048:
				    VAL = VAL - 4096
				temperature = VAL*60.0/960
				print "ELA="+HEX+", RSS="+str(RSS)+", val="+str(VAL)
				currSensor = None
				for sensor in self.config.AllSensors.elements:
				    currSensor = self.config.AllSensors.elements[sensor]
				    if (currSensor.fields['sensor'].translate(None, '. ') == HEX.translate(None, '. ')):
					print (u"Sensor ELA-" + currSensor.fields['sensor']+ u": " + currSensor.fields['acronym'] +u" = "+str(temperature))
					currSensor.updateRRD(now,temperature)
			    line = None
			else:
			    line.append(data)
		except:
		    traceback.print_exc()   
	    elaSerial.close()
        except:
	    traceback.print_exc()
	    self.config.isThreading = False
        
class UpdateAlarm(threading.Thread):

    def __init__(self, sensor, time):
        threading.Thread.__init__(self)
        self.sensor = sensor
	self.time = time

    def run(self):
	ow.init("/dev/i2c-1")
        owDevices = ow.Sensor("/")
	time.sleep(int(self.time))
	if self.sensor.fields['channel'] == 'wire':
	    try:
		sensorAdress = '/'+str(self.sensor.fields['sensor'])
		aDevice = ow.Sensor(sensorAdress)
		if aDevice:
		    owData = aDevice.__getattr__(self.sensor.fields['subsensor'])
		    if owData:
			if self.sensor.fields['formula']:
			    value = float(owData)
			    owData = str(eval(self.sensor.fields['formula']))
			print (u"SENSOR ALARM 1Wire-" + self.sensor.getName('EN')+u": " + self.sensor.fields['acronym'] + " = " + owData)
			self.sensor.comeFromUpdateAlarm(owData)
	    except:
		traceback.print_exc()
	

class AllObjects():

    def __init__(self):
	self.fileobject = None
        self.filename = None
        self.keyColumn = None
	self.count = 0
	
    def load(self):
	self.loadFields()
	if self.filename is not None :
	    self.loadNames()

    def loadFields(self):
        with open(self.fileobject) as csvfile:
            reader = csv.DictReader(csvfile, delimiter = "\t")
            for row in reader:
		key = row[self.keyColumn]
		currObject = self.newObject()
		currObject.fields = row
		currObject.id = key
		if key in self.elements :
		    currObject.created = self.elements[key].created
		    currObject.creator = self.elements[key].creator
		else :
		    currObject.created = currObject.fields['begin']
		    currObject.creator = row['user']
		self.elements[key] = currObject
		
    def loadNames(self):
	with open(self.filename) as csvfile:
	    reader = csv.DictReader(csvfile, delimiter = "\t")
            for row in reader:
		keyObj = row[self.keyColumn]
		keyLang = row['lang']
		currObject = self.elements[keyObj]
		currObject.names[keyLang] = row
		

    def newObject(self):
        return None
	
    def initCount(self):
	for k,v in self.elements.items():
	    if self.count < int(v.fields[self.keyColumn]):
		self.count = int(v.fields[self.keyColumn])
		
    def getNewId(self):
	if self.count == 0 :
	    self.initCount()
	self.count +=1
	return self.count
	
    def createObject(self):
	currObject = self.newObject()
	currObject.initialise(self.fieldnames)
	self.initCount()
	tmp = self.getNewId()
	currObject.fields[self.keyColumn] = str(tmp)
	currObject.id = tmp
	self.elements[str(tmp)] = currObject
	currObject.fields["begin"] = unicode(datetime.datetime.now().strftime("%H:%M:%S  -  %d/%m/%y"))
	return currObject
	
    def uniqueAcronym(self, acronym):
	for k in self.elements.keys():
	    if self.elements[k].fields['acronym'] == acronym:
		return false
	return true
	
    def getItem(self,iditem):
	if iditem == 'new':
	    return self.createObject()
	elif iditem in self.elements.keys():
	    return self.elements[iditem]
	return None
	    
	        
class AllUsers(AllObjects):

    def __init__(self, config):
	AllObjects.__init__(self)
        self.elements = {}
        self.config = config
        self.fileobject = csvDir + "U.csv"
	self.filename = csvDir + "Unames.csv"
        self.keyColumn = "u_id"
	self.fieldnames = ['begin', 'u_id', 'deny', 'acronym', 'remark', 'registration', 'mail', 'password', 'language', 'user']
	self.fieldtranslate = ['begin', 'lang', 'u_id', 'name', 'user']

    def newObject(self):
        return User()
	
    def checkUser(self,mail, password):
	for user in self.elements.value():
	    if user.fields['mail'] == mail:
		return user.checkPassword(password)
    def getUser(self,mail):
	for myId,user in self.elements.items():
	    if user.fields['mail']==mail:
		return user
		

class AllRoles(AllObjects):

    def __init__(self, config):
        self.elements = {}
        self.config = config
        self.filename = csvDir + "O.csv"
        self.keyColumn = "o_id"

    def load(self):
        with open(self.filename) as csvfile:
            reader = csv.DictReader(csvfile, delimiter = "\t")
            for row in reader:
                if((not 'deny' in row) or (row['deny'] != "1")):
                    key = row[self.keyColumn]
                    currObject = self.newObject()
                    currObject.fields = row
                    currObject.id = key
                    self.elements[key] = currObject
                else:
                    print self.filename+': '+row['name'] + " is denied !"
                
    def newObject(self):
        return Role()
    
class AllUO():

    def __init__(self, config):
        self.config = config

    def load(self):
        with open(csvDir + "UO.csv") as csvfile:
            reader = csv.DictReader(csvfile, delimiter = "\t")
            for row in reader:
                if((not 'deny' in row) or (row['deny'] != "1")):
                    for user in self.config.AllUsers.elements: 
                        if (self.config.AllUsers.elements[user].fields['u_id'] == row['u_id']):
                            self.config.AllUsers.elements[user].roles.add(row['o_id'])
                    for role in self.config.AllRoles.elements: 
                        if (self.config.AllRoles.elements[role].fields['o_id'] == row['o_id']):
                            self.config.AllRoles.elements[role].users.add(row['u_id'])
                else:
                    print self.filename+': '+row['name'] + " is denied !"

class AllEquipments(AllObjects):

    def __init__(self, config):
	AllObjects.__init__(self)
        self.elements = {}
        self.config = config
        self.fileobject = csvDir + "E.csv"
	self.filename = csvDir + "Enames.csv"
        self.keyColumn = "e_id"
	self.fieldnames = ["begin", "e_id", "deny", "acronym", "remark",'colorgraph', "user"]
	self.fieldtranslate = ['begin', 'lang', 'e_id', 'name', 'user']

    def newObject(self):
        return Equipment()

class AllContainers(AllObjects):

    def __init__(self, config):
	AllObjects.__init__(self)
        self.elements = {}
        self.config = config
        self.fileobject = csvDir + "C.csv"
	self.filename = csvDir + "Cnames.csv"
        self.keyColumn = "c_id"
	self.fieldnames = ["begin", "c_id", "deny", "acronym", "remark",'colorgraph', "user"]
	self.fieldtranslate = ['begin', 'lang', 'c_id', 'name', 'user']

    def newObject(self):
        return Container()	

class AllPieces(AllObjects):

    def __init__(self, config):
	AllObjects.__init__(self)
        self.elements = {}
        self.config = config
        self.fileobject = csvDir + "P.csv"
	self.filename = csvDir + "Pnames.csv"
        self.keyColumn = "p_id"
	self.fieldnames = ['begin', 'p_id', 'deny', 'acronym', 'remark','colorgraph', 'user']
	self.fieldtranslate = ['begin', 'lang', 'p_id', 'name', 'user']
	self.count = 0

    def newObject(self):
	return Piece()
	
class AllHalflings(AllObjects):

    def __init__(self, config):
	AllObjects.__init__(self)
        self.elements = {}
        self.config = config
        self.fileobject = csvDir + "halflings.csv"
	self.filename = None
        self.keyColumn = "classname"
	self.fieldnames = ['begin', 'p_id', 'deny', 'acronym', 'remark','colorgraph', 'user']
	self.fieldtranslate = None
	self.count = 0

    def newObject(self):
	return Halfling()
	
    def getString(self):
	tmp=''
	for k,v in self.elements.items():
	    tmp = tmp + k + '/' + v.fields['glyphname'] + ' '
	return tmp[0:-1]
	
class AllAlarms(AllObjects):

    def __init__(self, config):
	AllObjects.__init__(self)
        self.elements = {}
        self.config = config
        self.fileobject = csvDir + "A.csv"
	self.filename = csvDir + "Anames.csv"
        self.keyColumn = "a_id"
	self.fieldnames = ['begin', 'a_id', 'deny', 'acronym', 'o_sms1', 'o_sms2', 'o_email1', 'o_email2', 'sound1', 'sound2', 'relay1', 'relay2', 'remark', 'user']
	self.fieldtranslate = ['begin', 'lang', 'a_id', 'name', 'user']

    def newObject(self):
	return Alarm()	
    
class AllGroups(AllObjects):

    def __init__(self, config):
	AllObjects.__init__(self)
        self.elements = {}
        self.config = config
        self.fileobject = csvDir + "G.csv"
	self.filename = csvDir + "Gnames.csv"
        self.keyColumn = "g_id"
	self.fieldnames = ["begin", "g_id", "deny", "acronym", "remark", "user"]
	self.fieldtranslate = ['begin', 'lang', 'g_id', 'name', 'user']

    def newObject(self):
        return Group()
	

class AllMeasures(AllObjects):

    def __init__(self, config):
	AllObjects.__init__(self)
        self.elements = {}
        self.config = config
        self.fileobject = csvDir + "M.csv"
	self.filename = csvDir + "Mnames.csv"
        self.keyColumn = "m_id"
	self.fieldnames = ['begin', 'm_id', 'deny', 'acronym', 'unit', 'source', 'formula', 'remark', 'user']
	self.fieldtranslate = ['begin', 'lang', 'm_id', 'name', 'user']
	self.count = 0

    def newObject(self):
        return Measure()

class AllSensors(AllObjects):

    def __init__(self, config):
        AllObjects.__init__(self)
        self.elements = {}
        self.config = config
        self.fileobject = csvDir + "CPEHM.csv"
	self.filename = csvDir + "CPEHMnames.csv"
        self.keyColumn = "cpehm_id"
	self.fieldnames = ['begin', 'cpehm_id', 'c_id', 'p_id', 'e_id', 'h_id', 'm_id', 'deny', 'acronym', 'remark', 'channel', 'sensor', 'subsensor', 'valuetype', 'formula', 'minmin', 'min', 'typical', 'max', 'maxmax', 'a_minmin', 'a_min', 'a_typical', 'a_max', 'a_maxmax', 'lapse1', 'lapse2', 'lapse3', 'user']
	self.fieldtranslate = ['begin', 'lang', 'cpehm_id', 'name', 'user']
	self.count = 0

    def newObject(self):
        return Sensor()
	
    def getColor(self, ids):
	color = "#006600"
	if ids in self.elements:
	    sensor = self.elements[ids]
	    if not sensor.fields['p_id'] == '':
		pid = sensor.fields['p_id']
		if not self.config.AllPieces.elements[pid].fields['colorgraph'] == '':
		    color = self.config.AllPieces.elements[pid].fields['colorgraph']
	    elif not sensor.fields['c_id'] == '':
		cid = sensor.fields['c_id']
		if not self.config.AllContainers.elements[cid].fields['colorgraph'] == '':
		    color = self.config.AllContainers.elements[cid].fields['colorgraph'] 
	    elif not sensor.fields['e_id'] == '':
		eid = sensor.fields['e_id']
		if not self.config.AllEquipments.elements[eid].fields['colorgraph'] == '':
		    color = self.config.AllEquipments.elements[eid].fields['colorgraph'] 
	return color

class AllBatches(AllObjects):

    def __init__(self, config):
        self.elements = {}
        self.config = config
        self.filename = csvDir + "B.csv"
        self.keyColumn = "b_id"

    def newObject(self):
        return Batch(self.config)

class AllBarcodes(AllObjects):

    def __init__(self, config):
        self.elements = {}
        self.config = config
        self.filename = csvDir + "K.csv"
        self.keyColumn = "k_id"

    def newObject(self):
        return Barcode()

class AllPhases(AllObjects):

    def __init__(self, config):
        self.elements = {}
        self.config = config
        self.filename = csvDir + "H.csv"
        self.keyColumn = "h_id"

    def newObject(self):
        return Phase()



class AllStepMeasures(AllObjects):
    
    def __init__(self, config):
        self.elements = {}
        self.config = config
        self.filename = csvDir + "RPEHMA.csv"
        self.keyColumn = "r_id"
        self.keyColumn2 = "p_id"
        self.keyColumn3 = "e_id"
        self.keyColumn4 = "h_id"
        self.keyColumn5 = "m_id"

    def load(self):
        with open(self.filename) as csvfile:
            reader = csv.DictReader(csvfile, delimiter = "\t")
            for row in reader:
                if((not 'deny' in row) or (row['deny'] != "1")):
                    key = row[self.keyColumn] + "-" + row[self.keyColumn2] + "-" + row[self.keyColumn3] + "-" + row[self.keyColumn4] + "-" + row[self.keyColumn5]
                    currObject = self.newObject()
                    currObject.fields = row
                    currObject.id = key
                    self.elements[key] = currObject
                else:
                    print self.filename+': '+row['name'] + " is denied !"

    def newObject(self):
        return StepMeasure()

class AllSteps(AllObjects):

    def __init__(self, config):
        self.elements = {}
        self.config = config
        self.filename = csvDir + "RPEHMA.csv"
        self.keyColumn = "seq"
        self.recipe = None

    def load(self, recipe):
        self.recipe = recipe
        with open(self.filename) as csvfile:
            reader = csv.DictReader(csvfile, delimiter = "\t")
            for row in reader:
                if ((not 'deny' in row) or (row['deny'] != "1")) and (row['r_id'] == self.config.AllRecipes.elements[self.recipe].id):
                    key = row[self.keyColumn]
                    if (key not in self.elements):
                        currObject = self.newObject()
                        currObject.fields = {'r_id':row['r_id'],'p_id':row['p_id'],'e_id':row['e_id'],'h_id':row['h_id'],'seq':row['seq']}
                        currObject.id = key
                        self.elements[key] = currObject
            for stepmeasure in self.config.AllStepMeasures.elements:
                for seq in self.elements:
                    if (self.config.AllStepMeasures.elements[stepmeasure].fields['r_id'] == self.elements[seq].fields['r_id'] and self.config.AllStepMeasures.elements[stepmeasure].fields['p_id'] == self.elements[seq].fields['p_id'] and self.config.AllStepMeasures.elements[stepmeasure].fields['e_id'] == self.elements[seq].fields['e_id'] and self.config.AllStepMeasures.elements[stepmeasure].fields['h_id'] == self.elements[seq].fields['h_id']):
                        self.elements[seq].stepmeasures[self.config.AllStepMeasures.elements[stepmeasure].fields['m_id']] = self.config.AllStepMeasures.elements[stepmeasure]

    def newObject(self):
        return Step()        

class AllRecipes(AllObjects):

    def __init__(self, config):
        self.elements = {}
        self.config = config
        self.filename = csvDir + "R.csv"
        self.keyColumn = "r_id"

    def load(self):
        with open(self.filename) as csvfile:
            reader = csv.DictReader(csvfile, delimiter = "\t")
            for row in reader:
                if((not 'deny' in row) or (row['deny'] != "1")):
                    key = row[self.keyColumn]
                    currObject = self.newObject()
                    currObject.fields = row
                    currObject.id = key
                    currObject.recipe = row['r_id']
                    self.elements[key] = currObject
                else:
                    print self.filename+': '+row['name'] + " is denied !"

    def newObject(self):
        return Recipe(self.config)

class AllScanners(AllObjects):

    def __init__(self, config):
        self.elements = {}
        self.config = config
        self.filename = csvDir + "S.csv"
        self.keyColumn = "s_id"

    def makeKey(self, MAC):
        return hash(MAC.upper()) % 1000

    def load(self):
        with open(self.filename) as csvfile:
            reader = csv.DictReader(csvfile, delimiter = "\t")
            i = 0;
            for row in reader:
                if((not 'deny' in row) or (row['deny'] != "1")):
                    key = mac = None
                    if self.keyColumn in row:
                        key = row[self.keyColumn]
                    if 'mac' in row:
                        mac = row['mac'].upper()
                    if mac and not key:
                        key = self.makeKey(mac)
                    currObject = self.newObject()
                    currObject.fields = row
                    currObject.id = key
                    currObject.mac = mac
                    currObject.rank = i
                    self.elements[key] = currObject
                    i+=1
                else:
                    print self.filename+': '+row['name'] + " is denied !"

    def newObject(self):
        return Scanner()

class ConnectedUser():
    
    def __init__(self, user):
	self.cuser = user
	self.datetime = time.time()
	
    def update(self):
	self.datetime = time.time()
    
class AllConnectedUsers():
    
    def __init__(self):
	self.users = {}
    
    def __getitem__(self,key):
	return self.users[key]
    
    def addUser(self,user):
	self.update()
	mail = user.fields['mail']
	if mail not in self.users :
	    self.users[mail] = ConnectedUser(user)
	else :
	    self.users[mail].update()
	
    def update(self):
	updatetime = time.time()
	for mail,connecteduser in self.users.items():
	    if (updatetime - connecteduser.datetime) > 900:
		del self.users[mail]
		
    def isConnected(self,mail,password):
	self.update()
	if mail in self.users :
	    user = self.users[mail].cuser
	    if user.fields['password'] == password :
		self.users[mail].update()
		return True
	return False
    
    def getLanguage(self, mail):
	if mail in self.users:
	    return self.users[mail].cuser.fields['language']
	return 'english'
			
class AllLanguages(AllObjects):

    def __init__(self, config):
        self.elements = {}
        self.config = config
        self.fileobject = csvDir + "language.csv"
	self.filename = None
        self.keyColumn = "l_id"
	self.nameColumn = "name"

    def newObject(self):
        return Language()
	
    def __getitem__(self,key):
	return self.elements[key]
	
class AllMessages(AllObjects):

    def __init__(self, config):
        self.elements = {}
	self.names = {}
        self.config = config
	self.fileobject = csvDir + "mess.csv"
        self.filename = csvDir + "messages.csv"
        self.keyColumn = "m_id"
	self.nameColumn = "name"

    def newObject(self):
        return Message()
	
    def __getitem__(self,key):
	return self.elements[key]

  

class Language(ConfigurationObject):
    
    def __init__(self):
	ConfigurationObject.__init__(self)

    def __repr__(self):
        string = self.id + " " + self.fields['name']
        return string

    def __str__(self):
        string = "\nLanguage :"
        for field in self.fields:
            string = string + "\n" + field + " : " + self.fields[field]
        return string + "\n"

class Message(ConfigurationObject):
    
    

    def __repr__(self):
        string = self.id + " " + self.fields['default']
        return string

    def __str__(self):
        string = "\nMessage :"
        for field in self.fields:
            string = string + "\n" + field + " : " + self.fields[field]
        return string + "\n"	
	

class User(ConfigurationObject):

    def __init__(self):
	ConfigurationObject.__init__(self)
        self.roles = sets.Set()
        self.context = Context()

    def __repr__(self):
        string = self.id + " " + self.fields['acronym']
        return string

    def __str__(self):
        string = "\nUtilisateur :"
        for field in self.fields:
            string = string + "\n" + field + " : " + str(self.fields[field])
        return string + "\n"
	
    def checkPassword(self,password):
	return self.fields['password']==password
	
    def getType(self):
	return 'u'

	    
class Role(ConfigurationObject):

    def __init__(self):
        self.users = sets.Set()

    def __repr__(self):
        string = self.id + " " + self.fields['name']
        return string

    def __str__(self):
        string = "\nRole :"
        for field in self.fields:
            string = string + "\n" + field + " : " + self.fields[field]
        return string + "\n"

class Equipment(ConfigurationObject):

    def __init__(self):
	ConfigurationObject.__init__(self)

    def __repr__(self):
        string = self.id + " " + self.fields['acronym']
        return string

    def __str__(self):
        string = "\nEquipement :"
        for field in self.fields:
            string = string + "\n" + field + " : " + self.fields[field]
        return string + "\n"
	
    def getType(self):
	return 'e'

class Container(ConfigurationObject):

    def __init__(self):
	ConfigurationObject.__init__(self)

    def __repr__(self):
        string = self.id + " " + self.fields['acronym']
        return string

    def __str__(self):
        string = "\nContainer :"
        for field in self.fields:
            string = string + "\n" + field + " : " + self.fields[field]
        return string + "\n"
	
    def getType(self):
	return 'c'
	
class Group(ConfigurationObject):

    def __init__(self):
	ConfigurationObject.__init__(self)
	self.classes = {}
	self.groups = {}

    def __repr__(self):
        string = str(self.id) + " " + self.fields['acronym']
        return string

    def __str__(self):
        string = "\nGroup :"
        for field in self.fields:
            string = string + "\n" + field + " : " + self.fields[field]
        return string + "\n"
	
    def getType(self):
	return 'g'
	
    def containsGroup(self, oGroup):
	if len(self.groups) >0:
	    for k,v in self.groups.items():
		if 'g_id' in oGroup.fields.keys():
		    if k == oGroup.fields['g_id'] :
			return True
		elif v.containsGroup(oGroup):
		    return True
	return False
	
    def addGroup(self, oGroup):
	currContainsGroup = currObject.containsGroup(group)
	groupContainsCurr = group.containsGroup(currObject)
	if ( not currContainsGroup ) and ( not groupContainsCurr ):
	    self.groups[k] = group
	    
		

class Piece(ConfigurationObject):

    def __init__(self):
	ConfigurationObject.__init__(self)
	

    def __repr__(self):
        string = str(self.id) + " " + self.fields['acronym']
        return string

    def __str__(self):
        string = "\nPiece :"
        for field in self.fields:
            string = string + "\n" + field + " : " + self.fields[field]
        return string + "\n"
	
    def getType(self):
	return 'p'

class Halfling(ConfigurationObject):

    def __init__(self):
	ConfigurationObject.__init__(self)
	

    def __repr__(self):
        string = str(self.id) + " " + self.fields['classname']
        return string

    def __str__(self):
        string = "\nHalfling :"
        for field in self.fields:
            string = string + "\n" + field + " : " + self.fields[field]
        return string + "\n"
	
    def getType(self):
	return 'halfling'
	
    def getHalfling(self):
	return 'halflings halflings-'+self.fields['glyphname']

class Alarm(ConfigurationObject):

    def __init__(self):
	ConfigurationObject.__init__(self)
	

    def __repr__(self):
        string = str(self.id) + " " + self.fields['acronym']
        return string

    def __str__(self):
        string = "\nAlarm :"
        for field in self.fields:
            string = string + "\n" + field + " : " + self.fields[field]
        return string + "\n"
	
    def getType(self):
	return 'a'	
	
class Measure(ConfigurationObject):

    def __init__(self):
	ConfigurationObject.__init__(self)
        self.sensors = sets.Set()

    def __repr__(self):
        string = self.id + " " + self.fields['name']
        return string

    def __str__(self):
        string = "\nMeasure :"
        for field in self.fields:
            string = string + "\n" + field + " : " + self.fields[field]
        return string + "\n"
	    
    def getType(self):
	return 'm'

class Sensor(ConfigurationObject):
    def __init__(self):
	ConfigurationObject.__init__(self)
	self.actualAlarm = None
	self.countActual = 0
	self.degreeAlarm = 0
    
    def __repr__(self):
        string = self.id + " " + self.fields['channel'] + " " + self.fields['acronym']
        return string

    def __str__(self):
        string = "\nSensor :"
        for field in self.fields:
            string = string + "\n" + field + " : " + self.fields[field]
        return string + "\n"
	
    def getType(self):
	return 'cpehm'
	
    def getRRDName(self):
	name = ''
	if not self.fields['p_id'] == '':
	    name += 'P' + str(self.fields['p_id'])
	elif not self.fields['c_id'] == '':
	    name += 'C' + str(self.fields['c_id'])  
	elif not self.fields['e_id'] == '':
	    name += 'E' + str(self.fields['e_id'])
	if not self.fields['h_id'] == '':
	    name += 'H' + str(self.fields['h_id'])
	name += 'M' + str(self.fields['m_id'])
	name += '.rrd'
	return name

    def addComponent(self, data):
	tmp = data.split('_')
	typeComponent = tmp[-2][-1]
	if typeComponent == 'p' :
	    self.fields['p_id'] = tmp[-1]
	elif typeComponent == 'c' :
	    self.fields['c_id'] = tmp[-1]
	elif typeComponent == 'e' :
	    self.fields['e_id'] = tmp[-1]	    
	    
    def addMeasure(self, data):
	tmp = data.split('_')
	self.fields['m_id']= tmp[-1]
	    
	    
    def addPhase(self, data):
	self.fields['h_id'] = data
	
    def update(self, now, value):
	#updateRRD(now, value)
	typeAlarm = self.getTypeAlarm(value)
	if typeAlarm == 'typical' :
	    self.countActual = 0
	    self.actualAlarm = 'typical'
	    self.degreeAlarm = 0
	else:
	    if ( typeAlarm == 'min' and self.actualAlarm == 'minmin' ) or ( typeAlarm == 'max' and self.actualAlarm == 'maxmax') :
		self.launchAlarm()
	    else:
		self.actualAlarm = typeAlarm
		self.launchAlarm()	
	
    def updateRRD(self,now, value):
	rrdtool.update(rrdDir +self.getRRDName() , '%d:%f' % (now ,value))
	
    def createRRD(self):
	name = self.getName('EN').replace(" ","")
	now = str( int(time.time())-60)
	data_sources = str('DS:'+name+'1:GAUGE:120:U:U')
	rrdtool.create( str('rrd/'+self.getRRDName()), "--step", "60", '--start', now, data_sources, 'RRA:LAST:0.5:1:43200', 'RRA:AVERAGE:0.5:5:103680', 'RRA:AVERAGE:0.5:30:86400')
	
    def getTypeAlarm(self,value):
	tmp = float(value)
	print tmp
	if value <= float(self.fields['minmin']):
	    return 'minmin'
	elif value <= float(self.fields['min']):
	    return 'min'
	elif value <= float(self.fields['maxmax']) and value >= float(self.fields['max']):
	    return 'max'
	elif value > float(self.fields['maxmax']):
	    return 'maxmax'
	else:
	    return 'typical'
	    
    def launchAlarm(self):
	if self.degreeAlarm == 0 :
	    self.degreeAlarm = 1
	    self.countAlarm = 0
	    if int(float(self.fields['lapse1'])) < 60 :
		time = int(float(self.fields['lapse1']))
                test = UpdateAlarm(self, time)
		return test.run()
	    else:
		self.countAlarm = self.countAlarm+60
		nextUpdate = self.countAlarm + 60
		if self.degreeAlarm == 1 :
		    if nextUpdate > int(float(self.fields['lapse1'])):
			time = nextUpdate - int(float(self.fields['lapse1']))
			return UpdateAlarm(self, time)
		elif self.degreeAlarm == 2 :
		    if nextUpdate > int(float(self.fields['lapse2'])):
			time = nextUpdate - int(float(self.fields['lapse2']))
			return UpdateAlarm(self, time)
		if self.countAlarm > int(float(self.fields['lapse1'])) and self.degreeAlarm == 1:
		    self.countAlarm = self.countAlarm - int(float(self.fields['lapse1']))
		    degreeAlarm = 2
    
    def comeFromUpdateAlarm(self, value):
	tmp = self.getTypeAlarm(value)
	if not tmp == 'typical':
	    sys.stdout.write('ALARME : SENSEUR ' + self.getName('FR'))
            sys.stdout.flush()
	
	    
	    
class Batch(ConfigurationObject):

    def __init__(self, config):
        self.piece = ""
        self.equipment = ""
        self.phase = ""
        self.number = 0
        self.user = ""
        self.oldSeq = 0
        self.currStep = Step()
        self.currStep.fields = {}
        self.currStep.fields['seq'] = 0
        self.stepValues = {}
        self.config = config

    def endStep(self):
        print "Ligne finale"
        date = time.time()
        if (self.currStep.fields['seq'] != 0):
            for stepmeasure in self.currStep.stepmeasures:
                if(self.currStep.stepmeasures[stepmeasure] != None):
                    self.stepValues[self.currStep.stepmeasures[stepmeasure].fields['m_id']].end = date
        self.writeStepValues()
        self.stepValues = {}

    def beginStep(self):
        print "StepValues Initialization for seq."+str(self.currStep.fields['seq'])
        date = time.time()
        for stepmeasure in self.currStep.stepmeasures:
            print stepmeasure
            currStepVal = StepValue();
            currStepVal.measure = self.currStep.stepmeasures[stepmeasure]
            currStepVal.begin = date;
            self.stepValues[currStepVal.measure.fields['m_id']] = currStepVal
        print "\n"

    def writeStepValues(self):
        for stepvalue in self.stepValues:
            if (self.config.AllMeasures.elements[self.stepValues[stepvalue].measure.fields['m_id']].fields['source'] == "sensor" and self.stepValues[stepvalue].number != 0):
                print stepvalue + " start --- " + str(time.asctime(time.localtime(float(self.stepValues[stepvalue].begin))))
                print stepvalue + " finish --- " + str(time.asctime(time.localtime(float(self.stepValues[stepvalue].end))))
                print stepvalue + " min --- " + str(self.stepValues[stepvalue].min)
                print stepvalue + " max --- " + str(self.stepValues[stepvalue].max)
                self.stepValues[stepvalue].moy = float(self.stepValues[stepvalue].total/self.stepValues[stepvalue].number)
                print stepvalue + " moy --- " + str(self.stepValues[stepvalue].moy)
            elif(self.config.AllMeasures.elements[self.stepValues[stepvalue].measure.fields['m_id']].fields['source'] == "time"):
                print stepvalue + " start --- " + str(time.asctime(time.localtime(float(self.stepValues[stepvalue].begin))))
                print stepvalue + " finish --- " + str(time.asctime(time.localtime(float(self.stepValues[stepvalue].end))))
                self.stepValues[stepvalue].min = ""
                self.stepValues[stepvalue].max = ""
                self.stepValues[stepvalue].moy = round(self.stepValues[stepvalue].end - self.stepValues[stepvalue].begin, 0)
                print stepvalue + " duration --- " + str(self.stepValues[stepvalue].moy)
            elif(self.config.AllMeasures.elements[self.stepValues[stepvalue].measure.fields['m_id']].fields['source'] == "scan"):
                print stepvalue + " start --- " + str(time.asctime(time.localtime(float(self.stepValues[stepvalue].begin))))
                print stepvalue + " finish --- " + str(time.asctime(time.localtime(float(self.stepValues[stepvalue].end))))
                self.stepValues[stepvalue].min = ""
                self.stepValues[stepvalue].max = ""
                if self.stepValues[stepvalue].number:
                    self.stepValues[stepvalue].moy = float(self.stepValues[stepvalue].total/self.stepValues[stepvalue].number)
                else:
                    self.stepValues[stepvalue].moy = ""
                print stepvalue + " input --- " + str(self.stepValues[stepvalue].moy)
            else:
                print stepvalue + " start --- " + str(time.asctime(time.localtime(float(self.stepValues[stepvalue].begin))))
                print stepvalue + " finish --- " + str(time.asctime(time.localtime(float(self.stepValues[stepvalue].end))))
                self.stepValues[stepvalue].min = ""
                self.stepValues[stepvalue].max = ""
                self.stepValues[stepvalue].moy = ""
               
            if self.stepValues[stepvalue].moy:
                if self.piece != "":
                    piece = self.piece.id
                    pieceg = self.piece.fields['p_group']
                else:
                    piece = ""
                    pieceg = ""
                if self.equipment != "":
                    equipment = self.equipment.id
                    equipmentg = self.equipment.fields['e_group']
                else:
                    equipment = ""
                    equipmentg = ""
                if self.phase != "":
                    phase = self.phase.id
                    phaseg = self.phase.fields['h_group']
                else:
                    phase = ""
                    phaseg = ""
                    
                try:
                    with open("BCURPEHMAON.csv", "ab") as csvfile:
                        date = time.time()
                        fieldnames = ['start','end','b_group','b_id','c_group','c_id','u_group','u_id','r_group','r_id','p_group','p_id','e_group','e_id','h_group','h_id','m_group','m_id','a_group','a_id','o_group','o_id','n_group','n_id','order','value','unit','category','min','max','a_start','a_level','a_media']																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																													
                        writer = csv.DictWriter(csvfile, fieldnames, delimiter="\t")
                        row = {'e_group':equipmentg,'p_group':pieceg,'m_group':self.config.AllStepMeasures.elements[self.stepValues[stepvalue].measure.id].fields['m_group'],'h_group':phaseg,'u_id':self.user.fields['u_id'],'u_group':self.user.fields['u_group'],'end':time.asctime(time.localtime(float(date))),'start':str(time.asctime(time.localtime(float(self.stepValues[stepvalue].begin)))),'r_id':self.fields['r_id'],'value':self.stepValues[stepvalue].moy,'min':self.stepValues[stepvalue].min,'max':self.stepValues[stepvalue].max,'b_group':self.fields['b_group'],'b_id':self.fields['b_id'],'order':self.fields['order'],'e_id':equipment,'p_id':piece,'m_id':self.config.AllStepMeasures.elements[self.stepValues[stepvalue].measure.id].fields['m_id'],'h_id':phase}
                        writer.writerow(row)
                        print "BigLine added !"
                except IOError:
                    print "File already open"
            

    def __repr__(self):
        string = self.id + " " + self.fields['name']
        return string

    def __str__(self):
        string = "\nBatch :"
        for field in self.fields:
            string = string + "\n" + field + " : " + self.fields[field]
        return string + "\n"

class Barcode(ConfigurationObject):

    def __repr__(self):
        string = ""
        string = string + self.fields['acronym']
        return string

    def __str__(self):
        string = "\nCode barre :"
        for field in self.fields:
            string = string + "\n" + field + " : " + self.fields[field]
        return string + "\n"

class Phase(ConfigurationObject):

    def __repr__(self):
        string = self.id + " " + self.fields['name']
        return string

    def __str__(self):
        string = "\nPhase :"
        for field in self.fields:
            string = string + "\n" + field + " : " + self.fields[field]
        return string + "\n"

class StepValue():

    def __init__(self):
        self.min = 999999
        self.max = -999999
        self.total = 0
        self.number = 0
        self.begin = 0
        self.end = 0

class StepMeasure(ConfigurationObject):

    def __repr__(self):
        string = self.fields['seq'] + " " + self.fields['name']
        return string

class Step(ConfigurationObject):
    
    def __init__(self):
        self.stepmeasures = {}

    def __repr__(self):
        string = "\nStep :"
        for field in self.fields:
            string = string + "\n" + field + " : " + self.fields[field]
        return string + "\n"

class Recipe(ConfigurationObject):
    
    def __init__(self, config):
        self.config = config
        self.recipe = None
        self.AllSteps = AllSteps(self.config)

    def __repr__(self):
        string = self.id + " " + self.fields['name']
        return string

    def __str__(self):
        string = "\nRecette :"
        for field in self.fields:
            string = string + "\n" + field + " : " + self.fields[field]
        return string + "\n"

class Scanner(ConfigurationObject):
    mac = None
    key = None
    there = False
    paired = False
    last = None
    reader = None

    def __repr__(self):
        string = str(self.rank)+"#"+str(self.id) + "=" + self.fields['name']
        return string

    def __str__(self):
        string = "\nScanner "+str(self.rank)+"#"+str(self.id)
        for field in self.fields:
            string = string + "\n" + field + " : " + self.fields[field]
        return string + "\n"

class Context():

    def __init__(self):
        self.piece = ""
        self.equipment = ""
        self.phase = ""
        self.measure = ""
        self.batch = ""
        self.number = ""

    def __repr__(self):
        string = ""
        if self.piece != "":
            piece = self.piece.id
        else:
            piece = ""
        if self.equipment != "":
            equipment = self.equipment.id
        else:
            equipment = ""
        if self.phase != "":
            phase = self.phase.id
        else:
            phase = ""
        if self.measure != "":
            measure = self.measure.id
        else:
            measure = ""
        if self.batch != "":
            batch = self.batch.id
        else:
            batch = ""
        string = string + piece + " " + equipment + " " + phase + " " + measure + " " + batch + " "
        return string

    def __str__(self):
        string = "\nContext :\n"
        if self.piece != "":
            piece = str(self.piece)
        else:
            piece = ""
        if self.equipment != "":
            equipment = str(self.equipment)
        else:
            equipment = ""
        if self.phase != "":
            phase = str(self.phase)
        else:
            phase = ""
        if self.measure != "":
            measure = str(self.measure)
        else:
            measure = ""
        if self.batch != "":
            batch = str(self.batch)
        else:
            batch = ""
        string = string + piece + equipment + phase + measure + batch
        return string
