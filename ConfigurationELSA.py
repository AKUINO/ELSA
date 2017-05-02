#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sets
import time
import datetime
import traceback
import unicodecsv
import datetime
import random
import sys
import threading
import time
import os
import rrdtool
import pyownet
import serial
import myuseful as useful
import HardConfig as hardconfig
import barcode
import re
import socket

from I2CScreen import *

import pigpio
PIG = pigpio.pi()

#mise a jour git
csvDir = "../ELSAcsv/csv/"
rrdDir = '../ELSArrd/rrd/'
ttyDir = '/dev/ttyS0'
imgDir = 'static/img'
barcodesDir = 'static/img/barcodes/'
groupWebUsers = '_WEB'
datetimeformat = "%H:%M:%S  -  %d/%m/%y"

_lock_socket = None

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
	
	self.InfoSystem = InfoSystem(self)
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
	self.AllBatches = AllBatches(self)
	self.AllSensors = AllSensors(self)
	self.AllAlarms = AllAlarms(self)
	self.AllAlarmLogs= AllAlarmLogs(self)
	self.AllHalflings = AllHalflings(self)
	self.AllBarcodes = AllBarcodes(self)
	self.AllManualData = AllManualData(self)
	self.connectedUsers = AllConnectedUsers()
	self.AllTransfers = AllTransfers(self)
	self.isThreading = True
	self.UpdateThread = UpdateThread(self)
	self.RadioThread = RadioThread(self)
	self.RadioThread.daemon = True
	self.screen = None
	self.owproxy = None

    def load(self):
	
        if not self.HardConfig.oled is None:
            # 128x64 display with hardware I2C:
            self.screen = I2CScreen(True, disp = SSD1306.SSD1305_132_64(rst=self.HardConfig.oled_reset,gpio=PIG))
            self.screen.clear()
        else:
            self.screen = I2CScreen(False, disp = None)

	

	self.AllLanguages.load()
        self.AllUsers.load()
        self.AllPieces.load()
	self.AllEquipments.load()
	self.AllContainers.load()	
	self.AllMessages.load()
	self.AllGroups.load()
	self.AllMeasures.load()
	self.AllSensors.load()
	self.AllSensors.check_rrd()
	self.InfoSystem.check_rrd()
	self.AllSensors.correctValueAlarm()
	self.AllAlarms.load()
	self.AllHalflings.load()
	self.AllBatches.load()
	#doit toujours être appelé à la fin
	self.AllBarcodes.load()
	self.loadRelation()
	self.AllTransfers.load()
	self.AllManualData.load()
	self.AllAlarmLogs.load()
	self.UpdateThread.start()
	self.RadioThread.start()
	
    
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
	elif className == u"Batch":
	    return self.AllBatches 
	elif className == u"Transfer":
	    return self.AllTransfers 
	elif className == u"ManualData":
	    return self.AllManualData 
        else:
            return None
	    
    def getObject(self, idObject,className):
	if className == u"u":
            return self.AllUsers.getItem(idObject)
        elif className == u"e":
            return self.AllEquipments.getItem(idObject)
        elif className == u"Language":
            return self.AllLanguages.getItem(idObject)
	elif className == u"p":
	    return self.AllPieces.getItem(idObject)
	elif className == u"g":
	    return self.AllGroups.getItem(idObject)
	elif className == u"c":
	    return self.AllContainers.getItem(idObject)
	elif className == u"m":
	    return self.AllMeasures.getItem(idObject)
	elif className == u"cpehm":
	    return self.AllSensors.getItem(idObject)
	elif className == u"a":
	    return self.AllAlarms.getItem(idObject)
	elif className == u"b":
	    return self.AllBatches.getItem(idObject)
	elif className == u"WebTransfer" or className == u"t":
	    return self.AllTransfers.getItem(idObject)
	elif className == u"WebManualData" or className == u"d":
	    return self.AllManualData.getItem(idObject)
	elif className == u"WebAlarmLogs" or className == u"al":
	    return self.AllManualData.getItem(idObject)
        else:
            return None
    
    def getFieldsname(self,className):
        if className == u"u":
            return self.AllUsers.fieldnames
        elif className == u"e":
            return self.AllEquipments.fieldnames
        elif className == u"Language":
            return self.AllLanguages.fieldnames
	elif className == u"p":
	    return self.AllPieces.fieldnames  
	elif className == u"g":
	    return self.AllGroups.fieldnames  
	elif className == u"c":
	    return self.AllContainers.fieldnames  
	elif className == u"m":
	    return self.AllMeasures.fieldnames  
	elif className == u"cpehm":
	    return self.AllSensors.fieldnames 
	elif className == u"a":
	    return self.AllAlarms.fieldnames
	elif className == u"b":
	    return self.AllAlarms.fieldnames
	elif className == u"WebTransfer":
	    return self.AllTransfers.fieldnames
	elif className == u"WebManualData":
	    return self.AllManualData.fieldnames
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
	elif aType == u"b":
	    return self.AllBatches
	elif aType == u"t":
	    return self.AllTransfers
	elif aType == u"d":
	    return self.AllManualData
        else:
            return None
	    
    def loadRelation(self):
	with open(self.csvRelations) as csvfile:
	    reader = unicodecsv.DictReader(csvfile, delimiter = "\t")
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
    
    def hierarchyString(self, g = None, myString = None):
	if myString is None:
	    myString = []
	for k,group in self.AllGroups.elements.items():
	    cond1 = ( g == None and len(group.groups) == 0 )
	    cond2 = ( g is not None and g.fields['g_id'] in group.groups )
	    if cond1 or cond2:
		myString.append(k)
		myString.append('IN')
		self.hierarchyString(group,myString)
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

    def get_parents_list(self, item):
	if item.get_type() == 'g':
	    return self.AllGroups.get_parents(item)
	listparents = []
	for k,g in item.groups.items():
	    tmp = self.AllGroups.get_parents(g)
	    for idGroup in tmp :
		if not idGroup in listparents : 
		    listparents.append(idGroup)
	return listparents
	
    def get_children_list(self, item):
	if item.get_type() == 'g':
	    return self.AllGroups.get_children(item)
	listchildren = []
	for k,g in item.groups.items():
	    tmp = self.AllGroups.get_children(g)
	    for idGroup in tmp :
		if not idGroup in listchildren : 
		    listchildren.append(idGroup)
	return listchildren
	
    def get_user_group(self, idg):
	listusers = []
	childrenlist = self.AllGroups.get_children(self.AllGroups.elements[idg])
	childrenlist.append(idg)
	for k,user in self.AllUsers.elements.items():
	    userG = user.groups.keys()
	    if len(list(set(childrenlist) & set(userG))) > 0:
		listusers.append(k)
	return listusers
	
    def get_object(self, type, id):
	objects = self.findAllFromType(type)
	return objects.elements[id]
	
    def get_time(self):
	return useful.get_time(datetimeformat)
	
    def is_component(self, type):
	if type == 'c' or type == 'p' or type == 'e' or type == 'b':
	    return True
	return False
	
	

class InfoSystem():

##    global lastBatt
##
##    def readBattery(self):
##        if self.conf.HardConfig.battery:
##            try:
##                if self.bus_pi is None:
##                    if self.conf.HardConfig.battery == 'I2C':
##                        #bus_pi = I2C.get_i2c_device(hardConf.battery_address, busnum=hardConf.i2c_bus)
##                        self.bus_pi = SMBus(self.conf.HardConfig.i2c_bus)
##                        print self.bus_pi
##                    elif self.conf.HardConfig.battery == 'SPI':
##                        self.bus_pi = ADCDACPi()  # create an instance of the ADCDAC Pi with a DAC gain set to 1
##
##                        # set the reference voltage.  this should be set to the exact voltage
##                        # measured on the raspberry pi 3.3V rail.
##                        self.bus_pi.set_adc_refvoltage(3.3)
##
##                if self.conf.HardConfig.battery == 'I2C':
##
##                    #bus_pi.write_byte(ADCaddr,0x98)# va charger la valeur du registre
##                                                # dans le mcp
##                    """print 'ADC I2C:',hex(addr)"""
##                    #xa = bus_pi.read_word_data(ADCaddr,0)# recupère la valeur en décimal
##                    xa = self.bus_pi.read_i2c_block_data(hardConf.battery_address,ADCconf,3)
##                    if len(xa) < 2:
##                        continue
##                    x1 = xa[0] # les 2 premier Bytes et les 2 derniers doivent                    
##                    x2 = xa[1] # être inversé pour récupérer la bonne valeur
##                    #x1b = int(x1,16)*256                
##                    #x2b = int(x2,16)
##                    tens = (x1*256) + x2
##                    if tens == 32767:
##                        continue   #TODO: Implanter la bonne synchronisation avec l'arrivee du résultat...
##                    elif tens >=32768:
##                        tens = tens - 65536
##                    tens = (tens*0.0625)/1000 # 0.0625 codé sur 16 bits
##                                              # et /1000 pour avoir la valeur en volt
##                elif self.conf.HardConfig.battery == 'SPI':
##                    tens = self.bus_pi.read_adc_voltage(1, 0)
##                tens= tens*self.conf.HardConfig.battery_divider # 9.4727 est le coefficient du pont diviseur de
##                                      # tension qui est placé au borne de l'ADC
##                tens = round(tens, 2) # Arrondi la valeur au centième près
##
##                if tens < 4:
##                    print ("Sous tension: "+unicode(tens))
##                    pass
##                else:
##                    lastBatt = tens
##                    if tens <= self.conf.HardConfig.battery_breakout_volt:
##                        stats_label.set(unicode(tens)+u"V : ATTENTION")
##                        print (tens+"V lower than "+unicode(self.conf.HardConfig.battery_breakout_volt)+"...")
##                        time.sleep(5)
##                        if self.conf.HardConfig.battery == 'I2C':
##                            self.bus_pi.write_byte(self.conf.HardConfig.battery_address,ADCconf)
##                            xa = self.bus_pi.read_i2c_block_data(self.conf.HardConfig.battery_address,0)
##                            if len(xa) < 3:
##                                continue
##                            x = hex(xa) 
##                            x1 = x[4:6]                    
##                            x2 = x[2:4]
##                            tens = (x1*256) + x2
##                            if tens >=32768:
##                                tens = tens - 65536
##                            tens = (tens*0.0625)/1000
##                        elif self.conf.HardConfig.battery == 'SPI':
##                            tens = self.bus_pi.read_adc_voltage(1, 0)
##                        tens= tens*self.conf.HardConfig.battery_divider
##                        tens = round(tens, 2)
##                        if tens < self.conf.HardConfig.battery_breakout_volt:
##                            stats_label.set(unicode(tens)+u"V : HALTE DU SYSTEME")
##                            print(tens+"V : Shutdown...")
##                            SHUT_NOW(None)
##                    else:  
##                        print 'Sensor battery: '+unicode(tens)+' V'
##
##        except:
##                traceback.print_exc()

    def __init__(self, config):
	self.uptime = 0
	self.memTot = 0
	self.memFree = 0
	self.memAvailable = 0
	self.load1 = 0
	self.load5 = 0
	self.load15 = 0
	self.temperature = 0
	self.ip = ''
	self.config = config
	self.battery = 0.0
	
    def updateInfoSystem(self,now):
	try:
	    info = os.popen('cat /proc/uptime','r')
	    info = info.read()
	    info = info.split(' ')
	    self.uptime = int(float(info[0]))
	    rrdtool.update(rrdDir+'systemuptime.rrd' , '%d:%d' % (now , self.uptime))
	    
	    info = os.popen('cat /sys/class/thermal/thermal_zone0/temp','r')
	    info = info.read()
	    self.temperature = float(info.split('\n')[0])/1000.0
	    rrdtool.update(rrdDir+'temperaturecpu.rrd' , '%d:%f' % (now , self.temperature))
	    
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
	    rrdtool.update(rrdDir+'memoryinfo.rrd' , '%d:%f:%f:%f' % (now , self.memTot, self.memFree, self.memAvailable))
	    
	    info = os.popen('cat /proc/loadavg')
	    info = info.read()
	    info = info.split(' ')
	    self.load1 = float(info[0])
	    self.load5 = float(info[1])
	    self.load15 = float(info[2])
	    rrdtool.update(rrdDir+'cpuload.rrd' , '%d:%f:%f:%f' % (now , self.load1, self.load5, self.load15))
	    iptmp = useful.get_ip_address('eth0')
	    if not iptmp == self.ip:
		userlist = self.config.get_user_group(self.config.AllGroups.get_group(groupWebUsers))
		for user in userlist:
		    useful.send_email(self.config.AllUsers.elements[user].fields['mail'],u'Nouvelle IP pour ELSA: '+iptmp,u'Pour acceder ELSA:\nhttp://'+iptmp+u':8080')
		self.ip = iptmp
	    
	except:
	    traceback.print_exc()
	    
    def check_rrd(self):
	now = str( int(time.time())-60)
	if os.path.exists(rrdDir+'systemuptime.rrd') is not True:
	    data_sources = 'DS:Uptime:GAUGE:120:U:U'
	    rrdtool.create( rrdDir+'systemuptime.rrd', "--step", "60", '--start', now, data_sources, 'RRA:LAST:0.5:1:43200', 'RRA:AVERAGE:0.5:5:103680', 'RRA:AVERAGE:0.5:30:86400')
	    
	if not os.path.exists(rrdDir+'temperaturecpu.rrd'):
	    data_sources = 'DS:Temperature:GAUGE:120:U:U'
	    rrdtool.create( rrdDir+'temperaturecpu.rrd', "--step", "60", '--start', now, data_sources, 'RRA:LAST:0.5:1:43200', 'RRA:AVERAGE:0.5:5:103680', 'RRA:AVERAGE:0.5:30:86400')
	    
	if not os.path.exists(rrdDir+'memoryinfo.rrd'):
	    data_sources=[ 'DS:MemTot:GAUGE:120:U:U', 'DS:MemFree:GAUGE:120:U:U', 'DS:MemAvailable:GAUGE:120:U:U' ]
	    rrdtool.create( rrdDir+'memoryinfo.rrd', "--step", "60", '--start', now, data_sources, 'RRA:LAST:0.5:1:43200', 'RRA:AVERAGE:0.5:5:103680', 'RRA:AVERAGE:0.5:30:86400')
	    
	if not os.path.exists(rrdDir+'cpuload.rrd'):
	    data_sources=[ 'DS:Load1:GAUGE:120:U:U', 'DS:Load5:GAUGE:120:U:U', 'DS:Load15:GAUGE:120:U:U' ]
	    rrdtool.create( rrdDir+'cpuload.rrd', "--step", "60", '--start', now, data_sources, 'RRA:LAST:0.5:1:43200', 'RRA:AVERAGE:0.5:5:103680', 'RRA:AVERAGE:0.5:30:86400')

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
	
    def saveGroups(self, configuration,anUser):
	print self.groups	
	allObjects = configuration.findAllFromObject(self)
	with open(configuration.csvRelations,"a") as csvfile:
	    for k,v in self.groups.items():
		tmpCode={}
		tmpCode['begin'] = unicode(datetime.datetime.now().strftime(datetimeformat))
		tmpCode['g_id'] = k
		tmpCode['idobject'] = self.fields[allObjects.keyColumn]
		tmpCode['type'] = self.get_type()
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
            return directory + '/c/container_'+self.fields['c_id']+'.' 
	elif self.__class__.__name__ == u"Batch":
            return directory + '/b/batch_'+self.fields['b_id']+'.' 
        else:
            return None

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
	    		
    def deleteGroup(self,groupid, configuration,anUser):
	print self.groups
	print groupid	
	self.write_group(groupid, configuration, anUser, 1)
	del self.groups[groupid]
	print self.groups
	
    def add_group(self, groupid, configuration, anUser):
	tmp = configuration.get_parents_list(configuration.AllGroups.elements[groupid])
	for k in tmp :
	    if k in self.groups.keys():
		return None
	tmp = configuration.get_children_list(configuration.AllGroups.elements[groupid])
	for k in tmp :
	    if k in self.groups.keys():
		return None
	self.groups[groupid] = configuration.AllGroups.elements[groupid]
	self.write_group(groupid, configuration, anUser, 0)
		
    def add_data(self,manualdata):
	if not manualdata.getID() in self.data:
	    self.data.append(manualdata.getID())
    
    def removekey(self, key):
	del self.groups[key]
	
    def containsGroup(self, oGroup):
	if len(self.groups) >0:
	    for k,v in self.groups.items():
		if v.containsGroup(oGroup):
		    return True
	return False
	
    def write_group(self, groupid, configuration, user, deny):
	allObjects = configuration.findAllFromObject(self)
	with open(configuration.csvRelations,"a") as csvfile:
	    tmpCode={}
	    tmpCode['begin'] = unicode(datetime.datetime.now().strftime(datetimeformat))
	    tmpCode['g_id'] = groupid
	    tmpCode['idobject'] = self.fields[allObjects.keyColumn]
	    tmpCode['type'] = self.get_type()
	    tmpCode["user"] = user.fields['u_id']
	    tmpCode['deny'] = deny
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
	    
	try : 
	    if 'formula' in data  and len(data['formula']) >0:
		print data
		value = 1
		owData = unicode(eval(data['formula']))
		value = 0
		owData = unicode(eval(data['formula']))
	except:
	    tmp += configuration.AllMessages.elements['formularules'].getName(lang) + '\n'
	    
	if tmp == '':
	    return True
	return tmp
	
    def delete(self, configuration):
	allObjects = configuration.findAllFromObject(self)
	allObjects.delete(self.id)
	
    def set_deny(self, deny):
	if 'deny' in self.fields :
	    self.fields['deny'] = deny
	    
    def add_position(self, transfer):
	self.position.append(transfer)
	
    def get_actual_position(self):
	if len(self.position) > 0:
	    return self.position[-1]
	return None
	
    def is_actual_position(self, type, id):
	tmp = self.get_actual_position()
	if tmp is not None :
	    if type == tmp.fields['cont_type'] and str(id) == tmp.fields['cont_id']:
		return True
	return False
	
    def get_name_listing(self):
	return 'index'

    def get_acronym(self):
        return self.fields['acronym']
	

class UpdateThread(threading.Thread):

    def __init__(self,config):
        threading.Thread.__init__(self)
        self.config = config

    def run(self):
	time.sleep(60)
	self.config.owproxy = pyownet.protocol.proxy(host="localhost", port=4304)
	while self.config.isThreading is True:
	    #ow.init("/dev/i2c-1")
	    now = useful.get_timestamp()
	    self.config.InfoSystem.updateInfoSystem(now)
	    if not len(self.config.AllSensors.elements) == 0 :
		self.config.AllSensors.update(now)
	    #ow.finish()
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
		    elif line != None:
			if data == ']' :
			    if len(line) == 10:
                                now = useful.get_timestamp()
				RSS = int(line[0]+line[1],16)
				HEX = line[2]+line[3]+line[4]
				ADDRESS = int(HEX,16)
				VAL = int(line[5]+line[6]+line[7],16)
				READER = int(line[8]+line[9],16)
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
		    currObject.creator = row['user']
		self.elements[key] = currObject
		if currObject.get_type() == 't':
		    objects = self.config.findAllFromType(currObject.fields['object_type'])
		    objects.elements[currObject.fields['object_id']].add_position(currObject)
		elif currObject.get_type() == 'd':
		    objects = self.config.findAllFromType(currObject.fields['object_type'])
		    objects.elements[currObject.fields['object_id']].add_data(currObject)
		    
		
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
	if iditem == 'new':
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
	if self.filename is not None :
	    with open(self.filename,'w') as csvfile:
		csvfile.write(self.fieldtranslate[0])
		tmp = 1
		while tmp < len(self.fieldtranslate):
		    csvfile.write('\t'+self.fieldtranslate[tmp])
		    tmp = tmp + 1
		    
    def get_name_object(self ):
	return 'component'
	        
class AllUsers(AllObjects):

    def __init__(self, config):
	AllObjects.__init__(self)
        self.elements = {}
        self.config = config
        self.fileobject = csvDir + "U.csv"
	self.filename = csvDir + "Unames.csv"
        self.keyColumn = "u_id"
	self.fieldnames = ['begin', 'u_id', 'deny', 'acronym', 'remark', 'registration', 'phone','mail', 'password', 'language', 'user']
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
		

class AllRoles(AllObjects):

    def __init__(self, config):
        self.elements = {}
        self.config = config
        self.filename = csvDir + "O.csv"
        self.keyColumn = "o_id"

    def load(self):
        with open(self.filename) as csvfile:
            reader = unicodecsv.DictReader(csvfile, delimiter = "\t")
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
            reader = unicodecsv.DictReader(csvfile, delimiter = "\t")
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
	
    def get_name_object(self ):
	return 'equipment'

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
	
    def get_name_object(self ):
	return 'container'

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
	
    def get_name_object(self):
	return 'place'
	
class AllAlarmLogs(AllObjects):

    def __init__(self, config):
	AllObjects.__init__(self)
        self.elements = {}
        self.config = config
        self.fileobject = csvDir + "alarmlogs.csv"
	self.filename = None
        self.keyColumn = "al_id"
	self.fieldnames = ['begin', 'al_id', 'cont_id', 'cont_type', 'cpehm_id','value','typealarm','begintime', 'alarmtime', 'degree']
	self.fieldtranslate = None
	self.count = 0

    def newObject(self):
	return AlarmLog()
	
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
	self.fieldnames = ['begin', 'a_id', 'deny', 'acronym', 'o_sms1', 'o_sms2', 'o_email1', 'o_email2', 'o_sound1', 'o_sound2', 'relay1', 'relay2', 'remark', 'user']
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
	self.fieldnames = ['begin', 'd_id', 'object_id', 'object_type', 'time', 'remark', 'm_id', 'value', 'user']
	self.fieldtranslate = None

    def newObject(self):
	return ManualData()
	
    def get_name_object(self ):
	return 'd'
    
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
	
    def get_name_object(self ):
	return 'group'
	
    def get_children(self,group, listchildren = None):
	if listchildren == None :
	    listchildren = []
	for k, g in self.elements.items():
	    if group.fields['g_id'] in g.groups:
		listchildren.append(k)
		self.get_children(g,listchildren)
	return listchildren
	
    def get_parents(self, group, listparents = None):
	if listparents == None :
	    listparents = []
	for k, v in group.groups.items():
	    listparents.append(k)
	    self.get_parents(v,listparents)
	return listparents
	
    def get_group(self, acro):
	for k,g in self.elements.items():
	    if g.fields['acronym'] == groupWebUsers:
		return k
	

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
	
    def get_name_object(self ):
	return 'measure'

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
	    if sensor.fields['channel'] == 'wire' and not sensor.fields['deny'] == '0' :
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
	self.fieldnames = ["begin", "b_id", "deny", "acronym", "remark", "user"]
	self.fieldtranslate = ['begin', 'lang', 'b_id', 'name', 'user']

    def newObject(self):
        return Batch(self.config)
	
    def get_name_object(self ):
	return 'batch'
	
class AllTransfers(AllObjects):

    def __init__(self, config):
	AllObjects.__init__(self)
        self.elements = {}
        self.config = config
        self.fileobject = csvDir + "T.csv"
	self.filename = None
        self.keyColumn = "t_id"
	self.fieldnames = ["begin","t_id",'time', "cont_id", "cont_type", "object_id", "object_type", "remark", "user"]
	self.fieldtranslate = None

    def newObject(self):
        return Transfer(self.config)
	
    def get_name_object(self ):
	return 'transfer'
	

class AllBarcodes(AllObjects):

    def __init__(self, config):
        AllObjects.__init__(self)
        self.elements = {}
        self.config = config
        self.fileobject = csvDir + "codes.csv"
	self.filename = None
        self.keyColumn = "code"
	self.fieldnames = ['begin', 'type', 'idobject', 'code', 'deny', 'user']
	self.fieldtranslate = None
	self.count = 0
	self.EAN = barcode.get_barcode_class('ean13')
	
    def load(self):
	with open(self.fileobject) as csvfile:
            reader = unicodecsv.DictReader(csvfile, delimiter = "\t")
            for row in reader:
		key = row[self.keyColumn]
		if row['deny'] == '0' :
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
	
    def write_csv(self, code, deny, user):
	with open(self.fileobject,"a") as csvfile:
	    tmpCode=self.create_fields(code, deny, user)
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
	
    def create_fields(self, code,deny, user, item = None):
	fields = {}
	fields['begin'] = unicode(datetime.datetime.now().strftime(datetimeformat))
	if item is None :
	    fields['type'] = self.elements[code].element.get_type()
	    fields['idobject'] = self.elements[code].element.id
	else :
	    fields['type'] = item.get_type()
	    fields['idobject'] = item.id
	fields['code'] = code
	fields['deny'] = deny
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
    
	    

class AllPhases(AllObjects):

    def __init__(self, config):
        self.elements = {}
        self.config = config
        self.filename = csvDir + "testH.csv"
        self.keyColumn = "h_id"
	self.fieldnames = ['begin', 'p_id', 'deny', 'acronym', 'remark','colorgraph', 'user']

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
            reader = unicodecsv.DictReader(csvfile, delimiter = "\t")
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
            reader = unicodecsv.DictReader(csvfile, delimiter = "\t")
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
            reader = unicodecsv.DictReader(csvfile, delimiter = "\t")
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
            reader = unicodecsv.DictReader(csvfile, delimiter = "\t")
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
        self.roles = sets.Set()
        self.context = Context()

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

class Container(ConfigurationObject):

    def __init__(self):
	ConfigurationObject.__init__(self)

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
	print data
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
		tmp += configuration.AllMessages.elements['floatrules'].getName(lang) + '\n'
	try:
	    type = data['component'].split('_')[0]
	    id = data['component'].split('_')[1]
	    if not configuration.is_component(type):
		tmp += configuration.AllMessages.elements['componentrules'].getName(lang) + '\n'
	except:
	    tmp += configuration.AllMessages.elements['componentrules'].getName(lang) + '\n'
		    
	if tmp == '':
	    return True
	return tmp
	
    def get_name(self):
	return 'manueldata'
	
class Group(ConfigurationObject):

    def __init__(self):
	ConfigurationObject.__init__(self)
	self.classes = {}
	self.groups = {}

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
	    
    def get_name_listing(self):
	return 'groups'
		
    def get_name(self):
	return 'group'

class Piece(ConfigurationObject):

    def __init__(self):
	ConfigurationObject.__init__(self)
	

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
		if transfer.fields['cont_type'] == 'e'and  transfer.fields['cont_id'] == self.id:
		    checklist.append(['e',k])
	for k, sensor in config.AllSensors.elements.items():
	    for comp,id in checklist:
		if sensor.is_in_component(comp,id):
		    listSensor.append(k)
	return listSensor
	
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
	
    def get_alarm_message(self, sensor,config, lang):
	if sensor.get_type() == 'cpehm' :
	    mess = config.AllMessages.elements['alarmmessage'].getName(lang)
	    cpe = ''
	    elem = ''
	    currObject = c.getObject('new','al')
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
	    currObject.fields['cpehm_id'] = sensor.getID()
	    currObject.fields['value'] = unicode(sensor.lastvalue)
	    currObject.fields['typealarm'] = sensor.actualAlarm
	    currObject.fields['begintime'] = sensor.time
	    currObject.fields['alarmtime'] = int(sensor.time) * sensor.countActual
	    currObject.fields['degree'] = sensor.degreeAlarm
	    currObject.save(config)
	    return unicode.format(mess,u'Akuino 6001', cpe, elem.getName(lang), elem.fields['acronym'], sensor.getName(lang), sensor.fields['acronym'], unicode(sensor.lastvalue), sensor.actualAlarm, useful.timestamp_to_date(sensor.time, datetimeformat), unicode(sensor.degreeAlarm))
	else :
	    return unicode('Il manque le message')
       
	
    def get_alarm_title(self, sensor, config, lang):
	if sensor.get_type() == 'cpehm' :
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
	else:
	    return unicode('il manque un titre')
	
    def launch_alarm(self, sensor, config):
	if sensor.get_type() == 'cpehm' :
	    level = sensor.degreeAlarm
	    if level == 1 :
		print 'Send mails'
		userlist = config.get_user_group(self.fields['o_email1'])
		for user in userlist:
		    lang = config.AllUsers.elements[user].fields['language']
		    mess = self.get_alarm_message(sensor,config, lang)
		    title = self.get_alarm_title( sensor, config, lang)
		    useful.send_email(config.AllUsers.elements[user].fields['mail'], title, mess)
	    elif level == 2:
		print 'Send mails'
		userlist = config.get_user_group(self.fields['o_email2'])
		for user in userlist:
		    lang = config.AllUsers.elements[user].fields['language']
		    mess = self.get_alarm_message(sensor,config, lang)
		    title = self.get_alarm_title( sensor, config, lang)
		    useful.send_email(config.AllUsers.elements[user].fields['mail'], title, mess)
	else :
	    userlist = config.get_user_group(self.fields['o_email2'])
	    for user in userlist:
		lang = config.AllUsers.elements[user].fields['language']
		mess = self.get_alarm_message(sensor,config, lang)
		title = self.get_alarm_title( sensor, config, lang)
		print 'Send mail depuis manuel data'
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
        string = self.id + " " + self.fields['name']
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
            self.fields['minmin'] = -99999
        if self.fields['min'] == '' :
            self.fields['min'] = -99999
        if self.fields['max'] == '' :
            self.fields['max'] = 99999
        if self.fields['maxmax'] == '' :
            self.fields['maxmax'] = 99999
	if self.fields['lapse1'] =='':
	    self.fields['lapse1'] = 99999
	if self.fields['lapse2'] =='':
	    self.fields['lapse2'] = 99999
	if self.fields['lapse3'] =='':
	    self.fields['lapse3'] = 99999
	
    def get_type(self):
	return 'cpehm'
	
    def get_name(self):
	return 'sensor'
	
    def getRRDName(self):
	name = 'cpehm_' + unicode(self.id)
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
            hours = (int(minutes / 60) % 24)+100
            minutes = (minutes % 60)+100
            strnow = unicode(hours)[1:3]+":"+unicode(minutes)[1:3]
            pos = config.screen.show(0,strnow)
            pos = config.screen.showBW(pos+2,self.get_acronym())
            pos = config.screen.show(pos+2,unicode(round(float(value),1)))
            if self.fields['m_id']:
                id_measure = unicode(self.fields['m_id'])
                if id_measure in config.AllMeasures.elements:
                    measure = config.AllMeasures.elements[id_measure]
                    pos = config.screen.show(pos,measure.fields['unit'])
                
	    typeAlarm,symbAlarm = self.getTypeAlarm(value)
            print (u'Sensor update Channel : '+ self.fields['channel'] + u'    ' + self.fields['sensor'] + u' ==> ' + self.fields['acronym'] + u' = ' + unicode(value))
	    if typeAlarm == 'typical' :
		self.setTypicalAlarm()
	    else:
		if not (( typeAlarm == 'min' and self.actualAlarm == 'minmin' ) or ( typeAlarm == 'max' and self.actualAlarm == 'maxmax')) :
		    self.actualAlarm = typeAlarm
                config.screen.show(pos+2,symbAlarm)
		self.launchAlarm(config, now)
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
	if self.fields['channel'] == 'wire' :
	    data_sources = str('DS:'+name+'1:GAUGE:120:U:U')
	    rrdtool.create( str(rrdDir+self.getRRDName()), "--step", "60", '--start', now, data_sources, 'RRA:LAST:0.5:1:43200', 'RRA:AVERAGE:0.5:5:103680', 'RRA:AVERAGE:0.5:30:86400')
	elif self.fields['channel'] == 'radio' :
	    data_sources = str('DS:'+name+'1:GAUGE:360:U:U')
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
	return False
	
    def get_sensors_in_component(self, config):
	tmp = []
	tmp.append(self.id)
	return tmp
	    
	    
class Batch(ConfigurationObject):

    def __init__(self, config):
	ConfigurationObject.__init__(self)
	self.config = config
            

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
	    if objet.is_actual_position(postype, posid) is True :
		tmp += configuration.AllMessages.elements['transferrules'].getName(lang) + '\n'
	else :
	    tmp += configuration.AllMessages.elements['transferrules'].getName(lang) + '\n'
	if tmp == '':
	    return True
	return tmp
	
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
        string = unicode(self.rank)+"#"+unicode(self.id) + "=" + self.fields['name']
        return string

    def __str__(self):
        string = "\nScanner "+unicode(self.rank)+"#"+unicode(self.id)
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
            piece = unicode(self.piece)
        else:
            piece = ""
        if self.equipment != "":
            equipment = unicode(self.equipment)
        else:
            equipment = ""
        if self.phase != "":
            phase = unicode(self.phase)
        else:
            phase = ""
        if self.measure != "":
            measure = unicode(self.measure)
        else:
            measure = ""
        if self.batch != "":
            batch = unicode(self.batch)
        else:
            batch = ""
        string = string + piece + equipment + phase + measure + batch
        return string
