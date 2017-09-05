#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sets
import time
import datetime
import traceback
import unicodecsv
#import random
import sys
import threading
import os
import os.path
import rrdtool
import pyownet
import serial
import myuseful as useful
import HardConfig as hardconfig
import barcode
import re
import socket
import collections
"""
import SSD1306
from I2CScreen import *
import pigpio
PIG = pigpio.pi()
"""

#import smbus

#mise a jour git
csvDir = "../ELSAcsv/csv/"
rrdDir = '../ELSArrd/rrd/'
ttyDir = '/dev/ttyS0'
imgDir = 'static/img'
barcodesDir = 'static/img/barcodes/'
groupWebUsers = '_WEB'
datetimeformat = "%Y-%m-%d %H:%M:%S"

_lock_socket = None

queryChannels = ['wire','battery','cputemp','system']

class Configuration():

    def __init__(self):
	
        self.HardConfig = hardconfig.HardConfig()
	

##        # Run only OUNCE: Check if /run/akuino/ELSA.pid exists...
##        pid = str(os.getpid())
##        self.pidfile = self.HardConfig.RUNdirectory+"/ELSA.pid"
##
##        if os.path.isfile(self.pidfile):
##            print "%s already exists, exiting" % self.pidfile
##            sys.exit()
##        file(self.pidfile, 'w').write(pid)
	
        # Without holding a reference to our socket somewhere it gets garbage
        # collected when the function exits
        global _lock_socket
        
        _lock_socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)

        try:
            _lock_socket.bind('\0AKUINO-ELSA')
            print 'Socket AKUINO-ELSA now locked'
        except socket.error:
            print 'AKUINO-ELSA lock exists'
            sys.exit()
	
	self.csvCodes = csvDir + 'codes.csv'
	self.csvRelations = csvDir + 'relations.csv'
	self.fieldcode = ['begin', 'type', 'idobject', 'code', 'user']
        self.AllUsers = AllUsers(self)
	self.AllLanguages = AllLanguages(self)
        self.AllPieces = AllPieces(self)
        self.AllContainers = AllContainers(self)
	self.AllMessages = AllMessages(self)
	self.AllEquipments = AllEquipments(self)
	self.AllMeasures = AllMeasures(self)
	self.AllBatches = AllBatches(self)
	self.AllSensors = AllSensors(self)
	self.AllGrFunction = AllGrFunction(self)
	self.AllGrUsage = AllGrUsage(self)
	self.AllGrRecipe= AllGrRecipe(self)
	self.AllCheckPoints= AllCheckPoints(self)
	self.AllAlarms = AllAlarms(self)
	self.AllAlarmLogs= AllAlarmLogs(self)
	self.AllHalflings = AllHalflings(self)
	self.AllBarcodes = AllBarcodes(self)
	self.AllManualData = AllManualData(self)
	self.connectedUsers = AllConnectedUsers()
	self.AllTransfers = AllTransfers(self)
	self.AllPourings = AllPourings(self)
	self.AllTransferModels = AllTransferModels(self)
	self.AllManualDataModels = AllManualDataModels(self)
	self.AllPouringModels = AllPouringModels(self)
	self.isThreading = True
	self.UpdateThread = UpdateThread(self)
	self.RadioThread = RadioThread(self)
	self.RadioThread.daemon = True
	self.screen = None
	self.owproxy = None
	self.batteryVoltage = 0.0

    def load(self):
	"""
        if not self.HardConfig.oled is None:
            # 128x64 display with hardware I2C:
            self.screen = I2CScreen(True, disp = SSD1306.SSD1305_132_64(rst=self.HardConfig.oled_reset,gpio=PIG))
            self.screen.clear()
        else:
            self.screen = I2CScreen(False, disp = None)	
	"""
	self.AllLanguages.load()
        self.AllUsers.load()
        self.AllPieces.load()
	self.AllEquipments.load()
	self.AllContainers.load()	
	self.AllMessages.load()
	self.AllMeasures.load()
	self.AllSensors.load()
	self.AllSensors.check_rrd()
	self.AllSensors.correctValueAlarm()
	self.AllAlarms.load()
	self.AllHalflings.load()
	self.AllBatches.load()
	#doit toujours être appelé à la fin
	self.AllGrFunction.load()
	self.AllGrUsage.load()
	self.AllGrRecipe.load()
	self.AllCheckPoints.load()
	self.AllBarcodes.load()
	self.AllTransfers.load()
	self.AllManualData.load()
	self.AllPourings.load()
	self.AllTransferModels.load()
	self.AllManualDataModels.load()
	self.AllPouringModels.load()
	self.AllAlarmLogs.load()
	self.UpdateThread.start()
	self.RadioThread.start()
    
    def findAllFromName(self,className):
        if className == User.__name__:
            return self.AllUsers
        elif className == Equipment.__name__:
            return self.AllEquipments
        elif className == Language.__name__:
            return self.AllLanguages
	elif className == Piece.__name__:
	    return self.AllPieces 
	elif className == GrUsage.__name__:
	    return self.AllGrUsage
	elif className == GrRecipe.__name__:
	    return self.AllGrRecipe
	elif className == CheckPoint.__name__:
	    return self.AllCheckPoints
	elif className == GrFunction.__name__:
	    return self.AllGrFunction 
	elif className == Container.__name__:
	    return self.AllContainers 
	elif className == Measure.__name__:
	    return self.AllMeasures 
	elif className == Sensor.__name__:
	    return self.AllSensors 
	elif className == Alarm.__name__:
	    return self.AllAlarms 
	elif className == Batch.__name__:
	    return self.AllBatches 
	elif className == Transfer.__name__:
	    return self.AllTransfers 
	elif className == ManualData.__name__:
	    return self.AllManualData 
	elif className == Pouring.__name__:
	    return self.AllPourings 
	elif className == AlarmLog.__name__:
	    return self.AllAlarmLogs 
	elif className == TransferModel.__name__:
	    return self.AllTransferModels 
	elif className == ManualDataModel.__name__:
	    return self.AllManualDataModels 
	elif className == PouringModel.__name__:
	    return self.AllPouringModels 
	elif className == u"u":
            return self.AllUsers
        elif className == u"e":
            return self.AllEquipments
        elif className == u"l":
            return self.AllLanguages
	elif className == u"p":
	    return self.AllPieces
	elif className == u"gu":
	    return self.AllGrUsage
	elif className == u"gr":
	    return self.AllGrRecipe
	elif className == u"gf":
	    return self.AllGrFunction
	elif className == u"h":
	    return self.AllCheckPoints
	elif className == u"c":
	    return self.AllContainers
	elif className == u"m":
	    return self.AllMeasures
	elif className == u"s":
	    return self.AllSensors
	elif className == u"a":
	    return self.AllAlarms
	elif className == u"b":
	    return self.AllBatches
	elif className == u"t":
	    return self.AllTransfers
	elif className == u"tm":
	    return self.AllTransferModels
	elif className == u"dm":
	    return self.AllManualDataModels
	elif className == u"d":
	    return self.AllManualData
	elif className == u"v":
	    return self.AllPourings
	elif className == u"al":
	    return self.AllAlarmLogs
	elif className == u"v":
	    return self.AllPourings
	elif className == u"vm":
	    return self.AllPouringModels
        else:
            return None
	    
    def findAllFromObject(self,anObject):
        return self.findAllFromName(anObject.__class__.__name__)

    def getObject(self, idObject,className):
        allObjects = self.findAllFromName(className)
        if allObjects is not None:
            return allObjects.getItem(idObject)
        else:
            return None
    
    def getFieldsname(self,className):
        allObjects = self.findAllFromName(className)
        if allObjects is not None:
            return allObjects.fieldnames
        else:
            return None
	    
    def getKeyColumn(self, anObject):
	obj = self.findAllFromObject(anObject)
	return obj.keyColumn
	
    def findAllFromType(self, aType):
	return self.findAllFromName(aType)

    def get_group(self, key):
	if key == 'gu':
	    return self.AllGrUsage
	elif key == 'gr':
	    return self.AllGrRecipe
	elif key == 'gf':
	    return self.AllGrFunction
	elif key == 'h':
	    return self.AllCheckPoints
	
    def get_object(self, type, id):
	objects = self.findAllFromType(type)
	return objects.elements[id]
	
    def get_time(self):
	return useful.get_time(datetimeformat)
	
    def is_component(self, type):
	if type == 'c' or type == 'p' or type == 'e' or type == 'b':
	    return True
	return False

    def get_time_format(self):
        return datetimeformat
	
    def create_picture(self,code):
	EAN = barcode.get_barcode_class('ean13')
	try :
	    ean = EAN(code)
	    ean.save(barcodesDir+str(code))
	except:
	    return False
	return True

class ConfigurationObject():

    def __init__(self):
        self.fields = {}
	self.names = {}
	self.groups = {}
        self.id = None
	self.created = None
	self.creator = None
	self.position = []
	self.data = []
	
    def save(self,configuration,anUser=""):
        self.fields["begin"] = unicode(datetime.datetime.now().strftime(datetimeformat))
	if anUser != "" :
	    self.fields["user"] = anUser.fields['u_id']
        allObjects = configuration.findAllFromObject(self)
	print allObjects.fileobject
        print allObjects.fieldnames
        with open(allObjects.fileobject,"a") as csvfile:
            writer = unicodecsv.DictWriter(csvfile, delimiter = '\t', fieldnames=allObjects.fieldnames, encoding="utf-8")
            writer.writerow(self.fields)
	self.saveName(configuration, anUser)
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
	    tmpCode['begin'] = unicode(datetime.datetime.now().strftime(datetimeformat))
	    tmpCode['type'] = self.get_type()
	    tmpCode['idobject'] = self.fields[allObjects.keyColumn]
	    tmpCode['code'] = self.code
	    tmpCode["user"] = anUser.fields['u_id']
            writer = unicodecsv.DictWriter(csvfile, delimiter = '\t', fieldnames = configuration.fieldcode, encoding="utf-8")
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
            return directory + '/c/container_'+self.fields['c_id']+'.' 
	elif self.__class__.__name__ == u"Batch":
            return directory + '/b/batch_'+self.fields['b_id']+'.' 
        else:
            return None

    def isImaged(self):
        fileName = self.getImageDirectory()
        if fileName is None:
            return False
        else:
            return os.path.isfile(fileName+"jpg")

    def setName(self,key,value,user,keyColumn):
	if value != '' and value is not None:
	    newName={}
	    newName["begin"] = unicode(datetime.datetime.now().strftime(datetimeformat))
	    newName['user'] = user.fields['u_id']
	    newName['lang'] = key
	    newName['name'] = value
	    newName[keyColumn] = self.fields[keyColumn]
	    self.names[key] = newName
	    
    def getName(self,lang):
	if lang == 'disconnected':
	    lang = 'EN'
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
	    
    def get_real_name(self, lang):
	if lang in self.names:
	    return self.names[lang]['name']
	return ''
	    
    def getID(self):
	return self.id
	
    def write_group(self, groupid, configuration, user, active):
	allObjects = configuration.findAllFromObject(self)
	with open(configuration.csvRelations,"a") as csvfile:
	    tmpCode={}
	    tmpCode['begin'] = unicode(datetime.datetime.now().strftime(datetimeformat))
	    tmpCode['g_id'] = groupid
	    tmpCode['idobject'] = self.fields[allObjects.keyColumn]
	    tmpCode['type'] = self.get_type()
	    tmpCode["user"] = user.fields['u_id']
	    tmpCode['active'] = active
	    writer = unicodecsv.DictWriter(csvfile, delimiter = '\t', fieldnames = configuration.fieldrelations, encoding="utf-8")
	    writer.writerow(tmpCode)
	    
    def validate_form(self, data, configuration, lang) :
	tmp = ''
	if 'acronym' not in data :
	    tmp = configuration.AllMessages.elements['acronymrequired'].getName(lang) + '\n'
	try :
	    cond = data['acronym'] == re.sub('[^\w]+', '', data['acronym'])
	    if not cond :
		tmp += configuration.AllMessages.elements['acronymrules'].getName(lang) + '\n'
	except : 
	    tmp += configuration.AllMessages.elements['acronymrules'].getName(lang) + '\n'
	
	allObjects = configuration.findAllFromObject(self)    
	cond = allObjects.unique_acronym( data['acronym'], self.id)
	if not cond :
	    tmp += configuration.AllMessages.elements['acronymunique'].getName(lang) + '\n'
	try :
	    if 'code' in data and len(data['code']) >0 :
		code = int(data['code'])
		cond = configuration.AllBarcodes.validate_barcode(code, self.id, self.get_type())
		if cond == False :
		    tmp += configuration.AllMessages.elements['barcoderules'].getName(lang) + '\n'
	except:
	    tmp += configuration.AllMessages.elements['barcoderules'].getName(lang) + '\n'	    
	if tmp == '':
	    return True
	return tmp
	
    def set_value_from_data(self, data, c,user):
	self.fields['acronym'] = data['acronym']
	
	for key in c.AllLanguages.elements:
	    if key in data:
		self.setName(key, data[key],user, c.getKeyColumn(self))
		
	if 'active'in data:
	    self.set_active('1')
	else:
	    self.set_active('0')
	    
	if data['placeImg'] != {}: 
	    if data.placeImg.filename != '': 
		filepath = data.placeImg.filename.replace('\\','/') 
		ext = ((filepath.split('/')[-1]).split('.')[-1])
		fout = open(self.getImageDirectory()+'jpg','w')
		fout.write(data.placeImg.file.read())
		fout.close()
	if 'code' in data and len(data['code']) < 14 and len(data['code'])> 11:
	    self.code = int(data['code'])
	    c.AllBarcodes.create_barcode(self, self.code,user)
	    
		
	self.fields['remark'] = data['remark']
	
	if self.creator is None:
	    self.creator = user.fields['u_id']
	    self.created = self.fields['begin']
	    
    def add_data(self,manualdata):
	self.remove_data(manualdata)
	if len(self.data) == 0:
	    self.data.append(manualdata.getID())
	else:
	    time = useful.date_to_timestamp(manualdata.fields['time'],datetimeformat)
	    insert = False
	    for i in range(len(self.data)):
		tmp = self.config.AllManualData.elements[self.data[i]]
		tmptime = useful.date_to_timestamp(tmp.fields['time'],datetimeformat)
		if time < tmptime:
		    insert = True
		    self.data.insert(i,manualdata.getID())
		    break
	    if insert is False:
		self.data.append(manualdata.getID())
		
    def remove_data(self, manualdata):
	if manualdata.getID() in self.data:
	    self.data.remove(manualdata.getID())			
	
    def get_transfers_in_time_interval(self, begin, end):
	tmp = []
	first = True
	count = 0
	while count < len(self.position):
	    t = self.config.AllTransfers.elements[self.position[count]]
	    time = useful.date_to_timestamp(t.fields['time'],datetimeformat)
	    if begin < time and time < end :
		if first is True :
		    first = False
		    if count  > 0: 
			if useful.date_to_timestamp(self.config.AllTransfers.elements[self.position[count-1]].fields['time'],datetimeformat) > begin :
			    tmp.append(self.position[count -1])
	        tmp.append(t)
	    count += 1
	return tmp
	
    def delete(self, configuration):
	allObjects = configuration.findAllFromObject(self)
	allObjects.delete(self.id)
	
    def set_active(self, active):
	if 'active' in self.fields :
	    self.fields['active'] = active
	    
    def add_position(self, transfer):
	self.remove_position(transfer)
	if len(self.position) == 0:
	    self.position.append(transfer.getID())
	else:
	    time = useful.date_to_timestamp(transfer.fields['time'],datetimeformat)
	    insert = False
	    for i in range(len(self.position)):
		tmp = self.config.AllTransfers.elements[self.position[i]]
		tmptime = useful.date_to_timestamp(tmp.fields['time'],datetimeformat)
		if time < tmptime:
		    insert = True
		    self.position.insert(i,transfer.getID())
		    break
	    if insert is False:
		self.position.append(transfer.getID())
    
    def remove_position(self, transfer):
	if transfer.getID() in self.position:
	    self.position.remove(transfer.getID())
	
    def get_actual_position(self):
	if len(self.position) > 0:
	    return self.position[-1]
	return None
	
    def is_actual_position(self, type, id):
	tmp = self.get_actual_position()
	if tmp is not None :
	    tmp = self.config.AllTransfers.elements[tmp]
	    if type == tmp.fields['cont_type'] and str(id) == tmp.fields['cont_id']:
		return True
	return False
	
    def get_name_listing(self):
	return 'index'

    def get_acronym(self):
        return self.fields['acronym']
	
    def get_batch_in_component(self,config):
	batches = []
	for k,v in config.AllBatches.elements.items():
	    if v.is_actual_position(self.get_type(),self.getID()):
		batches.append(v)
	return batches

class UpdateThread(threading.Thread):

    def __init__(self,config):
        threading.Thread.__init__(self)
        self.config = config

    def run(self):
	time.sleep(60)
	self.config.owproxy = pyownet.protocol.proxy(host="localhost", port=4304)
	while self.config.isThreading is True:
	    now = useful.get_timestamp()
	    if not len(self.config.AllSensors.elements) == 0 :
		self.config.AllSensors.update(now)
	    time.sleep(60)
	    
class RadioThread(threading.Thread):

    def __init__(self,config):
        threading.Thread.__init__(self)
        self.config = config

    def run(self):
        noDots = { ord(' '): None, ord('.'): None }
        try:
	    elaSerial = serial.Serial(ttyDir, self.config.HardConfig.ela_bauds, timeout=0.1)
	    time.sleep(0.1)
	    elaSerial.write(self.config.HardConfig.ela_reset)
	    line = None
	    while self.config.isThreading is True:
		try:
		    data = elaSerial.read()
		    if data == '[' :
			line = []
		    elif line is not None:
			if data == ']' :
			    if len(line) == 10:
                                now = useful.get_timestamp()
				RSS = int(line[0]+line[1],16)
				HEX = line[2]+line[3]+line[4]
				#ADDRESS = int(HEX,16)
				VAL = int(line[5]+line[6]+line[7],16)
				#READER = int(line[8]+line[9],16)
				print "ELA="+HEX+", RSS="+unicode(RSS)+", val="+unicode(VAL)
				currSensor = None
				value = VAL
				for sensor in self.config.AllSensors.elements:
				    currSensor = self.config.AllSensors.elements[sensor]
				    try :
					if (unicode(currSensor.fields['sensor']).translate(noDots) == unicode(HEX).translate(noDots)):
					    if not  currSensor.fields['formula'] == '' :
						value = unicode(eval(currSensor.fields['formula']))
					    print (u"Sensor ELA-" + currSensor.fields['sensor']+ u": " + currSensor.fields['acronym'] +u" = "+unicode(value))
					    currSensor.update(now, value, self.config)
				    except :
                                	    traceback.print_exc()
					    print "Erreur dans la formule"					
			    line = None
			else:
			    line.append(data)
		except:
		    traceback.print_exc()
        except:
	    traceback.print_exc()

	if elaSerial:
      	    elaSerial.close()	

class AllObjects():

    def __init__(self):
	self.fileobject = None
        self.filename = None
        self.keyColumn = None
	self.count = 0
	
    def load(self):
	self.check_csv()
	self.loadFields()
	if self.filename is not None :
	    self.loadNames()

    def loadFields(self):
        with open(self.fileobject) as csvfile:
            reader = unicodecsv.DictReader(csvfile, delimiter = "\t")
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
		    if 'user' in row:
                        currObject.creator = row['user']
                    else:
                        currObject.creator = None
		self.elements[key] = currObject
		if currObject.get_type() == 't':
		    objects = self.config.findAllFromType(currObject.fields['object_type'])
		    if currObject.fields['active'] == '1' :
			objects.elements[currObject.fields['object_id']].add_position(currObject)
		    else:
			objects.elements[currObject.fields['object_id']].remove_position(currObject)
		elif currObject.get_type() == 'd':
		    objects = self.config.findAllFromType(currObject.fields['object_type'])
		    if currObject.fields['active'] == '1' :
			objects.elements[currObject.fields['object_id']].add_data(currObject)
		    else:
			objects.elements[currObject.fields['object_id']].remove_data(currObject)		    
		elif currObject.get_type() == 'dm':
		    objects = self.config.AllCheckPoints
		    if currObject.fields['active'] == '1' :
			objects.elements[currObject.fields['h_id']].add_dm(currObject)
		    else:
			objects.elements[currObject.fields['h_id']].remove_dm(currObject)		    
		elif currObject.get_type() == 'tm':
		    objects = self.config.AllCheckPoints
		    if currObject.fields['active'] == '1' :
			objects.elements[currObject.fields['h_id']].add_tm(currObject)
		    else:
			objects.elements[currObject.fields['h_id']].remove_tm(currObject)		    
		elif currObject.get_type() == 'vm':
		    objects = self.config.AllCheckPoints
		    if currObject.fields['active'] == '1' :
			objects.elements[currObject.fields['h_id']].add_vm(currObject)
		    else:
			objects.elements[currObject.fields['h_id']].remove_vm(currObject)		    
		elif currObject.get_type() == 'v':
		    objects = self.config.AllBatches
		    if currObject.fields['active'] == '1' :
			objects.elements[currObject.fields['src']].add_source(currObject)		    
			objects.elements[currObject.fields['dest']].add_destination(currObject)
		    else:
			objects.elements[currObject.fields['src']].remove_source(currObject)		    
			objects.elements[currObject.fields['dest']].remove_destination(currObject)
    def loadNames(self):
	with open(self.filename) as csvfile:
	    reader = unicodecsv.DictReader(csvfile, delimiter = "\t")
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
	currObject.fields[self.keyColumn] = unicode(tmp)
	currObject.id = str(tmp)
	self.elements[unicode(tmp)] = currObject
	currObject.fields["begin"] = unicode(datetime.datetime.now().strftime(datetimeformat))
	return currObject
	
    def unique_acronym(self, acronym, myID):
	for k, element in self.elements.items():
	    if element.fields['acronym'] == acronym and unicode(myID) != unicode(element.fields[self.keyColumn]) :
		return False
	return True
	
    def getItem(self,iditem):
	if iditem == u'new':
	    return self.createObject()
	elif iditem in self.elements.keys():
	    return self.elements[str(iditem)]
	return None
	
    def delete(self, anID):
	del self.elements[unicode(anID)]
	
    def check_csv(self):
	filename = self.fileobject
	if not os.path.exists(filename):
	    self.create_csv(filename)
    
    def create_csv(self, fname):
	with open(fname,'w') as csvfile:
	    csvfile.write(self.fieldnames[0])
	    tmp = 1
	    while tmp < len(self.fieldnames):
		csvfile.write('\t'+self.fieldnames[tmp])
		tmp = tmp + 1
            csvfile.write('\n')
	if self.filename is not None :
	    with open(self.filename,'w') as csvfile:
		csvfile.write(self.fieldtranslate[0])
		tmp = 1
		while tmp < len(self.fieldtranslate):
		    csvfile.write('\t'+self.fieldtranslate[tmp])
		    tmp = tmp + 1
		csvfile.write('\n')
		    
    def get_name_object(self ):
	return 'component'
	
    def get_sorted(self):
	return collections.OrderedDict(sorted(self.elements.items(),key = lambda t:t[1].fields['acronym'])).keys()
	
class AllUsers(AllObjects):

    def __init__(self, config):
	AllObjects.__init__(self)
        self.elements = {}
        self.config = config
        self.fileobject = csvDir + "U.csv"
	self.filename = csvDir + "Unames.csv"
        self.keyColumn = "u_id"
	self.fieldnames = ['begin', 'u_id', 'active', 'acronym', 'remark', 'registration', 'phone','mail', 'password', 'language','gf_id', 'user']
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
		
    def get_name_object(self ):
	return 'user'
	
    def get_key_group(self):
	return 'gf'
    
class AllEquipments(AllObjects):

    def __init__(self, config):
	AllObjects.__init__(self)
        self.elements = {}
        self.config = config
        self.fileobject = csvDir + "E.csv"
	self.filename = csvDir + "Enames.csv"
        self.keyColumn = "e_id"
	self.fieldnames = ["begin", "e_id", "active", "acronym", "remark",'colorgraph','gu_id', "user"]
	self.fieldtranslate = ['begin', 'lang', 'e_id', 'name', 'user']

    def newObject(self):
        return Equipment(self.config)
	
    def get_name_object(self ):
	return 'equipment'
	
    def get_key_group(self):
	return 'gu'

class AllContainers(AllObjects):

    def __init__(self, config):
	AllObjects.__init__(self)
        self.elements = {}
        self.config = config
        self.fileobject = csvDir + "C.csv"
	self.filename = csvDir + "Cnames.csv"
        self.keyColumn = "c_id"
	self.fieldnames = ["begin", "c_id", "active", "acronym", "remark",'colorgraph','gu_id', "user"]
	self.fieldtranslate = ['begin', 'lang', 'c_id', 'name', 'user']

    def newObject(self):
        return Container(self.config)
	
    def get_name_object(self ):
	return 'container'
	
    def get_key_group(self):
	return 'gu'

class AllPieces(AllObjects):

    def __init__(self, config):
	AllObjects.__init__(self)
        self.elements = {}
        self.config = config
        self.fileobject = csvDir + "P.csv"
	self.filename = csvDir + "Pnames.csv"
        self.keyColumn = "p_id"
	self.fieldnames = ['begin', 'p_id', 'active', 'acronym', 'remark','colorgraph','gu_id', 'user']
	self.fieldtranslate = ['begin', 'lang', 'p_id', 'name', 'user']
	self.count = 0

    def newObject(self):
	return Piece(self.config)
	
    def get_name_object(self):
	return 'place'
	
    def get_key_group(self):
	return 'gu'
	
class AllAlarmLogs(AllObjects):

    def __init__(self, config):
	AllObjects.__init__(self)
        self.elements = {}
        self.config = config
        self.fileobject = csvDir + "alarmlogs.csv"
	self.filename = None
        self.keyColumn = "al_id"
	self.fieldnames = ['begin', 'al_id', 'cont_id', 'cont_type', 's_id','value','typealarm','begintime', 'alarmtime', 'degree']
	self.fieldtranslate = None
	self.count = 0

    def newObject(self):
	return AlarmLog()
	
    def get_alarmlog_component(self, id,begin,end):
	logs = []
	for i in range(len(self.elements)):
	    e = self.elements[str(i+1)]
	    time = useful.date_to_timestamp(e.fields['begin'],datetimeformat)
	    if id == e.fields['s_id'] :
		if time > begin and time < end :
		    logs.append(e)
	return logs
	
class AllHalflings(AllObjects):

    def __init__(self, config):
	AllObjects.__init__(self)
        self.elements = {}
        self.config = config
        self.fileobject = csvDir + "halflings.csv"
	self.filename = None
        self.keyColumn = "classname"
	self.fieldnames = ['begin', 'classname', 'glyphname', 'user']
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
	self.fieldnames = ['begin', 'a_id', 'active', 'acronym', 'o_sms1', 'o_sms2', 'o_email1', 'o_email2', 'o_sound1', 'o_sound2', 'relay1', 'relay2', 'remark', 'user']
	self.fieldtranslate = ['begin', 'lang', 'a_id', 'name', 'user']

    def newObject(self):
	return Alarm()	
	
    def get_name_object(self ):
	return 'alarm'
	
class AllManualData(AllObjects):

    def __init__(self, config):
	AllObjects.__init__(self)
        self.elements = {}
        self.config = config
        self.fileobject = csvDir + "D.csv"
	self.filename = None
        self.keyColumn = "d_id"
	self.fieldnames = ['begin', 'd_id', 'object_id', 'object_type', 'time', 'remark', 'm_id', 'value', 'active', 'user']
	self.fieldtranslate = None

    def newObject(self):
	return ManualData()
	
    def get_name_object(self ):
	return 'manualdata'
    
class AllPourings(AllObjects):

    def __init__(self, config):
	AllObjects.__init__(self)
        self.elements = {}
        self.config = config
        self.fileobject = csvDir + "V.csv"
	self.filename = None
        self.keyColumn = "v_id"
	self.fieldnames = ['begin', 'v_id', 'src', 'dest', 'time', 'quantity', 'm_id', 'remark','active', 'user']
	self.fieldtranslate = None

    def newObject(self):
	return Pouring()
	
    def get_name_object(self ):
	return 'v'
    
class AllGroups(AllObjects):
    def __init__(self, config):
	AllObjects.__init__(self)
        self.elements = {}
        self.config = config
	self.fieldrelations = ['begin', 'parent_id', 'child_id', 'active', 'user']
	
    def load(self):
	AllObjects.load(self)
	self.check_relation()
	self.load_relation()
	
    def check_relation(self):
	filename = self.csvRelations
	if not os.path.exists(filename):
	    self.create_relation(filename)
	    
    def create_relation(self, fname):
	with open(fname,'w') as csvfile:
	    csvfile.write(self.fieldrelations[0])
	    tmp = 1
	    while tmp < len(self.fieldrelations):
		csvfile.write('\t'+self.fieldrelations[tmp])
		tmp = tmp + 1
            csvfile.write('\n')
	
    def get_master_groups(self):
	children = {}
	for k,group in self.elements.items():
	    if group.fields['g_parent'] == '':
		children[k] = group
	return children
	
    def load_relation(self):
	with open(self.csvRelations) as csvfile:
	    reader = unicodecsv.DictReader(csvfile, delimiter = "\t")
	    for row in reader:
		parent = row['parent_id']
		child = row['child_id']
		currObject = self.elements[child]
		if row['active'] =='0':		    
		    currObject.add_relation(self.elements[parent])
		elif row['active'] == '1' :
		    currObject.remove_relation(self.elements[parent])
	self.load_family()
	
    def load_family(self):
	for k,g in self.elements.items():
	    g.parents = []
	    g.children = []
	    g.siblings = []
	    g.load_parents()
	    g.load_children()
	    g.load_siblings()
    
    def get_hierarchy_str(self, g = None, myString = None):
	if myString is None:
	    myString = []
	for k,group in self.elements.items():
	    cond1 = ( g == None and len(group.related) == 0 )
	    cond2 = ( g is not None and g.getID() in group.related )
	    if cond1 or cond2:
		myString.append(k)
		myString.append('IN')
		self.get_hierarchy_str(group,myString)
		myString.append('OUT')
	return myString
	
    def get_group(self, acro):
	for k,g in self.elements.items():
	    if g.fields['acronym'] == groupWebUsers:
		return k	    
	
class AllGrUsage(AllGroups):
    def __init__(self, config):
	AllGroups.__init__(self, config)
        self.fileobject = csvDir + "GU.csv"
	self.filename = csvDir + "GUnames.csv"
        self.keyColumn = "gu_id"
	self.fieldnames = ["begin", "gu_id", "active", "acronym", "remark", "user"]
	self.fieldtranslate = ['begin', 'lang', 'gu_id', 'name', 'user']
	self.csvRelations = csvDir + "GUrelations.csv"

    def newObject(self):
        return GrUsage(self.config)
	
    def get_name_object(self):
	return 'guse'
	
    def get_key_group(self):
	return 'gu'
	
class AllGrRecipe(AllGroups):
    def __init__(self, config):
	AllGroups.__init__(self, config)
        self.fileobject = csvDir + "GR.csv"
	self.filename = csvDir + "GRnames.csv"
        self.keyColumn = "gr_id"
	self.fieldnames = ["begin", "gr_id", "active", "acronym", "remark", "user"]
	self.fieldtranslate = ['begin', 'lang', 'gr_id', 'name', 'user']
	self.csvRelations = csvDir + "GRrelations.csv"

    def newObject(self):
        return GrRecipe(self.config)
	
    def get_name_object(self):
	return 'grecipe'
	
    def get_key_group(self):
	return 'gr'
	
class AllCheckPoints(AllGroups):
    def __init__(self, config):
	AllGroups.__init__(self, config)
        self.fileobject = csvDir + "H.csv"
	self.filename = csvDir + "Hnames.csv"
        self.keyColumn = "h_id"
	self.fieldnames = ["begin", "h_id", "active", "acronym", "remark",'gr_id', "user"]
	self.fieldtranslate = ['begin', 'lang', 'h_id', 'name', 'user']
	self.fieldcontrols = ['begin', 'h_id', 'object_type','object_id', 'user']
	self.csvRelations = csvDir + "Hrelations.csv"
	self.csvControls = csvDir + "Hcontrols.csv"

    def newObject(self):
        return CheckPoint(self.config)
	
    def get_name_object(self):
	return 'checkpoint'
	
    def get_key_group(self):
	return 'h'
	
    def load(self):
	AllGroups.load(self)
	self.check_controls()
	self.load_controls()
    
    def check_controls(self):
	filename = self.csvControls
	if not os.path.exists(filename):
	    self.create_control(filename)
	    
    def create_control(self, fname):
	with open(fname,'w') as csvfile:
	    csvfile.write(self.fieldcontrols[0])
	    tmp = 1
	    while tmp < len(self.fieldcontrols):
		csvfile.write('\t'+self.fieldcontrols[tmp])
		tmp = tmp + 1
            csvfile.write('\n')
    
    def load_controls(self):
	with open(self.csvControls) as csvfile:
	    reader = unicodecsv.DictReader(csvfile, delimiter = "\t")
	    for row in reader:
		type = row['object_type']
		id = row['object_id']
		currObject = self.config.findAllFromType(type).elements[id].add_checkpoint(row['h_id'])
	
class AllGrFunction(AllGroups):
    def __init__(self, config):
	AllGroups.__init__(self, config)
        self.fileobject = csvDir + "GF.csv"
	self.filename = csvDir + "GFnames.csv"
        self.keyColumn = "gf_id"
	self.fieldnames = ["begin", "gf_id", "active", "acronym", "remark", "user"]
	self.fieldtranslate = ['begin', 'lang', 'gf_id', 'name', 'user']
	self.csvRelations = csvDir + "GFrelations.csv"

    def newObject(self):
        return GrFunction(self.config)
	
    def get_name_object(self):
	return 'gfunction'
	
    def get_key_group(self):
	return 'gf'

class AllMeasures(AllObjects):

    def __init__(self, config):
	AllObjects.__init__(self)
        self.elements = {}
        self.config = config
        self.fileobject = csvDir + "M.csv"
	self.filename = csvDir + "Mnames.csv"
        self.keyColumn = "m_id"
	self.fieldnames = ['begin', 'm_id', 'active', 'acronym', 'unit', 'remark', 'user']
	self.fieldtranslate = ['begin', 'lang', 'm_id', 'name', 'user']
	self.count = 0

    def newObject(self):
        return Measure()
	
    def get_name_object(self ):
	return 'measure'

class AllSensors(AllObjects):

    def __init__(self, config):
        AllObjects.__init__(self)
        self.elements = {}
        self.config = config
        self.fileobject = csvDir + "S.csv"
	self.filename = csvDir + "Snames.csv"
        self.keyColumn = "s_id"
	self.fieldnames = ['begin', 's_id', 'c_id', 'p_id', 'e_id', 'm_id', 'active', 'acronym', 'remark', 'channel', 'sensor', 'subsensor', 'valuetype', 'formula', 'minmin', 'min', 'typical', 'max', 'maxmax', 'a_minmin', 'a_min', 'a_typical', 'a_max', 'a_maxmax', 'lapse1', 'lapse2', 'lapse3', 'user']
	self.fieldtranslate = ['begin', 'lang', 's_id', 'name', 'user']
	self.count = 0

    def newObject(self):
        return Sensor()
	
    def get_name_object(self ):
	return 'sensor'
	
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

    def correctValueAlarm(self):
        for k,sensor in self.elements.items():
            sensor.setCorrectAlarmValue()
	    
    def update(self, now) :
	for k,sensor in self.elements.items():
	    if sensor.fields['channel'] in queryChannels and not sensor.fields['active'] == '0' :
		value = sensor.get_value_sensor(self.config)
		sensor.update(now, value,self.config)
		
    def check_rrd(self):
	for k, v in self.elements.items():
	    filename = rrdDir + v.getRRDName()
	    if not os.path.exists(filename):
		v.createRRD()

class AllBatches(AllObjects):

    def __init__(self, config):
	AllObjects.__init__(self)
        self.elements = {}
        self.config = config
        self.fileobject = csvDir + "B.csv"
	self.filename = csvDir + "Bnames.csv"
        self.keyColumn = "b_id"
	self.fieldnames = ["begin", "b_id", "active", "acronym", "basicqt", "m_id", "time", "cost", "remark", 'gr_id',"user"]
	self.fieldtranslate = ['begin', 'lang', 'b_id', 'name', 'user']

    def newObject(self):
        return Batch(self.config)
	
    def get_name_object(self ):
	return 'batch'
	
    def get_key_group(self):
	return 'gr'
	
class AllTransfers(AllObjects):

    def __init__(self, config):
	AllObjects.__init__(self)
        self.elements = {}
        self.config = config
        self.fileobject = csvDir + "T.csv"
	self.filename = None
        self.keyColumn = "t_id"
	self.fieldnames = ["begin","t_id",'time', "cont_id", "cont_type", "object_id", "object_type", "remark", 'active', "user"]
	self.fieldtranslate = None

    def newObject(self):
        return Transfer(self.config)
	
    def get_name_object(self ):
	return 'transfer'
	
class AllTransferModels(AllObjects):

    def __init__(self, config):
	AllObjects.__init__(self)
        self.elements = {}
        self.config = config
        self.fileobject = csvDir + "TM.csv"
	self.filename = csvDir + "TMnames.csv"
        self.keyColumn = "tm_id"
	self.fieldnames = ["begin","tm_id",'acronym','gu_id','h_id','rank', "remark", 'active', "user"]
	self.fieldtranslate = ['begin', 'lang', 'tm_id', 'name', 'user']

    def newObject(self):
        return TransferModel(self.config)
	
    def get_name_object(self ):
	return 'transfermodel'
    
    def get_key_group(self):
	return 'h'
	
class AllPouringModels(AllObjects):

    def __init__(self, config):
	AllObjects.__init__(self)
        self.elements = {}
        self.config = config
        self.fileobject = csvDir + "VM.csv"
	self.filename = csvDir + "VMnames.csv"
        self.keyColumn = "vm_id"
	self.fieldnames = ["begin","vm_id",'acronym','src','dest','quantity','h_id', 'rank', "in", "remark", 'active', "user"]
	self.fieldtranslate = ['begin', 'lang', 'vm_id', 'name', 'user']

    def newObject(self):
        return PouringModel(self.config)
	
    def get_name_object(self ):
	return 'pouringmodel'
    
    def get_key_group(self):
	return 'h'
	

	
class AllManualDataModels(AllObjects):

    def __init__(self, config):
	AllObjects.__init__(self)
        self.elements = {}
        self.config = config
        self.fileobject = csvDir + "DM.csv"
	self.filename = csvDir + "DMnames.csv"
        self.keyColumn = "dm_id"
	self.fieldnames = ["begin","dm_id",'acronym','m_id','h_id', 'rank', "remark", 'active', "user"]
	self.fieldtranslate = ['begin', 'lang', 'dm_id', 'name', 'user']

    def newObject(self):
        return ManualDataModel(self.config)
	
    def get_name_object(self ):
	return 'manualdatamodel'
	
    def get_key_group(self):
	return 'h'
	

class AllBarcodes(AllObjects):

    def __init__(self, config):
        AllObjects.__init__(self)
        self.elements = {}
        self.config = config
        self.fileobject = csvDir + "codes.csv"
	self.filename = None
        self.keyColumn = "code"
	self.fieldnames = ['begin', 'type', 'idobject', 'code', 'active', 'user']
	self.fieldtranslate = None
	self.count = 0
	self.EAN = barcode.get_barcode_class('ean13')
	
    def load(self):
	with open(self.fileobject) as csvfile:
            reader = unicodecsv.DictReader(csvfile, delimiter = "\t")
            for row in reader:
		key = row[self.keyColumn]
		if row['active'] == '0' :
		    del self.elements[key]
		elif len(row['code']) > 0:
		    currObject = self.newObject( self.config.getObject(row['idobject'], row['type']))
		    currObject.fields = row
		    currObject.id = key
		    self.elements[key] = currObject
	self.to_pictures()

    def newObject(self, item):
        return Barcode(item)
	
    def get_barcode(self, myType, myID):
	for k  in self.elements.keys():
            if self.elements[k].element:
                if self.elements[k].element.get_type() == myType and unicode(self.elements[k].element.getID()) == myID:
		    self.elements[k].barcode_picture()
                    return k
	return ''
	
    def unique_barcode(self,code, myID, myType):
	for k,v in self.elements.items():
	    if int(code) == int(k) and not myID == v.getID() and not myType == v.fields['type']:
		return False
	return True
    
    def add_barcode(self, item, code, user):
	if self.unique_barcode(code, item.getID(), item.get_type()) :
	    oldBarcode = self.get_barcode( item.get_type(), item.getID())
	    if not oldBarcode == code and not oldBarcode == '' :
		self.delete_barcode(oldBarcode, user)
	    self.elements[code] = self.create_barcode(item, code, user)
	
    def delete_barcode(self, oldBarcode, user):
	self.write_csv( oldBarcode, 0, user)
	del self.elements[oldBarcode]
	
    def write_csv(self, code, active, user):
	with open(self.fileobject,"a") as csvfile:
	    tmpCode=self.create_fields(code, active, user)
            writer = unicodecsv.DictWriter(csvfile, delimiter = '\t', fieldnames = self.fieldnames, encoding="utf-8")
            writer.writerow(tmpCode)
	    
    def create_barcode(self, item, code, user):
	tmp = self.newObject(item)
	fields = self.create_fields( code, 1, user, item)
	tmp.fields = fields
	self.elements[code] = tmp
	tmp.element = item
	self.write_csv(code, 1, user)
	return tmp
	
    def create_fields(self, code,active, user, item = None):
	fields = {}
	fields['begin'] = unicode(datetime.datetime.now().strftime(datetimeformat))
	if item is None :
	    fields['type'] = self.elements[code].element.get_type()
	    fields['idobject'] = self.elements[code].element.id
	else :
	    fields['type'] = item.get_type()
	    fields['idobject'] = item.id
	fields['code'] = code
	fields['active'] = active
	fields["user"] = user.fields['u_id']
	return fields
	
    def validate_barcode(self, code, anID, aType):
	if len(unicode(code)) < 12 or len(unicode(code)) >13 :
	    return False
	try:
	    EAN = barcode.get_barcode_class('ean13')
	    ean = EAN(unicode(code))
	except :
	    traceback.print_exc() 
	    return False
	if self.unique_barcode(code, anID, aType) is not True :
	    return False
	return True
	    
    def to_pictures(self):
	for k, v in self.elements.items():
	    v.barcode_picture()
	    
    def barcode_to_item(self, code):
	for k,barcode in self.elements.items():
	    if barcode.fields['code'] == code :
		return self.config.findAllFromType(barcode.fields['type']).elements[barcode.fields['idobject']]

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
    
    def disconnect(self, mail):
	if mail in self.users:
	    del self.users[mail]
			
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
        string = unicode(self.id) + " " + self.fields['name']
        return string

    def __str__(self):
        string = "\nLanguage :"
        for field in self.fields:
            string = string + "\n" + field + " : " + self.fields[field]
        return string + "\n"
	
    def get_type(self):
	return 'language'

class Message(ConfigurationObject):
    
    def __repr__(self):
        string = unicode(self.id) + " " + self.fields['default']
        return string

    def __str__(self):
        string = "\nMessage :"
        for field in self.fields:
            string = string + "\n" + field + " : " + self.fields[field]
        return string + "\n"	
	
    def get_type(self):
	return 'message'
	

class User(ConfigurationObject):

    def __init__(self):
	ConfigurationObject.__init__(self)
	self.exportdata = None

    def __repr__(self):
        string = unicode(self.id) + " " + self.fields['acronym']
        return string

    def __str__(self):
        string = "\nUtilisateur :"
        for field in self.fields:
            string = string + "\n" + field + " : " + unicode(self.fields[field])
        return string + "\n"
	
    def checkPassword(self,password):
	return self.fields['password']==password
	
    def get_type(self):
	return 'u'

    def get_name_listing(self):
	return 'users'
	
    def get_name(self):
	return 'user'
    
    def validate_form(self, data, configuration, lang) :
	tmp = ConfigurationObject.validate_form(self, data, configuration, lang)
	if tmp is True:
	    tmp = ''
	if tmp is True:
	    tmp = ''
	if data['password'] == '' or len(data['password'])<8:
	    tmp += configuration.AllMessages.elements['passwordrules'].getName(lang) + '\n'	    
	
	if tmp == '':
	    return True
	return tmp
	
    def set_value_from_data(self, data, c,user):
	ConfigurationObject.set_value_from_data(self, data, c,user)
	tmp = ['phone', 'mail','language']
	for elem in tmp:
	    self.fields[elem] = data[elem]
	self.fields['registration'] = self.created
	self.fields['password'] = useful.encrypt(data['password'],self.fields['registration'])
	self.fields['gf_id'] = data['group']
	self.save(c,user)
	
    def get_group(self):
	return self.fields['gf_id']

class Equipment(ConfigurationObject):

    def __init__(self,config):
	ConfigurationObject.__init__(self)
	self.config = config

    def __repr__(self):
        string = unicode(self.id) + " " + self.fields['acronym']
        return string

    def __str__(self):
        string = "\nEquipement :"
        for field in self.fields:
            string = string + "\n" + field + " : " + self.fields[field]
        return string + "\n"
	
    def get_type(self):
	return 'e'
	
    def getID(self):
	return self.fields['e_id']
	
    def get_name_listing(self):
	return 'equipments'
	
    def get_name(self):
	return 'equipment'
	
    def get_sensors_in_component(self, config):
	listSensor = []
	for k, sensor in config.AllSensors.elements.items():
	    if sensor.is_in_component('e',self.id):
		listSensor.append(k)
	return listSensor
	
    def validate_form(self, data, configuration, lang):
	return ConfigurationObject.validate_form(self, data, configuration, lang)	
	
    def set_value_from_data(self, data, c,user):
	ConfigurationObject.set_value_from_data(self, data, c,user)
	self.fields['colorgraph'] = data['colorgraph']
	self.fields['gu_id'] = data['group']
	self.save(c,user)
	
    def get_group(self):
	return self.fields['gu_id']

class Container(ConfigurationObject):

    def __init__(self, config):
	ConfigurationObject.__init__(self)
	self.config = config

    def __repr__(self):
        string = unicode(self.id) + " " + self.fields['acronym']
        return string

    def __str__(self):
        string = "\nContainer :"
        for field in self.fields:
            string = string + "\n" + field + " : " + self.fields[field]
        return string + "\n"
	
    def get_type(self):
	return 'c'
	
    def get_name_listing(self):
	return 'containers'
	
    def get_name(self):
	return 'container'
	
    def get_sensors_in_component(self, config):
	listSensor = []
	for k, sensor in config.AllSensors.elements.items():
	    if sensor.is_in_component('c',self.id):
		listSensor.append(k)
	return listSensor
	
    def validate_form(self, data, configuration, lang):
	return ConfigurationObject.validate_form(self, data, configuration, lang)	
	
    def set_value_from_data(self, data, c,user):
	ConfigurationObject.set_value_from_data(self, data, c,user)
	self.fields['colorgraph'] = data['colorgraph']
	self.fields['gu_id'] = data['group']
	self.save(c,user)
	
    def get_group(self):
	return self.fields['gu_id']
	
class ManualData(ConfigurationObject):

    def __init__(self):
	ConfigurationObject.__init__(self)
	self.id = str(self.id)

    def __repr__(self):
        string = unicode(self.id)
        return string

    def __str__(self):
        string = "\nManual Data :"
        for field in self.fields:
            string = string + "\n" + field + " : " + self.fields[field]
        return string + "\n"
	
    def get_type(self):
	return 'd'
	
    def get_name_listing(self):
	return 'manualdata'
	
    def add_component(self, component):
	type = component.split('_')[0]
	id = component.split('_')[1]
	self.fields['object_id'] = id
	self.fields['object_type'] = type
	
    def add_measure(self, measure):
	if not measure =='None':
	    self.fields['m_id'] = str(measure)
	else:
	    self.fields['m_id'] = ''
	
    def validate_form(self, data, configuration, lang) :
	tmp = ''
	try:
	    value = datetime.datetime.strptime(data['time'],datetimeformat)
	except:
	    traceback.print_exc()
	    tmp += configuration.AllMessages.elements['timerules'].getName(lang) + '\n'
	
	if 'value' in data and data['measure'] == u'None':
	    if not data['value'] == '' :
		tmp += configuration.AllMessages.elements['datarules'].getName(lang) + '\n'
	elif 'value' in data:
	    try : 
		value = float(data['value'])
	    except:
		tmp += configuration.AllMessages.elements['floatrules'].getName(lang) + ' '+data['value']+'\n'
	try:
	    aType = data['component'].split('_')[0]
	    anId = data['component'].split('_')[1]
	    if not configuration.is_component(aType):
		tmp += configuration.AllMessages.elements['componentrules'].getName(lang) + ' '+data['component']+'\n'
	except:
	    tmp += configuration.AllMessages.elements['componentrules'].getName(lang) + '\n'
		    
	if tmp == '':
	    return True
	return tmp
	
    def set_value_from_data(self, data, c,user):
	if self.fields['object_type'] != '' and self.fields['object_id'] != '' :
	    c.findAllFromType(self.fields['object_type']).elements[self.fields['object_id']].remove_data(self)
	tmp = ['time', 'value', 'remark']
	for elem in tmp:
	    self.fields[elem] = data[elem]
	self.add_component(data['component'])
	self.add_measure(data['measure'])
	if 'active' in data :
	    self.fields['active'] = '1'
	else :
	    self.fields['active'] = '0'
	if self.fields['active'] == '1' :
	    c.findAllFromType(self.fields['object_type']).elements[self.fields['object_id']].add_data(self)
	else:
	    c.findAllFromType(self.fields['object_type']).elements[self.fields['object_id']].remove_data(self)
	self.save(c,user)
	
	
    def get_name(self):
	return 'manualdata'
	
class Pouring(ConfigurationObject):
    def __init__(self):
	ConfigurationObject.__init__(self)
	self.id = str(self.id)

    def __repr__(self):
        string = unicode(self.id)
        return string

    def __str__(self):
        string = "\nPouring :"
        for field in self.fields:
            string = string + "\n" + field + " : " + self.fields[field]
        return string + "\n"
	
    def get_type(self):
	return 'v'
	
    def get_name_listing(self):
	return 'pouring'
	
    def add_measure(self, measure):
	tmp = measure.split('_')
	self.fields['m_id']= tmp[-1]
	
	
    def validate_form(self, data, configuration, lang) :
	tmp = ''
	try:
	    value = datetime.datetime.strptime(data['time'],datetimeformat)
	except:
	    tmp += configuration.AllMessages.elements['timerules'].getName(lang) + '\n'
	try : 
	    value = float(data['quantity'])
	except:
	    tmp += configuration.AllMessages.elements['floatrules'].getName(lang) + '\n'
	try:
	    b_id = data['src']
	    if not b_id in configuration.AllBatches.elements.keys():
		tmp += configuration.AllMessages.elements['batchrules1'].getName(lang) + '\n'
	except:
	    tmp += configuration.AllMessages.elements['batchrules1'].getName(lang) + '\n'
	try:
	    b_id = data['dest']
	    if not b_id in configuration.AllBatches.elements.keys():
		tmp += configuration.AllMessages.elements['batchrules2'].getName(lang) + '\n'
	except:
	    tmp += configuration.AllMessages.elements['batchrules2'].getName(lang) + '\n'
	if data['src'] == data['dest']:
	    tmp += configuration.AllMessages.elements['batchrules3'].getName(lang) + '\n'
	
	if tmp == '':
	    return True
	return tmp
	
    def set_value_from_data(self, data, c,user):
	if self.fields['src'] != '' and self.fields['dest'] != '' :
	    c.AllBatches.elements[self.fields['src']].remove_source(self)
	    c.AllBatches.elements[self.fields['dest']].remove_destination(self)
	tmp = ['time', 'remark', 'src', 'dest', 'quantity' ]
	for elem in tmp:
	    self.fields[elem] = data[elem]
	self.fields['m_id'] = c.AllBatches.elements[data['src']].fields['m_id']
	if 'active' in data :
	    self.fields['active'] = '1'
	else :
	    self.fields['active'] = '0'
	if self.fields['active'] == '1' :
	    c.AllBatches.elements[data['src']].add_source(self)
	    c.AllBatches.elements[data['dest']].add_destination(self)
	else:
	    c.AllBatches.elements[data['src']].remove_source(self)
	    c.AllBatches.elements[data['dest']].remove_destination(self)
	self.save(c,user)
	
    def get_name(self):
	return 'pouring'
	
class Group(ConfigurationObject):
    def __init__(self, config):
	ConfigurationObject.__init__(self)
	self.classes = {}
	self.groups = {}
	self.config = config
	self.parents = []
	self.children = []
	self.related = []

    def __repr__(self):
        string = unicode(self.id) + " " + self.fields['acronym']
        return string

    def __str__(self):
        string = "\nGroup :"
        for field in self.fields:
            string = string + "\n" + field + " : " + self.fields[field]
        return string + "\n"
	
    def get_type(self):
	return 'g'
	
    def containsGroup(self, oGroup):
	if len(self.groups) >0:
	    for k,v in self.groups.items():
		if self.keyColumn in oGroup.fields.keys():
		    if k == oGroup.fields[self.keyColumn] :
			return True
		elif v.containsGroup(oGroup):
		    return True
	return False
	    
    def get_name_listing(self):
	return 'groups'
	
    def validate_form(self, data, configuration, lang):
	tmp = ConfigurationObject.validate_form(self, data, configuration, lang)	
	if tmp is True:
	    tmp = ''
	for k,v in configuration.findAllFromObject(self).elements.items():
	    if k in data:
		if self.getID() in v.parents or self.getID() in v.siblings:
		    tmp += configuration.AllMessages.elements['grouprules'].getName(lang) + '\n'
		    return tmp
	if tmp == '':
	    return True
	return tmp
	
    def set_value_from_data(self, data, c,user):
	ConfigurationObject.set_value_from_data(self, data, c,user)
	self.parents = []
	self.children = []
	self.siblings = []
	for a in self.related:
	    if a not in data:
		self.write_group(a,c,user,'1')
		self.related.remove(a)
	for k in c.findAllFromObject(self).elements.keys():
	    if k in data and k not in self.related:
		self.related.append(k)
		self.write_group(k,c,user,'0')
	c.findAllFromObject(self).load_family()
	
    def write_group(self, parentid, configuration, user, active):
  	with open(configuration.findAllFromObject(self).csvRelations,"a") as csvfile:
  	    tmpCode={}
	    tmpCode['begin'] = unicode(datetime.datetime.now().strftime(datetimeformat))
	    tmpCode['parent_id'] = parentid
	    tmpCode['child_id'] = self.getID()
	    tmpCode["user"] = user.fields['u_id']
	    tmpCode['active'] = active
	    writer = unicodecsv.DictWriter(csvfile, delimiter = '\t', fieldnames = configuration.findAllFromObject(self).fieldrelations, encoding="utf-8")
	    writer.writerow(tmpCode)
	
    def get_group(self):
	return self.related
	
    def get_parents(self):
	return self.parents
	
    def get_children(self):
	return self.children
	
    def get_siblings(self):
	return self.siblings
    
    def add_parent(self, parent):
	if not parent.getID() in self.parents:
	    self.parents.append(parent.getID())
	    
    def remove_parent(self, exparent):
	self.parents.remove(exparent.getID())
	    
    def add_child(self, child):
	if not child.getID() in self.children:
	    self.children.append(child.getID())
	    
    def remove_child(self, exchild):
	self.children.remove(exchild.getID())
    
    def add_relation(self, group):
	if not group.getID() in self.related:
	    self.related.append(group.getID())
    
    def remove_relation(self, group):
	self.related.remove(group.getID())
	
    def load_parents(self, group = None):
	if group == None:
	    group = self
	    self.parents = []
	for i in self.related:
	    if i not in self.parents:
		self.parents.append(i)
		self.config.findAllFromType(self.get_type()).elements[i].load_parents()
	    else :
		print "Error Group : GROUPE EN RELATION CIRCLAIRE"
		
    def load_children(self, g = None):
	if g == None:
	    g = self
	for k, group in self.config.findAllFromType(self.get_type()).elements.items():
	    if self.getID() in group.related:
		if group.getID() not in g.children:
		    g.add_child(group)
		    group.load_children(g)
		else:
		    print "Error Group : GROUPE EN RELATION CIRCLAIRE"
		    
    def load_siblings(self):
	for k,group in self.config.findAllFromType(self.get_type()).elements.items():
	    for rel in group.related:
		if rel in self.related and k != self.getID():
		    self.siblings.append(k)
	    
	
class GrUsage(Group):
    def __init__(self,config):
	Group.__init__(self,config)
	self.keyColumn = 'gu_id'
	
    def get_type(self):
	return 'gu'
		
    def get_name(self):
	return 'guse'
	
    def validate_form(self, data, configuration, lang):
	tmp = Group.validate_form(self, data, configuration, lang)	
	if tmp == '':
	    return True
	return tmp
	
    def set_value_from_data(self, data, c,user):
	Group.set_value_from_data(self, data, c,user)
	self.save(c,user)
	
class CheckPoint(Group):
    def __init__(self,config):
	Group.__init__(self,config)
	self.keyColumn = 'h_id'
	self.tm = []
	self.vm = []
	self.dm = []
	
    def get_type(self):
	return 'h'
		
    def get_name(self):
	return 'checkpoint'
	
    def validate_form(self, data, configuration, lang):
	tmp = Group.validate_form(self, data, configuration, lang)	
	if tmp == '':
	    return True
	return tmp
	
    def set_value_from_data(self, data, c,user):
	Group.set_value_from_data(self, data, c,user)
	self.fields['gr_id'] = data['recipe']
	self.save(c,user)
	
    def remove_tm(self, model):
	if model.fields['tm_id'] in self.tm:
	    self.tm.remove(model.fields['tm_id'])
	    
    def add_tm(self,model):
	self.remove_tm(model)
	if len(self.tm) == 0:
	    self.tm.append(model.getID())
	else:
	    rank = int(model.fields['rank'])
	    insert = False
	    for i in range(len(self.tm)):
		tmp = self.config.AllTransferModels.elements[self.tm[i]]
		tmprank = int(tmp.fields['rank'])
		if rank < tmprank:
		    insert = True
		    self.tm.insert(i,model.getID())
		    break
	    if insert is False:
		self.tm.append(tm.getID())	    
    
    def remove_dm(self, model):
	if model.fields['dm_id'] in self.dm:
	    self.dm.remove(model.fields['dm_id'])
	    
    def add_dm(self,model):
	self.remove_dm(model)
	if len(self.dm) == 0:
	    self.dm.append(model.getID())
	else:
	    rank = int(model.fields['rank'])
	    insert = False
	    for i in range(len(self.dm)):
		dmp = self.config.AllManualDataModels.elements[self.dm[i]]
		dmprank = int(dmp.fields['rank'])
		if rank < dmprank:
		    insert = True
		    self.dm.insert(i,model.getID())
		    break
	    if insert is False:
		self.dm.append(dm.getID())
    
    def remove_vm(self, model):
	if model.fields['vm_id'] in self.vm:
	    self.vm.remove(model.fields['vm_id'])
	    
    def add_vm(self,model):
	self.remove_vm(model)
	if len(self.vm) == 0:
	    self.vm.append(model.getID())
	else:
	    rank = int(model.fields['rank'])
	    insert = False
	    for i in range(len(self.vm)):
		vmp = self.config.AllPouringModels.elements[self.vm[i]]
		vmprank = int(vmp.fields['rank'])
		if rank < vmprank:
		    insert = True
		    self.vm.insert(i,model.getID())
		    break
	    if insert is False:
		self.vm.append(vm.getID())
    
    def get_model_sorted(self):
	listdm = self.get_hierarchy_dm()
	listvm = self.get_hierarchy_vm()
	listtm = self.get_hierarchy_tm()
	sum = len(listdm) + len(listvm) + len (listtm)
	count = 0
	sorted = []
	iddm = 0
	idtm = 0
	idvm = 0
	while count < sum:
	    if iddm < len(listdm):
		tmpdm = self.config.AllManualDataModels.elements[listdm[iddm]]
	    else:
		tmpdm = None
	    if idtm < len(listtm):
		tmptm = self.config.AllTransferModels.elements[listtm[idtm]]
	    else:
		tmptm = None
	    if idvm < len(listvm):
		tmpvm = self.config.AllPouringModels.elements[listvm[idvm]]
	    else:
		tmpvm = None
	    if tmpdm is not None :
		rank = tmpdm.fields['rank']
		type = 'dm'
	    elif tmptm is not None:
		rank = tmptm.fields['rank']
		type = 'tm'
	    elif tmpvm is not None:
		rank = tmpvm.fields['rank']
		type = 'vm'
	    else:
		break
	    if tmptm is not None :
		if tmptm.fields['rank'] < rank:
		    type = 'tm'
		    rank = tmptm.fields['rank']
	    if tmpvm is not None:
		if tmpvm.fields['rank'] < rank:
		    type = 'vm'
		    rank = tmpvm.fields['rank']
	    if type == 'vm':
		sorted.append(tmpvm)
		idvm += 1
		count += 1
	    elif type == 'tm':
		sorted.append(tmptm)
		idtm += 1
		count += 1
	    elif type == 'dm':
		sorted.append(tmpdm)
		iddm += 1
		count += 1
	return sorted
	
    def validate_control(self,data, lang):
	model = self.get_model_sorted()
	countdm = 1
	countvm = 1
	counttm = 1
	tmp = ''
	try:
	    value = datetime.datetime.strptime(data['time'],datetimeformat)
	except:
	    traceback.print_exc()
	    tmp += self.config.AllMessages.elements['timerules'].getName(lang) + '\n'
	for m in model:
	    type = m.get_type()
	    if type == 'dm':
		try:
		    value = float(data['dm_value_'+str(countdm)])
		except:
		    tmp += self.config.AllMessages.elements['floatrules'].getName(lang) + ' '+data['dm_value_'+str(countdm)]+'\n'
		countdm += 1
	    elif type == 'vm' :
		try:
		    value = float(data['vm_quantity_'+str(countvm)])
		except:
		    tmp += self.config.AllMessages.elements['floatrules'].getName(lang) + ' '+data['vm_quantity_'+str(countvm)]+'\n'
		countvm += 1
	if tmp == '' :
	    return True
	return tmp
    
    def create_control(self, data, user):
	model = self.get_model_sorted()
	countdm = 1
	countvm = 1
	counttm = 1
	for m in model:
	    type = m.get_type()
	    currObject = self.config.getObject('new', type[0])
	    if type == 'dm':
		tmp = self.create_data(data,type, countdm)
		countdm += 1
	    elif type == 'tm' :
		tmp = self.create_data(data,type, counttm)
		counttm += 1
	    elif type == 'vm' :
		tmp = self.create_data(data,type, countvm)
		countvm += 1
	    currObject.set_value_from_data(tmp,self.config,user)
	type = data['batch'].split('_')[0]
	id = data['batch'].split('_')[1]
	self.write_control( type, id, user)
	self.config.findAllFromType(type).elements[id].add_checkpoint(self.getID())
		
    def create_data(self, data, type, count):
	batch = data['batch']
	time = data['time']
	tmp = {}
	tmp['time'] = time
	tmp['active'] = '1'
	if type == 'dm':
	    tmp['component'] = batch
	    tmp['remark'] = data['dm_remark_'+str(count)]
	    tmp['measure'] = data['dm_measure_'+str(count)]
	    tmp['value'] = data['dm_value_'+str(count)]
	elif type == 'tm' :
	    tmp['object'] = batch
	    tmp['position'] = data['tm_position_'+str(count)]
	    tmp['remark'] = data['tm_remark_'+str(count)]
	elif type == 'vm' :
	    if 'vm_src_'+str(count) in data :
		tmp['src'] = data['vm_src_'+str(count)]
		tmp['dest'] = batch.split('_')[1]
	    else :
		tmp['dest'] = data['vm_dest_'+str(count)]
		tmp['src'] = batch.split('_')[1]
	    tmp['quantity'] = data['vm_quantity_'+str(count)]
	    tmp['remark'] = data['tm_remark_'+str(count)]
	return tmp
    
    def write_control(self, type,id, user):
  	with open(self.config.findAllFromObject(self).csvControls,"a") as csvfile:
  	    tmpCode={}
	    tmpCode['begin'] = unicode(datetime.datetime.now().strftime(datetimeformat))
	    tmpCode['h_id'] = self.getID()
	    tmpCode['object_type'] = type
	    tmpCode['object_id'] = id
	    tmpCode["user"] = user.fields['u_id']
	    writer = unicodecsv.DictWriter(csvfile, delimiter = '\t', fieldnames = self.config.findAllFromObject(self).fieldcontrols, encoding="utf-8")
	    writer.writerow(tmpCode)
	    
    def get_hierarchy_dm(self, list= None, group = None):
	if group == None:
	    list = []
	    group = self
	for e in group.dm:
	    list.append(e)
	for e in group.parents:
	    self.get_hierarchy_dm(list,self.config.AllCheckPoints.elements[e])
	return list
	
    def get_hierarchy_tm(self, list= None, group = None):
	if group == None:
	    list = []
	    group = self
	for e in group.tm:
	    list.append(e)
	for e in group.parents:
	    self.get_hierarchy_tm(list,self.config.AllCheckPoints.elements[e])
	return list
	
    def get_hierarchy_vm(self, list= None, group = None):
	if group == None:
	    list = []
	    group = self
	for e in group.vm:
	    list.append(e)
	for e in group.parents:
	    self.get_hierarchy_vm(list,self.config.AllCheckPoints.elements[e])
	return list
	
class GrRecipe(Group):
    def __init__(self,config):
	Group.__init__(self,config)
	self.keyColumn = 'gr_id'
	
    def get_type(self):
	return 'gr'
		
    def get_name(self):
	return 'grecipe'
    
    def validate_form(self, data, configuration, lang):
	tmp = Group.validate_form(self, data, configuration, lang)	
	if tmp == '':
	    return True
	return tmp
	
    def set_value_from_data(self, data, c,user):
	Group.set_value_from_data(self, data, c,user)
	self.save(c,user)
	
class GrFunction(Group):
    def __init__(self,config):
	Group.__init__(self,config)
	self.keyColumn = 'gf_id'
	
    def get_type(self):
	return 'gf'
	
    def get_user_group(self):
	listusers=[]
	for k,user in self.config.AllUsers.elements.items():
	    if user.fields['gf_id'] in self.children or user.fields['gf_id'] == self.fields['gf_id']:
		listusers.append(k)
	return listusers
		
    def get_name(self):
	return 'gfunction'
    
    def validate_form(self, data, configuration, lang):
	tmp = Group.validate_form(self, data, configuration, lang)	
	if tmp == '':
	    return True
	return tmp
	
    def set_value_from_data(self, data, c,user):
	Group.set_value_from_data(self, data, c,user)
	self.save(c,user)
	
class Piece(ConfigurationObject):
    def __init__(self, config):
	ConfigurationObject.__init__(self)
	self.config = config	

    def __repr__(self):
        string = unicode(self.id) + " " + self.fields['acronym']
        return string

    def __str__(self):
        string = "\nPiece :"
        for field in self.fields:
            string = string + "\n" + field + " : " + self.fields[field]
        return string + "\n"
	
    def get_type(self):
	return 'p'
	
    def get_name_listing(self):
	return 'places'
	
    def get_name(self):
	return 'place'
	
    def get_sensors_in_component(self, config):
	listSensor = []
	checklist = []
	checklist.append(['p',self.id])
	for k,v in config.AllEquipments.elements.items():
	    transfer = v.get_actual_position()
	    if transfer is not None: 
		transfer = config.AllTransfers.elements[transfer]
		if transfer.fields['cont_type'] == 'e'and  transfer.fields['cont_id'] == self.id:
		    checklist.append(['e',k])
	for k, sensor in config.AllSensors.elements.items():
	    for comp,id in checklist:
		if sensor.is_in_component(comp,id):
		    listSensor.append(k)
	return listSensor
	
    def validate_form(self, data, configuration, lang):
	return ConfigurationObject.validate_form(self, data, configuration, lang)	
	
    def set_value_from_data(self, data, c,user):
	ConfigurationObject.set_value_from_data(self, data, c,user)
	self.fields['colorgraph'] = data['colorgraph']
	self.fields['gu_id'] = data['group']
	self.save(c,user)
	
    def get_group(self):
	return self.fields['gu_id']
	
	
class AlarmLog(ConfigurationObject):

    def __init__(self):
	ConfigurationObject.__init__(self)	

    def __repr__(self):
        string = unicode(self.id) 
        return string

    def __str__(self):
        string = "\nAlarmLog :"
        for field in self.fields:
            string = string + "\n" + field + " : " + self.fields[field]
        return string + "\n"
	
    def get_type(self):
	return 'al'
	
    def get_name_listing(self):
	return ''
	
    def get_name(self):
	return 'alarmlog'

class ExportData():
    def __init__(self, config, elem,cond, user):
	self.config = config
	self.fieldnames = ['timestamp','user','type', 'b_id', 'p_id', 'e_id', 'c_id','m_id','sensor','value','unit', 'category', 'duration', 'remark']
	self.history = []
	self.filename = csvDir + "exportdata.csv"
	self.cond = cond
	self.elem = elem
	if elem.get_type() != 'b' :
	    self.batches = elem.get_batch_in_component(self.config)
	else :
	    self.batches = []
	    self.batches.append(self.elem)
	self.b = None
	self.user = user
	self.data = []
	self.transfers = []
	self.pourings = []
	self.elements = []
	self.min = 99999999999
	self.max = -99999999999
	self.average = 0
	self.count = 0
	
    def load_data(self):
	for d in self.b.data:
	    self.data.append(self.config.AllManualData.elements[d])
		
    def load_transfers(self):
	for t in self.b.position:
	    self.transfers.append(self.config.AllTransfers.elements[t])
	    
    def load_pourings(self):
	for t in self.b.destination:
	    self.pourings.append(self.config.AllPourings.elements[t])
	for t in self.b.source:
	    self.pourings.append(self.config.AllPourings.elements[t])

    def create_export(self):
	if self.elem.get_type() != 'b':
	    if self.cond['manualdata'] is True:
		for data in self.elem.data:
		    self.elements.append(self.transform_object_to_export_data(self.config.AllManualData.elements[data]))
	    if self.cond['transfer'] is True:
		for t in self.elem.position:
		    self.elements.append(self.transform_object_to_export_data(self.config.AllTransfers.elements[t]))		    
	    
	for self.b in self.batches :
	    self.load_data()
	    self.load_transfers()
	    self.load_pourings()
	    
	    self.load_hierarchy()
	    
            bexport = self.transform_object_to_export_data(self.b)
	    self.elements.append(bexport)
	    lastSensor = None
	    count = 0
	    while count < (len(self.history)):
		e = self.history[count]
		begin = useful.date_to_timestamp(e.fields['time'], datetimeformat)
		infos = None
		tmp = self.transform_object_to_export_data(e)
		if len(self.history)-1 == count :
		    end = int(time.time())
		else :
		    end = useful.date_to_timestamp(self.history[count+1].fields['time'], datetimeformat)
                bexport['duration'] = self.get_duration(bexport['timestamp'],end)
		if self.cond['manualdata'] is True and e.get_type() == 'd':
		    self.elements.append(tmp)
		elif self.cond['transfer'] is True and e.get_type() == 't':
		    tmp['duration'] = self.get_duration(begin, end) 
		    self.elements.append(tmp)
		elif self.cond['pouring'] is True and e.get_type() == 'v':
		    self.elements.append(tmp)
		if e.get_type() == 'd':
		    if lastSensor != None:
			infos = self.get_all_in_component(lastSensor,begin,end)
		else :
		    e = self.config.getObject(e.fields['cont_id'],e.fields['cont_type'])
		    infos = self.get_all_in_component(e,begin,end)
		    lastSensor = e
		if infos is not None:
		    self.add_value_from_sensors(infos,lastSensor)
		count += 1
		

    def write_csv(self):
	with open(self.filename,'w') as csvfile:
	    csvfile.write(self.fieldnames[0])
	    tmp = 1
	    while tmp < len(self.fieldnames):
		csvfile.write('\t'+self.fieldnames[tmp])
		tmp = tmp + 1
            csvfile.write('\n')
        for e in self.elements :
            with open(self.filename,'a') as csvfile:
                writer = unicodecsv.DictWriter(csvfile, delimiter = "\t",fieldnames=self.fieldnames,encoding="utf-8")
                writer.writerow(e)
	
    def add_value_from_sensors(self, infos, component):
	sensors = component.get_sensors_in_component(self.config)
	for a in infos.keys() :
	    self.min = 99999999999
	    self.max = -99999999999
	    self.average = 0.0
	    timemin = ''
	    timemax = ''
	    self.count = 0
            if infos[a] is not None :
                begin = infos[a][0][0]
	        for value in infos[a]:
		    tmp = value[1][0]
                    sensor = self.transform_object_to_export_data(self.config.AllSensors.elements[a])
                    sensor['remark'] = ''
		    sensor['timestamp'] = value[0]
                    end = sensor['timestamp']
		    sensor['value'] = str(tmp)
		    sensor['type'] = 'MES'
		    if tmp is not None:
			tmp = float(value[1][0])
			self.count += 1
			self.average += tmp
			if tmp < self.min :
			    self.min = tmp
			    timemin = sensor['timestamp']
			if tmp > self.max :
			    self.max = tmp
			    timemax = sensor['timestamp']
                    #sensor['typevalue'] = 'DAT'
                    if self.cond['valuesensor'] is True :
		        self.elements.append(sensor)
		if self.count >0 :
		    self.average /= self.count
		if self.cond['specialvalue'] is True and self.count >0:
		    sensor1 = self.transform_object_to_export_data(self.config.AllSensors.elements[a])
		    sensor1['value'] = self.min
		    #sensor1['typevalue'] = 'MIN'
		    sensor1['type'] = 'MIN'
		    sensor1['timestamp'] = timemin
                    sensor1['remark'] = ''
		    self.elements.append(sensor1)
		    sensor2 = self.transform_object_to_export_data(self.config.AllSensors.elements[a])
		    sensor2['value'] = self.max
		    #sensor2['typevalue'] = 'MAX'
		    sensor2['type'] = 'MAX'
		    sensor2['timestamp'] = timemax
                    sensor2['remark'] = ''
		    self.elements.append(sensor2)
		    sensor3 = self.transform_object_to_export_data(self.config.AllSensors.elements[a])
		    sensor3['value'] = self.average
		    #sensor3['typevalue'] = 'AVG'
		    sensor3['type'] = 'AVG'
		    sensor3['timestamp'] = end
                    sensor3['duration'] = self.get_duration(begin,end)
                    sensor3['remark'] = ''
		    self.elements.append(sensor3)
		if self.cond['alarm'] is True :
		    logs = self.config.AllAlarmLogs.get_alarmlog_component(a,begin,end)
		    for log in logs :
			tmp = self.transform_object_to_export_data(log)
			self.elements.append(tmp)	    
	
	
    def load_hierarchy(self):
        self.history = []
	i = 0
	j = 0
	k = 0
	while i < len(self.data) and j < len(self.transfers) and k < len(self.pourings):
	    timed = useful.date_to_timestamp(self.data[i].fields['time'], datetimeformat)
	    timet = useful.date_to_timestamp(self.transfers[j].fields['time'], datetimeformat)
	    timev = useful.date_to_timestamp(self.pourings[j].fields['time'], datetimeformat)
	    tmp = timed
	    cond = 'd'
	    if timet < tmp :
		tmp = timet
		cond = 't'
	    if timev < tmp:
		tmp = timev
		cond = 'v'
	    if cond == 'd':
		self.history.append(self.data[i])
		i += 1
	    elif cond == 't':
		self.history.append(self.transfers[j])
		j += 1
	    elif cond == 'v':
		self.history.append(self.pourings[k])
		k += 1
	if i < len(self.data):
	    while i< len(self.data):
		self.history.append(self.data[i])
		i += 1
	if j < len(self.transfers):
	    while j< len(self.transfers):
		self.history.append(self.transfers[j])
		j += 1
	if k < len(self.pourings):
	    while k< len(self.pourings):
		self.history.append(self.pourings[k])
		k += 1
		
    def get_all_in_component(self,component,begin,end, infos = None):
	if infos is None :
	    infos = {}
	sensors = component.get_sensors_in_component(self.config)
	tmp = component.get_transfers_in_time_interval(begin,end)
	if len(tmp) > 0 :
	    for t in tmp :
		infos = self.get_all_in_component(t.get_cont(),begin,end,infos)
	for a in sensors:
	    infos[a] = self.config.AllSensors.elements[a].fetch(begin,end)
	return infos
	
    def transform_object_to_export_data(self, elem):
	tmp = self.get_new_line()
	if elem.creator:
	    tmp['user'] = elem.creator
            if self.cond['acronym'] is True and elem.creator:
                aUser = self.config.AllUsers.elements[elem.creator]
                if aUser and aUser.fields['acronym']:
                    tmp['user'] = aUser.fields['acronym']
        if elem.created:
	    tmp['timestamp'] = useful.date_to_timestamp(elem.created,datetimeformat)		
	if elem.get_type() in 'bcpem' :
	    if elem.get_type() == 'b':
		tmp['timestamp'] = elem.fields['time']
		tmp['unit'] = self.config.AllMeasures.elements[elem.fields['m_id']].fields['unit']
		tmp['value'] = elem.fields['basicqt']
		
	    if self.cond['acronym'] is True :
		tmp[elem.get_type()+'_id'] = elem.fields['acronym']
		if elem.get_type() == 'b':
		    tmp['m_id'] = self.config.AllMeasures.elements[elem.fields['m_id']].fields['acronym']
	    else :
	        tmp[elem.get_type()+'_id'] = elem.getID()
		if elem.get_type() == 'b':
		    tmp['m_id'] = elem.fields['m_id']
	    tmp['remark'] = elem.fields['remark']
	    tmp['type'] = elem.get_type()
	    if elem.get_type() == 'm':
		tmp['m_id'] = elem.getID()
	elif elem.get_type() == 's' :
	    if self.cond['acronym'] is True :
		if elem.fields['p_id'] != '' :
		    tmp['p_id'] = self.config.AllPieces.elements[elem.fields['p_id']].fields['acronym']
		else :
		    tmp['p_id'] = ''
		if elem.fields['e_id'] != '' :
		    tmp['e_id'] = self.config.AllEquipments.elements[elem.fields['e_id']].fields['acronym']
		else :
		    tmp['e_id'] = ''
		if elem.fields['c_id'] != '' :
		    tmp['c_id'] = self.config.AllContainers.elements[elem.fields['c_id']].fields['acronym']
		else :
		    tmp['c_id'] = ''
		tmp['sensor'] = elem.fields['acronym']
		tmp['m_id'] = self.config.AllMeasures.elements[elem.fields['m_id']].fields['acronym']
	    else :
		tmp['p_id'] = elem.fields['p_id']
		tmp['e_id'] = elem.fields['e_id']
		tmp['c_id'] = elem.fields['c_id']
		tmp['sensor'] = elem.fields['s_id']
		tmp['m_id'] = elem.fields['m_id']
	    tmp['unit'] = self.config.AllMeasures.elements[elem.fields['m_id']].fields['unit']
	    tmp['remark'] = elem.fields['remark']
	elif elem.get_type() == 'al' :
	    sensor = self.config.AllSensors.elements[elem.fields['s_id']]
	    tmp['timestamp'] = elem.fields['begintime']
            tmp['type'] = 'ALR'
            if self.cond['acronym'] is True :
                tmp[elem.fields['cont_type']+'_id'] = self.config.findAllFromType(elem.fields['cont_type']).elements[elem.fields['cont_id']].fields['acronym']
                tmp['sensor'] = self.config.AllSensors.elements[elem.fields['s_id']].fields['acronym']
		tmp['m_id'] = self.config.AllMeasures.elements[self.config.AllSensors.elements[elem.fields['s_id']].fields['m_id']].fields['acronym']
            else:
	        tmp[elem.fields['cont_type']+'_id'] = elem.fields['cont_id']
                tmp['sensor'] = elem.fields['s_id']
		tmp['m_id'] = elem.fields['m_id']
	    tmp['duration'] = self.get_duration(useful.date_to_timestamp(elem.fields['begin'],datetimeformat),int(elem.fields['begintime']))
	    tmp['category'] = elem.fields['degree']
	    tmp['value'] = elem.fields['value']
	    tmp['unit'] = self.config.AllMeasures.elements[sensor.fields['m_id']].fields['unit']
	elif elem.get_type() == 'd' :
	    tmp['type'] = 'MAN'
            tmp['timestamp'] = useful.date_to_timestamp(elem.fields['time'],datetimeformat)
            if elem.fields['m_id'] != '':
	        tmp['value'] = elem.fields['value']
	        tmp['unit'] = self.config.AllMeasures.elements[elem.fields['m_id']].fields['unit']
		if self.cond['acronym'] is True :
		    tmp['m_id'] = self.config.AllMeasures.elements[elem.fields['m_id']].fields['acronym']
		else :
		    tmp['m_id'] = elem.fields['m_id']
	    if self.cond['acronym'] is True and elem.fields['m_id'] != '':
	        tmp['m_id'] = self.config.AllMeasures.elements[elem.fields['m_id']].fields['acronym']
                tmp[elem.fields['object_type']+'_id'] = self.config.findAllFromType(elem.fields['object_type']).elements[elem.fields['object_id']].fields['acronym']
	    else:
		tmp['m_id'] = elem.fields['m_id']
                tmp[elem.fields['object_type']+'_id'] = elem.fields['object_id']
	    tmp['remark'] = elem.fields['remark']
	    if self.cond['acronym'] is True :
		tmp['user'] = self.config.AllUsers.elements[elem.fields['user']].fields['acronym']
		tmp[elem.fields['object_type']+'_id'] = self.config.findAllFromType(elem.fields['object_type']).elements[elem.fields['object_id']].fields['acronym']
	    else:
		tmp['user'] = elem.fields['user']
		tmp[elem.fields['object_type']+'_id'] = elem.fields['object_id']
        elif elem.get_type() == 't':
            tmp['type'] = 'TRF'
            tmp['timestamp'] = useful.date_to_timestamp(elem.fields['time'],datetimeformat)
            tmp['remark'] = elem.fields['remark']
            if self.cond['acronym'] is True :
                tmp[elem.fields['cont_type']+'_id'] = self.config.findAllFromType(elem.fields['cont_type']).elements[elem.fields['cont_id']].fields['acronym']
		print self.config.findAllFromType(elem.fields['cont_type']).elements[elem.fields['cont_id']].fields['acronym']
            else :
                tmp[elem.fields['cont_type']+'_id'] = elem.fields['cont_id']
	elif elem.get_type() == 'v':
	    tmp['type'] = 'VERS'
            tmp['timestamp'] = useful.date_to_timestamp(elem.fields['time'],datetimeformat)
            tmp['remark'] = elem.fields['remark']
	    tmp['value'] = elem.fields['quantity']
	    tmp['unit'] = self.config.AllMeasures.elements[elem.fields['m_id']].fields['unit']
	    if elem.fields['src'] == self.b.getID():
		if self.cond['acronym'] is True :
		    tmp['b_id'] = 'TO : ' + self.config.AllBatches.elements[elem.fields['dest']].fields['acronym']
		    tmp['m_id'] = self.config.AllMeasures.elements[elem.fields['m_id']].fields['acronym']
		else:
		    tmp['b_id'] = 'TO : ' + elem.fields['dest']
		    tmp['m_id'] = elem.fields['m_id']
	    else :
		if self.cond['acronym'] is True :
		    tmp['b_id'] = 'FROM : ' + self.config.AllBatches.elements[elem.fields['src']].fields['acronym']
		    tmp['m_id'] = self.config.AllMeasures.elements[elem.fields['m_id']].fields['acronym']
		else:
		    tmp['b_id'] = 'FROM : ' + elem.fields['src']
		    tmp['m_id'] = elem.fields['m_id']
	return tmp

    def get_duration(self, begin, end):
	timestamp = end - begin
	string = ''
	if timestamp > 86400 :
	    string = str(timestamp/86400) + 'd'
	    timestamp = timestamp% 86400
	string += useful.timestamp_to_time(timestamp)
	return string
    

    def get_new_line(self):
	tmp = {}	
	tmp['timestamp'] = ''
	tmp['user'] = ''
	tmp['type'] = ''
	tmp['b_id'] = ''
	tmp['p_id'] = ''
	tmp['e_id'] = ''
	tmp['c_id'] = ''
	tmp['m_id'] = ''
	tmp['sensor'] = ''
	tmp['value'] = ''
	tmp['unit'] = ''
	tmp['category'] = ''
	tmp['duration'] = ''
	tmp['remark'] = ''
	return tmp

class Halfling(ConfigurationObject):

    def __init__(self):
	ConfigurationObject.__init__(self)
	

    def __repr__(self):
        string = unicode(self.id) + " " + self.fields['classname']
        return string

    def __str__(self):
        string = "\nHalfling :"
        for field in self.fields:
            string = string + "\n" + field + " : " + self.fields[field]
        return string + "\n"
	
    def get_type(self):
	return 'halfling'
	
    def getHalfling(self):
	return 'halflings halflings-'+self.fields['glyphname']
	
    def get_name(self):
	return 'halfling'

class Alarm(ConfigurationObject):

    def __init__(self):
	ConfigurationObject.__init__(self)
	

    def __repr__(self):
        string = unicode(self.id) + " " + self.fields['acronym']
        return string

    def __str__(self):
        string = "\nAlarm :"
        for field in self.fields:
            string = string + "\n" + field + " : " + self.fields[field]
        return string + "\n"
	
    def get_type(self):
	return 'a'
	
    def validate_form(self, data, configuration, lang):
	tmp =  ConfigurationObject.validate_form(self, data, configuration, lang)
	return tmp	
	
    def set_value_from_data(self, data, c,user):
	ConfigurationObject.set_value_from_data(self, data, c,user)
	tmp = ['o_sms1', 'o_sms2', 'o_email1', 'o_email2', 'o_sound1', 'o_sound2', 'relay1', 'relay2']
	for elem in tmp:
	    self.fields[elem] = data[elem]
	self.save(c,user)
	
	
    def get_alarm_message(self, sensor,config, lang):
	if sensor.get_type() == 's' :
	    mess = config.AllMessages.elements['alarmmessage'].getName(lang)
	    cpe = ''
	    elem = ''
	    currObject = config.AllAlarmLogs.createObject()
	    if not sensor.fields['p_id'] == '':
		cpe = config.AllMessages.elements['place'].getName(lang)
		elem = config.AllPieces.elements[sensor.fields['p_id']]
		currObject.fields['cont_type'] = 'p'
	    elif not sensor.fields['e_id'] == '':
		cpe = config.AllMessages.elements['equipment'].getName(lang)
		elem = config.AllPieces.elements[sensor.fields['e_id']]
		currObject.fields['cont_type'] = 'e'
	    elif not sensor.fields['c_id'] == '':
		cpe = config.AllMessages.elements['container'].getName(lang)
		elem = config.AllPieces.elements[sensor.fields['c_id']]
		currObject.fields['cont_type'] = 'c'
	    currObject.fields['cont_id'] = elem.getID()
	    currObject.fields['s_id'] = sensor.getID()
	    currObject.fields['value'] = unicode(sensor.lastvalue)
	    currObject.fields['typealarm'] = unicode(sensor.actualAlarm)
	    currObject.fields['begintime'] = unicode(sensor.time)
	    currObject.fields['alarmtime'] = unicode(int(sensor.time) * sensor.countActual)
	    currObject.fields['degree'] = unicode(sensor.degreeAlarm)
	    currObject.save(config)
	    return unicode.format(mess,config.HardConfig.hostname, cpe, elem.getName(lang), elem.fields['acronym'], sensor.getName(lang), sensor.fields['acronym'], unicode(sensor.lastvalue), sensor.actualAlarm, useful.timestamp_to_date(sensor.time, datetimeformat), unicode(sensor.degreeAlarm))
	elif sensor.get_type() == 'd' :
	    mess = config.AllMessages.elements['alarmmanual'].getName(lang)
	    elem = config.findAllFromType(sensor.fields['object_type']).elements[sensor.fields['object_id']]
	    name = config.AllMessages.elements[elem.get_name()].getName(lang)
	    if sensor.fields['m_id'] != '' :
		measure = config.AllMeasures.elements[sensor.fields['m_id']].fields['unit']
	    else :
		measure = ''
	    return unicode.format(mess,config.HardConfig.hostname, name, elem.getName(lang), elem.fields['acronym'],unicode(sensor.fields['value']), measure,sensor.fields['remark'], sensor.fields['time'])
	elif sensor.get_type() == 'v' :
	    mess = config.AllMessages.elements['alarmpouring'].getName(lang)
	    elemin = config.AllBatches.elements[sensor.fields['src']]
	    elemout = config.AllBatches.elements[sensor.fields['dest']]
	    if sensor.fields['m_id'] != '' :
		measure = config.AllMeasures.elements[sensor.fields['m_id']].fields['unit']
	    else :
		measure = ''
	    return unicode.format(mess, config.HardConfig.hostname, elemout.getName(lang), elemout.fields['acronym'], elemin.getName(lang), elemin.fields['acronym'],unicode(sensor.fields['quantity']), measure,sensor.fields['remark'], sensor.fields['time'])
       
	
    def get_alarm_title(self, sensor, config, lang):
	if sensor.get_type() == 's' :
	    title = config.AllMessages.elements['alarmtitle'].getName(lang)
	    code = ''
	    equal = ''
	    if sensor.actualAlarm == 'minmin':
		code = '---'
		equal = '<'
	    elif sensor.actualAlarm == 'min':
		code = '-'
		equal = '<'
	    elif sensor.actualAlarm == 'max':
		code = '+'
		equal = '>'
	    elif sensor.actualAlarm == 'maxmax':
		code = '+++'
		equal = '>'
	    return unicode.format(title, code, unicode(sensor.degreeAlarm), sensor.fields['acronym'], unicode(sensor.lastvalue), equal, sensor.fields[sensor.actualAlarm], config.AllMeasures.elements[sensor.fields['m_id']].fields['unit'], sensor.getName(lang))
	elif sensor.get_type() == 'd' :
	    title = config.AllMessages.elements['alarmmanualtitle'].getName(lang)
	    elem = config.findAllFromType(sensor.fields['object_type']).elements[sensor.fields['object_id']]
	    if sensor.fields['m_id'] != ''  :
		measure = config.AllMeasures.elements[sensor.fields['m_id']].fields['unit']
	    else :
		measure = ''
	    return unicode.format(title,sensor.fields['value'],measure,elem.getName(lang))
	elif sensor.get_type() == 'v' :
	    title = config.AllMessages.elements['alarmpouringtitle'].getName(lang)
	    elemin = config.AllBatches.elements[sensor.fields['src']]
	    elemout = config.AllBatches.elements[sensor.fields['dest']]
	    return unicode.format(title,elemout.fields['acronym'],elemout.getName(lang),elemin.fields['acronym'],elemin.getName(lang))
	
    def launch_alarm(self, sensor, config):
	if sensor.get_type() == 's' :
	    level = sensor.degreeAlarm
	    if level == 1 :
		print 'Send mails, level 1'
		userlist = config.AllGrFunction.elements[self.fields['o_email1']].get_user_group()
		for user in userlist:
		    lang = config.AllUsers.elements[user].fields['language']
		    mess = self.get_alarm_message(sensor,config, lang)
		    title = self.get_alarm_title( sensor, config, lang)
		    useful.send_email(config.AllUsers.elements[user].fields['mail'], title, mess)
	    elif level == 2:
		print 'Send mails, level 2'
		userlist = config.AllGrFunction.elements[self.fields['o_email2']].get_user_group()
		for user in userlist:
		    lang = config.AllUsers.elements[user].fields['language']
		    mess = self.get_alarm_message(sensor,config, lang)
		    title = self.get_alarm_title( sensor, config, lang)
		    useful.send_email(config.AllUsers.elements[user].fields['mail'], title, mess)
	elif sensor.get_type() == 'd' :
	    userlist = config.AllGrFunction.elements[self.fields['o_email2']].get_user_group()
	    for user in userlist:
		lang = config.AllUsers.elements[user].fields['language']
		mess = self.get_alarm_message(sensor,config, lang)
		title = self.get_alarm_title( sensor, config, lang)
		print 'Send mail depuis manuel data'
		useful.send_email(config.AllUsers.elements[user].fields['mail'], title, mess)
	elif sensor.get_type() == 'v' :
	    userlist = config.AllGrFunction.elements[self.fields['o_email2']].get_user_group()
	    for user in userlist:
		lang = config.AllUsers.elements[user].fields['language']
		mess = self.get_alarm_message(sensor,config, lang)
		title = self.get_alarm_title( sensor, config, lang)
		print 'Send mail depuis versement'
		useful.send_email(config.AllUsers.elements[user].fields['mail'], title, mess)
	
		
    def get_name_listing(self):
	return 'alarms'
	
    def get_name(self):
	return 'alarm'
	    
	
class Measure(ConfigurationObject):

    def __init__(self):
	ConfigurationObject.__init__(self)
        self.sensors = sets.Set()

    def __repr__(self):
        string = self.id 
        return string

    def __str__(self):
        string = "\nMeasure :"
        for field in self.fields:
            string = string + "\n" + field + " : " + self.fields[field]
        return string + "\n"
	    
    def get_type(self):
	return 'm'
	
    def get_name_listing(self):
	return 'measures'
	
    def get_name(self):
	return 'measure'

    def get_sensors_in_component(self, config):
	listSensor = []
	for k, sensor in config.AllSensors.elements.items():
	    if sensor.is_in_component('m',self.id):
		listSensor.append(k)
	return listSensor
	
    def validate_form(self, data, configuration, lang) :
	tmp = ConfigurationObject.validate_form(self, data, configuration, lang)
	if tmp is True:
	    tmp = ''
	try : 
	    if 'formula' in data  and len(data['formula']) >0:
		value = 1
		owData = unicode(eval(data['formula']))
		value = 0
		owData = unicode(eval(data['formula']))
	except:
	    tmp += configuration.AllMessages.elements['formularules'].getName(lang) + '\n'
	    
	try:
	    if not len(data['unit']) > 0:
		tmp += configuration.AllMessages.elements['unitrules'].getName(lang) + '\n'
	except:
	    tmp += configuration.AllMessages.elements['unitrules'].getName(lang) + '\n'
	
	if tmp == '':
	    return True
	return tmp
	
    def set_value_from_data(self, data, c,user):
	ConfigurationObject.set_value_from_data(self, data, c,user)
	tmp = ['unit']
	for elem in tmp:
	    self.fields[elem] = data[elem]
	self.save(c,user)


class Sensor(ConfigurationObject):
    def __init__(self):
	ConfigurationObject.__init__(self)
	self.actualAlarm = 'typical'
	self.countActual = 0
	self.degreeAlarm = 0
	self.lastvalue = None
	self.time = 0
    
    def __repr__(self):
        string = self.id + " " + self.fields['channel'] + " " + self.fields['acronym']
        return string

    def __str__(self):
        string = "\nSensor :"
        for field in self.fields:
            string = string + "\n" + field + " : " + unicode(self.fields[field])
        string  = string + ' Actual Alarm : ' + self.actualAlarm
        string  = string + ' Count Actual : ' + unicode(self.countActual)
        string  = string + ' Degree Alarm : ' + unicode(self.degreeAlarm)
        return string + "\n"

    def setCorrectAlarmValue(self):
        if self.fields['minmin'] == '' :
            self.fields['minmin'] = -99999999
        if self.fields['min'] == '' :
            self.fields['min'] = -99999999
        if self.fields['max'] == '' :
            self.fields['max'] = 99999999
        if self.fields['maxmax'] == '' :
            self.fields['maxmax'] = 99999999
	if self.fields['lapse1'] =='':
	    self.fields['lapse1'] = 99999999
	if self.fields['lapse2'] =='':
	    self.fields['lapse2'] = 99999999
	if self.fields['lapse3'] =='':
	    self.fields['lapse3'] = 99999999
	
    def get_type(self):
	return 's'
	
    def get_name(self):
	return 'sensor'
	
    def getRRDName(self):
	name = 's_' + unicode(self.id)
	name += '.rrd'
	return name

    def add_component(self, data):
	tmp = data.split('_')
	typeComponent = tmp[-2][-1]
	if typeComponent == 'p' :
	    self.fields['p_id'] = tmp[-1]
	    self.fields['e_id'] = ''
	    self.fields['c_id'] = ''
	elif typeComponent == 'c' :
	    self.fields['c_id'] = tmp[-1]
	    self.fields['e_id'] = ''
	    self.fields['p_id'] = ''
	elif typeComponent == 'e' :
	    self.fields['e_id'] = tmp[-1]
	    self.fields['p_id'] = ''
	    self.fields['c_id'] = ''
	elif typeComponent == 'm' :
            self.fields['m_id'] = tmp[-1]
	    
    def add_measure(self, data):
	tmp = data.split('_')
	self.fields['m_id']= tmp[-1]
	    
	    
    def add_phase(self, data):
	self.fields['h_id'] = data

    def update(self, now, value ,config):
	if value is not None :
	    self.lastvalue = value
	    self.updateRRD(now, value)

            minutes = int(now / 60)
            #GMT + DST
            hours = (int(minutes / 60) % 24)+100 + 2
            minutes = (minutes % 60)+100
            strnow = unicode(hours)[1:3]+":"+unicode(minutes)[1:3]
	    if config.screen is not None :
		pos = config.screen.show(config.screen.begScreen,strnow)
		pos = config.screen.showBW(pos+2,self.get_acronym())
		pos = config.screen.show(pos+2,unicode(round(float(value),1)))
            if self.fields['m_id']:
                id_measure = unicode(self.fields['m_id'])
                if id_measure in config.AllMeasures.elements and config.screen is not None:
                    measure = config.AllMeasures.elements[id_measure]
                    pos = config.screen.show(pos,measure.fields['unit'])
                
	    typeAlarm,symbAlarm = self.getTypeAlarm(value)
            print (u'Sensor update Channel : '+ self.fields['channel'] + u'    ' + self.fields['sensor'] + u' ==> ' + self.fields['acronym'] + u' = ' + unicode(value))
	    if typeAlarm == 'typical' :
		self.setTypicalAlarm()
	    else:
		if not (( typeAlarm == 'min' and self.actualAlarm == 'minmin' ) or ( typeAlarm == 'max' and self.actualAlarm == 'maxmax')) :
		    self.actualAlarm = typeAlarm
		if config.screen is not None :
		    config.screen.showBW(-1,symbAlarm)
		self.launchAlarm(config, now)
	    if config.screen is not None :
		config.screen.end_line()
	else :
	    #TODO : si on ne sait pas se connecter au senseur, rajouter Alarme " Erreur Senseur not working"
	    print 'Impossible d acceder au senseur TO DO'
	
    def updateRRD(self,now, value):
        value = float(value)
	rrdtool.update(str(rrdDir +self.getRRDName()) , '%d:%f' % (now ,value))
	
    def createRRD(self):
	name = re.sub('[^\w]+', '', self.fields['acronym'])
	now = str( int(time.time())-60)
	if self.fields['channel'] in queryChannels :
	    data_sources = str('DS:'+name+':GAUGE:120:U:U')
	    rrdtool.create( str(rrdDir+self.getRRDName()), "--step", "60", '--start', now, data_sources, 'RRA:LAST:0.5:1:43200', 'RRA:AVERAGE:0.5:5:103680', 'RRA:AVERAGE:0.5:30:86400')
	elif self.fields['channel'] == 'radio' :
	    data_sources = str('DS:'+name+':GAUGE:360:U:U')
	    rrdtool.create( str(rrdDir+self.getRRDName()), "--step", "180", '--start', now, data_sources, 'RRA:LAST:0.5:1:14400', 'RRA:AVERAGE:0.5:5:34560', 'RRA:AVERAGE:0.5:30:28800')	    
	
    def getTypeAlarm(self,value):
	value = float(value)
	if self.fields['minmin'] and value <= float(self.fields['minmin']):
	    return 'minmin','--'
	elif self.fields['min'] and value <= float(self.fields['min']):
	    return 'min','-'
	elif self.fields['maxmax'] and value > float(self.fields['maxmax']):
	    return 'maxmax','++'
	elif self.fields['max'] and value > float(self.fields['max']):
	    return 'max','+'
	else:
	    return 'typical','='
	    
    def launchAlarm(self, config, now):
        print 'lancement alarme Sensor : ' + self.getName('EN')
	if self.degreeAlarm == 0 :
	    self.degreeAlarm = 1
	    self.countAlarm = 0
	    self.time = now
	    if int(float(self.fields['lapse1'])) == 0 :
		config.AllAlarms.elements[self.get_alarm()].launch_alarm(self, config)
		self.degreeAlarm = 2
	else:
	    self.countAlarm = self.countAlarm + 1
	    if self.degreeAlarm == 1 and self.countAlarm >= int(self.fields['lapse1']) :
		config.AllAlarms.elements[self.get_alarm()].launch_alarm(self, config)
		self.degreeAlarm = 2
                self.countAlarm = 0
	    elif self.degreeAlarm == 2 and self.countAlarm >= int(self.fields['lapse2']) :
		config.AllAlarms.elements[self.get_alarm()].launch_alarm(self, config)
		self.degreeAlarm = 3
                self.countAlarm = 0
	    elif self.degreeAlarm == 3 and self.countAlarm >= int(self.fields['lapse3']) :
		config.AllAlarms.elements[self.get_alarm()].launch_alarm(self, config)
		self.setTypicalAlarm()
		
    def setTypicalAlarm(self):
	self.countActual = 0
	self.actualAlarm = 'typical'
	self.degreeAlarm = 0
	self.time = 0
	
    def get_value_sensor(self,config):
	if self.fields['channel'] == 'wire':
	    try:
		sensorAdress = u'/'+unicode(self.fields['sensor'])
##		try:
##                    aDevice = ow.Sensor(str(sensorAdress))
##                except ow.exUnknownSensor:
##                    aDevice = None
##		if aDevice:
##		    owData = aDevice.__getattr__(self.fields['subsensor'])
                owData = config.owproxy.read(sensorAdress+u'/'+unicode(self.fields['subsensor']))
	    except:
		traceback.print_exc()
	elif self.fields['channel'] == 'battery':
            owData = config.batteryVoltage
	elif self.fields['channel'] == 'system':
	    with open(self.fields['sensor'],'r') as sensorfile:
		info = sensorfile.read()
		owData = eval(self.fields['subsensor'])
		print owData
	try:
            if owData:
                if self.fields['formula']:
                    value = float(owData)
                    owData = unicode(eval(self.fields['formula']))
                return owData
        except:
            traceback.print_exc()
	return None
    
    def get_alarm(self):
	if self.actualAlarm == 'typical':
	    return self.fields['a_typical']
	elif self.actualAlarm == 'minmin':
	    return self.fields['a_minmin']
	elif self.actualAlarm == 'min':
	    return self.fields['a_min']
	elif self.actualAlarm == 'max':
	    return self.fields['a_max']
	elif self.actualAlarm == 'maxmax':
	    return self.fields['a_maxmax']
	    
    def get_name_listing(self):
	return 'sensors'
	
    def is_in_component(self,type,id):
	if type == 'e':
	    return id == self.fields['e_id']
	elif type == 'p':
	    return id == self.fields['p_id']
	elif type == 'c':
	    return id == self.fields['c_id']
	elif type == 'm':
	    return id == self.fields['m_id']
	return False
	
    def get_component(self, config):
	if self.fields['p_id'] != '':
	    return config.AllPieces.elements[self.fields['p_id']]
	elif self.fields['e_id'] != '':
	    return config.AllEquipments.elements[self.fields['e_id']]
	elif self.fields['c_id'] != '':
	    return config.AllContainers.elements[self.fields['c_id']]
	
    def get_sensors_in_component(self, config):
	tmp = []
	tmp.append(self.id)
	return tmp
	  
    def fetch(self, start, end=None, resolution=60):
        """Fetch data from the RRD.

        start -- integer start time in seconds since the epoch, or negative for
                 relative to end
        end -- integer end time in seconds since the epoch, or None for current
               time
        resolution -- resolution in seconds"""
        if end is None:
            end = int(time.time())
        if start < 0:
            start += end
        if end - start > resolution :
            end -= end % resolution
            start -= start % resolution
            time_span, _, values = rrdtool.fetch(str(rrdDir+self.getRRDName()), 'AVERAGE','-s', str(int(start)),'-e', str(int(end)),'-r', str(resolution))
            ts_start, ts_end, ts_res = time_span
            times = range(ts_start, ts_end, ts_res)
            return zip(times, values)
	return None
	
    def validate_form(self, data, configuration, lang) :
	tmp = ConfigurationObject.validate_form(self, data, configuration, lang)
	if tmp is True:
	    tmp = ''
	try : 
	    if 'formula' in data  and len(data['formula']) >0:
		value = 1
		owData = unicode(eval(data['formula']))
		value = 0
		owData = unicode(eval(data['formula']))
	except:
	    tmp += configuration.AllMessages.elements['formularules'].getName(lang) + '\n'
	    
	try:
	    if not len(data['component']) > 0:
		tmp += configuration.AllMessages.elements['componentrules'].getName(lang) + '\n'
	except:
	    tmp += configuration.AllMessages.elements['componentrules'].getName(lang) + '\n'
	try:
	    if not len(data['measure']) > 0:
		tmp += configuration.AllMessages.elements['measurerules'].getName(lang) + '\n'
	except:
	    tmp += configuration.AllMessages.elements['measurerules'].getName(lang) + '\n'
	try:
	    if not len(data['channel']) > 0:
		tmp += configuration.AllMessages.elements['channelrules'].getName(lang) + '\n'
	except:
	    tmp += configuration.AllMessages.elements['channelrules'].getName(lang) + '\n'
	try:
	    if not len(data['sensor']) > 0:
		tmp += configuration.AllMessages.elements['sensorrules'].getName(lang) + '\n'
	except:
	    tmp += configuration.AllMessages.elements['sensorrules'].getName(lang) + '\n'
		
	    
	if tmp == '':
	    return True
	return tmp
	
    def set_value_from_data(self, data, c,user):
	ConfigurationObject.set_value_from_data(self, data, c,user)
	tmp = ['channel', 'sensor', 'subsensor', 'valuetype', 'formula', 'minmin', 'min', 'typical', 'max', 'maxmax', 'a_minmin', 'a_min', 'a_typical', 'a_max', 'a_maxmax', 'lapse1', 'lapse2', 'lapse3']
	for elem in tmp:
	    self.fields[elem] = data[elem]
	self.add_component(data['component'])
	self.add_measure(data['measure'])
	self.createRRD()
	self.save(c,user)
    
class Batch(ConfigurationObject):
    def __init__(self, config):
	ConfigurationObject.__init__(self)
	self.config = config
	self.source = []
	self.destination = []
	self.checkpoints = []

    def __repr__(self):
        string = unicode(self.id) + " " + self.fields['acronym']
        return string

    def __str__(self):
        string = "\nBatch :"
        for field in self.fields:
            string = string + "\n" + field + " : " + self.fields[field]
        return string + "\n"
	
    def get_type(self):
	return 'b'
	
    def get_name_listing(self):
	return 'batches'
    
    def get_name(self):
	return 'batch'
	
    def add_measure(self, data):
	tmp = data.split('_')
	self.fields['m_id']= tmp[-1]
	
    def get_cost(self, quantity):
	value = float(self.fields['cost'])/float(self.fields['basicqt'])
	return value * float(quantity)
	
    def get_quantity_used(self):
	qt = 0
	for e in self.source:
	    qt += float(self.config.AllPourings.elements[e].fields['quantity'])
	return qt
	
    def get_lifetime(self):
	if self.fields['basicqt'] == '' or self.fields['basicqt'] == 0:
	    self.fields['basicqt'] = 0
	else:
	    qt = self.get_quantity_used()
	    tmp = float(self.fields['basicqt']) - qt
	    if tmp < 0 :
		return useful.date_to_timestamp(self.pourings.fields['time'],datetimeformat) - useful.date_to_timestamp(self.fields['time'],datetimeformat)
	return useful.get_timestamp() - useful.date_to_timestamp(self.fields['time'],datetimeformat)
		
    def add_source(self, pouring):
	self.remove_source(pouring)
	if len(self.source) == 0:
	    self.source.append(pouring.getID())
	else:
	    time = useful.date_to_timestamp(pouring.fields['time'],datetimeformat)
	    insert = False
	    for i in range(len(self.source)):
		tmp = self.config.AllPourings.elements[self.source[i]]
		tmptime = useful.date_to_timestamp(tmp.fields['time'],datetimeformat)
		if time < tmptime:
		    insert = True
		    self.source.insert(i,pouring.getID())
		    break
	    if insert is False:
		self.source.append(pouring.getID())
    
    def remove_source(self, pouring):
	if pouring.getID() in self.source:
	    self.source.remove(pouring.getID())
	    
    def add_destination(self, pouring):
	self.remove_destination(pouring)
	if len(self.destination) == 0:
	    self.destination.append(pouring.getID())
	else:
	    time = useful.date_to_timestamp(pouring.fields['time'],datetimeformat)
	    insert = False
	    for i in range(len(self.destination)):
		tmp = self.config.AllPourings.elements[self.destination [i]]
		tmptime = useful.date_to_timestamp(tmp.fields['time'],datetimeformat)
		if int(time) < int(tmptime):
		    insert = True
		    self.destination.insert(i,pouring.getID())
		    break
	    if insert is False:
		self.destination.append(pouring.getID())
    
    def remove_destination(self, pouring):
	if pouring.getID() in self.destination:
	    self.destination.remove(pouring.getID())
	    
    def add_checkpoint(self, cp):
	self.checkpoints.append(cp)
		
    def get_residual_quantity(self):
	val = self.get_quantity_used()
	if self.fields['basicqt'] == '' or self.fields['basicqt'] == 0:
	    self.fields['basicqt'] = 0
	return float(self.fields['basicqt']) - val
	
    def clone(self, user, name = 1 ):
	b = self.config.getObject('new','b')
	b.fields['active'] = self.fields['active']
	tmp = len(self.fields['acronym'])-self.fields['acronym'].rfind('_')-1-len(str(name))
	tmpname = self.fields['acronym'][0:self.fields['acronym'].rfind('_')+1] + '0' * tmp + str(name)
	allObjects = self.config.findAllFromObject(self)    
	cond = allObjects.unique_acronym( tmpname, self.id)
	while not cond:
	    name += 1
	    tmp = len(self.fields['acronym'])-self.fields['acronym'].rfind('_')-1-len(str(name))
	    tmpname = self.fields['acronym'][0:self.fields['acronym'].rfind('_')+1] + '0' * tmp + str(name)
	    cond = allObjects.unique_acronym( tmpname, self.id)
	b.fields['acronym'] = tmpname
	b.fields['basicqt'] = self.fields['basicqt']
	b.fields['m_id'] = self.fields['m_id']
	b.fields['time'] = self.fields['time']
	b.fields['cost'] = self.fields['cost']
	b.fields['remark'] = self.fields['remark']
	b.fields['gr_id'] = self.fields['gr_id']
	for lang in self.config.AllLanguages.elements:
	    b.setName(lang, self.get_real_name(lang),user, self.config.getKeyColumn(b))
	b.creator = user.fields['u_id']
	b.created = b.fields['begin']
	b.save(self.config,user)
	
    def validate_form(self, data, configuration, lang) :
	tmp = ConfigurationObject.validate_form(self, data, configuration, lang)
	if tmp is True:
	    tmp = ''
	try:
	    value = datetime.datetime.strptime(data['time'],datetimeformat)
	except:
	    tmp += configuration.AllMessages.elements['timerules'].getName(lang) + '\n'
	    
	try:
	    value = float(data['cost'])
	    if value < 0.0:
		tmp += configuration.AllMessages.elements['costrules'].getName(lang) + '\n'
	except:
	    tmp += configuration.AllMessages.elements['costrules'].getName(lang) + '\n'
	    
	try:
	    value = float(data['basicqt'])
	    if value < 0.0:
		tmp += configuration.AllMessages.elements['quantityrules'].getName(lang) + '\n'
	except:
	    tmp += configuration.AllMessages.elements['quantityrules'].getName(lang) + '\n'
	    
	if data['measure'] == '':
	    tmp += configuration.AllMessages.elements['measurerules'].getName(lang) + '\n'
	
	if tmp == '':
	    return True
	return tmp
	
    def set_value_from_data(self, data, c,user):
	ConfigurationObject.set_value_from_data(self, data, c,user)
	tmp = ['basicqt', 'time', 'cost']
	for elem in tmp:
	    self.fields[elem] = data[elem]
	self.add_measure(data['measure'])
	self.fields['gr_id'] = data['group']
	self.save(c,user)	
	    
    def get_group(self):
	return self.fields['gr_id']

class PouringModel(ConfigurationObject):
    def __init__(self, config):
	ConfigurationObject.__init__(self)
        self.config = config
            
    def __repr__(self):
        string = unicode(self.id)
        return string

    def __str__(self):
        string = "\nPouring Model :"
        for field in self.fields:
            string = string + "\n" + field + " : " + self.fields[field]
        return string + "\n"
    
    def get_type(self):
	return 'vm'
	
    def get_name(self):
	return 'pouringmodel'
	
    def get_group(self):
	return self.fields['h_id']
    
    def validate_form(self, data, configuration, lang):
	return ConfigurationObject.validate_form(self, data, configuration, lang)	
	
    def set_value_from_data(self, data, c,user):
	if self.fields['h_id'] != '':
	    self.config.AllCheckPoints.elements[self.fields['h_id']].remove_vm(self)
	ConfigurationObject.set_value_from_data(self, data, c,user)
	self.fields['quantity'] = data['quantity']
	if data['src'] != 'current':
	    self.fields['src'] = data['src']
	else:
	    self.fields['src'] = ''
	    self.fields['in'] = '0'
	if data['dest'] != 'current':
	    self.fields['dest'] = data['dest']
	else:
	    self.fields['dest'] = '1'
	    self.fields['in'] = ''
	self.fields['h_id'] = data['checkpoint']
	self.fields['rank'] = data['rank']
	if 'active' in data:
	    self.config.AllCheckPoints.elements[self.fields['h_id']].add_vm(self)
	self.save(c,user)
	
class ManualDataModel(ConfigurationObject):
    def __init__(self, config):
	ConfigurationObject.__init__(self)
        self.config = config
            
    def __repr__(self):
        string = unicode(self.id)
        return string

    def __str__(self):
        string = "\nManual Data Model :"
        for field in self.fields:
            string = string + "\n" + field + " : " + self.fields[field]
        return string + "\n"
    
    def get_type(self):
	return 'dm'
	
    def get_name(self):
	return 'manualdatamodel'
	
    def get_group(self):
	return self.fields['h_id']
    
    def validate_form(self, data, configuration, lang):
	return ConfigurationObject.validate_form(self, data, configuration, lang)	
	
    def set_value_from_data(self, data, c,user):
	if self.fields['h_id'] != '':
	    self.config.AllCheckPoints.elements[self.fields['h_id']].remove_dm(self)
	ConfigurationObject.set_value_from_data(self, data, c,user)
	self.fields['m_id'] = data['measure']
	self.fields['h_id'] = data['checkpoint']
	self.fields['rank'] = data['rank']
	if 'active' in data:
	    self.config.AllCheckPoints.elements[self.fields['h_id']].add_dm(self)
	self.save(c,user)
	
class TransferModel(ConfigurationObject):
    def __init__(self, config):
	ConfigurationObject.__init__(self)
        self.config = config
            
    def __repr__(self):
        string = unicode(self.id)
        return string

    def __str__(self):
        string = "\nModelTransfer :"
        for field in self.fields:
            string = string + "\n" + field + " : " + self.fields[field]
        return string + "\n"
    
    def get_type(self):
	return 'tm'
	
    def get_name(self):
	return 'transfermodel'
	
    def validate_form(self, data, configuration, lang):
	return ConfigurationObject.validate_form(self, data, configuration, lang)	
	
    def set_value_from_data(self, data, c,user):
	if self.fields['h_id'] != '':
	    self.config.AllCheckPoints.elements[self.fields['h_id']].remove_tm(self)
	ConfigurationObject.set_value_from_data(self, data, c,user)
	self.fields['gu_id'] = data['position']
	self.fields['h_id'] = data['checkpoint']
	self.fields['rank'] = data['rank']
	if 'active' in data:
	    self.config.AllCheckPoints.elements[self.fields['h_id']].add_tm(self)
	self.save(c,user)
	
    def get_group(self):
	return self.fields['h_id']
	
class Transfer(ConfigurationObject):
    def __init__(self, config):
	ConfigurationObject.__init__(self)
        self.config = config
            
    def __repr__(self):
        string = unicode(self.id)
        return string

    def __str__(self):
        string = "\nBatchTransfer :"
        for field in self.fields:
            string = string + "\n" + field + " : " + self.fields[field]
        return string + "\n"
    
    def get_type(self):
	return 't'
	
    def get_type_container(self):
	return self.fields['cont_type']
	
    def get_id_container(self):
	return self.fields['cont_id']
	
    def get_type_object(self):
	return self.fields['object_type']
	
    def get_id_object(self):
	return self.fields['object_id']
	
    def set_position(self, pos):
	self.fields['cont_type'] = pos.split('_')[0]
	self.fields['cont_id'] = pos.split('_')[1]
	
    def set_object(self, obj):
	self.fields['object_type'] = obj.split('_')[0]
	self.fields['object_id'] = obj.split('_')[1]
	objects = self.config.findAllFromType(self.fields['object_type'])
	objects.elements[self.fields['object_id']].add_position(self)
	
    def validate_form(self, data, configuration, lang) :
	tmp = ''
	if 'position' in data :
	    objtype = data['object'].split('_')[0]
	    objid = data['object'].split('_')[1]
	    postype = data['position'].split('_')[0]
	    posid = data['position'].split('_')[1]
	    objet = configuration.get_object(objtype,objid)
	    print objet.get_actual_position()
	    if (objet.is_actual_position(postype, posid) is True and objet.get_actual_position() != self.id):
		tmp += configuration.AllMessages.elements['transferrules'].getName(lang) + '\n'
	    if ( objtype =='e' and postype != 'p') or(objtype =='c' and postype not in 'ep'):
		tmp += configuration.AllMessages.elements['transferhierarchy'].getName(lang) + '\n'
	else :
	    tmp += configuration.AllMessages.elements['transferrules'].getName(lang) + '\n'
	if tmp == '':
	    return True
	return tmp
	
    def set_value_from_data(self, data, c,user):
	if self.fields['object_type'] != '' and self.fields['object_id'] != '':
	    self.get_source().remove_position(self)
	tmp = ['time', 'remark']
	for elem in tmp:
	    self.fields[elem] = data[elem]
	if 'active' in data :
	    self.fields['active'] = '1'
	else :
	    self.fields['active'] = '0'
	self.set_position(data['position'])
	self.set_object(data['object'])
	if self.fields['active'] == '1':
	    self.get_source().add_position(self)
	else :
	    self.get_source().remove_position(self)
	self.save(c,user)
	
    def get_source(self):
	return self.config.findAllFromType(self.fields['object_type']).elements[self.fields['object_id']]
	
    def get_cont(self):
	return self.config.findAllFromType(self.fields['cont_type']).elements[self.fields['cont_id']]
		
    def get_name(self):
	return 'transfer'

class Barcode(ConfigurationObject):
    def __init__(self, item):
	ConfigurationObject.__init__(self)
	self.element = item

    def __repr__(self):
        string = ""
        string = string + self.fields['code']
        return string

    def __str__(self):
        string = "\nCode barre :"
        for field in self.fields:
            string = string + "\n" + field + " : " + self.fields[field]
        return string + "\n"
	
    def barcode_picture(self):
	EAN = barcode.get_barcode_class('ean13')
	self.fields['code'] = str(self.fields['code'])
	ean = EAN(self.fields['code'])
	ean.save(barcodesDir+self.fields['code'])
	
    def get_picture_name(self) :
	return self.fields['code']+'.png'
	
    def get_picture(self):
	location = barcodesDir + self.fields['code']
	if not os.path.exists(location) :
	    self.barcode_picture()
	return location
	
    def get_name(self):
	return 'barcode'
