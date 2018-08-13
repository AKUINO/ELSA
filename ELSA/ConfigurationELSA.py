#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sets
import time
import datetime
import traceback
import unicodecsv
import sys
import threading
import os
import os.path
import cgi
import rrdtool
import pyownet
import serial
import myuseful as useful
import HardConfig as hardconfig
import re
import socket
import urllib2
import collections
import math
import shutil
import abe_adcpi
import abe_mcp3424
import abe_mcp3423
import abe_iopi
import serial
import numbers
import abe_expanderpi
import barcode
"""
import SSD1306
from I2CScreen import *
import pigpio
PIG = pigpio.pi()
"""
# if a JSON decoder is needed to read a sensor...
import json

# import smbus

# mise a jour git
DIR_TTY = '/dev/ttyS0'
dir_hardconfig = os.path.normpath('~/akuino/hardware')

DIR_BASE = os.path.dirname(os.path.abspath(__file__)) + '/'
DIR_USER_DATA = os.path.join(DIR_BASE, '../data/')
DIR_APP_CSV = os.path.join(DIR_BASE, 'csv/')
DIR_DEFAULT_CSV = os.path.join(DIR_APP_CSV, 'default/')
# Defines default values for some .csv files
# (ex: default user for a new installation)
DIR_STATIC = os.path.join(DIR_BASE, 'static/')
URL_STATIC = u'/static/'

DIR_DATA_CSV = os.path.join(DIR_USER_DATA, 'csv/')
DIR_RRD = os.path.join(DIR_USER_DATA, 'rrd/')
DIR_DOC = os.path.join(DIR_USER_DATA, 'doc/')

URL_DOC = u'/doc/'
DIR_WEB_TEMP = os.path.join(DIR_STATIC, 'temp/')

TEMPLATES_DIR = os.path.join(DIR_BASE, 'templates/')

GROUPWEBUSERS = '_WEB'
KEY_ADMIN = "admin" #Omnipotent user


imagedTypes = [u'u', u'e', u'p', u'g', u'gf', u'gr', u'gu', u'c', u'b', u'h', u's', u'm', u'a']

alarm_fields_for_groups = ['o_sms1', 'o_sms2', 'o_email1', 'o_email2', 'o_sound1', 'o_sound2']


_lock_socket = None

color_violet = "FF00FF"
color_blue = "0000FF"
color_green = "00FF00"
color_orange = "FFFF00"
color_red = "FF0000"
color_grey = "808080"
color_black = "000000"
color_white = "FFFFFF"

def copy_default_csv(filename):
    '''
    Will copy the default .csv to `filename` and return true if a default
    exists, otherwise does nothing and returns false
    '''
    default_csv_file = os.path.join(DIR_DEFAULT_CSV, os.path.basename(filename))
    if os.path.exists(default_csv_file):
        shutil.copyfile(default_csv_file, filename)
        return True
    else:
        return False

# ensure comma to separate integer from decimals
def export_float(value):
    if not value:
        return ""
    else:
        return unicode(value).replace('.',',',1)

class valueCategory(object):

    def __init__(self, level, name, acronym, color,text_color):
        self.level = level
        self.name = name
        self.acronym = acronym
        self.color = color
        self.text_color = text_color

    # triple returns 4 values for a given category !
    def triple(self):
        return self.name, self.acronym, self.color, self.text_color


valueCategs = {-2: valueCategory(-2, 'minmin', '---', color_violet,color_black), -1: valueCategory(-1, 'min', '--', color_blue,color_white), 0: valueCategory(
    0, 'typical', '==', color_green,color_black), 1: valueCategory(1, 'max', '++', color_orange,color_black), 2: valueCategory(2, 'maxmax', '++', color_red,color_white), 3: valueCategory(3, 'none', '??', color_grey,color_white)}


class Configuration():

    def __init__(self, config_file):
        if config_file is not None:
            self.HardConfig = hardconfig.HardConfig(config_file)
        else:
            self.HardConfig = hardconfig.HardConfig(None)

# Run only ONCE: Check if /run/akuino/ELSA.pid exists...
# pid = str(os.getpid())
# self.pidfile = self.HardConfig.RUNdirectory+"/ELSA.pid"
##
# if os.path.isfile(self.pidfile):
# print "%s already exists, exiting" % self.pidfile
# sys.exit()
# file(self.pidfile, 'w').write(pid)

        # Without holding a reference to our socket somewhere it gets garbage
        # collected when the function exits
        global _lock_socket

        _lock_socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)

        try:
            _lock_socket.bind('\0AKUINO-ELSA')
            print ('Socket AKUINO-ELSA now locked')
        except socket.error:
            print ('AKUINO-ELSA lock exists')
            sys.exit()

        if not os.path.samefile(os.getcwd(), DIR_BASE) :
            os.chdir(DIR_BASE)

        # Currency to be retrieved where ?
        self.currency = '€'
        self.valueCategs = valueCategs
        self.sortedCategs = sorted(valueCategs)
        self.file_of_codes = os.path.join(DIR_DATA_CSV, 'codes.csv')
        self.file_of_relations = os.path.join(DIR_DATA_CSV, 'relations.csv')
        self.fieldcode = ['begin', 'type', 'idobject', 'code', 'user']
        self.registry = {}
        self.AllUsers = AllUsers(self)
        self.AllLanguages = AllLanguages(self)
        self.AllPlaces = AllPlaces(self)
        self.AllContainers = AllContainers(self)
        self.AllMessages = AllMessages(self)
        self.AllEquipments = AllEquipments(self)
        self.AllMeasures = AllMeasures(self)
        self.AllBatches = AllBatches(self)
        self.AllSensors = AllSensors(self)
        self.AllGrFunction = AllGrFunction(self)
        self.AllGrUsage = AllGrUsage(self)
        self.AllGrRecipe = AllGrRecipe(self)
        self.AllCheckPoints = AllCheckPoints(self)
        self.AllAlarms = AllAlarms(self)
        self.AllAlarmLogs = AllAlarmLogs(self)
        self.AllHalflings = AllHalflings(self)
        self.AllBarcodes = AllBarcodes(self)
        self.AllManualData = AllManualData(self)
        self.AllTransfers = AllTransfers(self)
        self.AllPourings = AllPourings(self)
        self.AllTransferModels = AllTransferModels(self)
        self.AllManualDataModels = AllManualDataModels(self)
        self.AllPouringModels = AllPouringModels(self)
        self.connectedUsers = AllConnectedUsers()
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
            self.screen = I2CScreen(True,
            disp = SSD1306.SSD1305_132_64 (rst=self.HardConfig.oled_reset,
                                           gpio=PIG))
            self.screen.clear()
        else:
            self.screen = I2CScreen(False, disp = None)	
        """
        self.AllLanguages.load()
        self.AllUsers.load()
        self.AllPlaces.load()
        self.AllEquipments.load()
        self.AllContainers.load()
        self.AllMessages.load()
        self.AllMeasures.load()
        self.AllSensors.load()
        self.AllSensors.check_rrd()
        self.AllSensors.correctValueAlarm()
        self.AllAlarms.load()
        self.AllHalflings.load()
        # doit toujours être appelé à la fin
        self.AllGrFunction.load()
        self.AllGrUsage.load()
        self.AllGrRecipe.load()
        self.AllBatches.load()   # must be just before loading checkpoints
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

    def findAll(self, identifier):
        if identifier in self.registry:
            return self.registry[identifier]
        return None

    def findAllFromObject(self, anObject):
        return self.findAll(anObject.__class__.__name__)

    def get_object(self, type, id):
        objects = self.findAll(type)
        if objects:
            return objects.get(id)
        return None

    def getObject(self, idObject, className):
        allObjects = self.findAll(className)
        if allObjects is not None:
            return allObjects.getItem(idObject)
        return None

    def getFieldsname(self, className):
        allObjects = self.findAll(className)
        if allObjects is not None:
            return allObjects.fieldnames
        return None

    def getKeyColumn(self, anObject):
        obj = self.findAllFromObject(anObject)
        return obj.keyColumn

    def getMessage(self,message_acronym,lang):
        return self.AllMessages.elements[message_acronym].getName(lang)

    def getName(self, allObjects,lang):
        return self.getMessage(allObjects.get_class_acronym(),lang)

    def getHalfling(self, acronym, supp_classes=""):
        return self.AllHalflings.getHalfling(acronym, supp_classes)

    def getAllHalfling(self, allObjects, supp_classes=""):
        return self.AllHalflings.getHalfling(allObjects.get_class_acronym(), supp_classes)

    def get_time(self):
        return useful.get_time()

    def is_component(self, type):
        if type == 'c' or type == 'p' or type == 'e' or type == 'b':
            return True
        return False

    def get_time_format(self):
        return useful.datetimeformat

    def triple(self,key):
        for k,v in valueCategs.items():
            if v.name == key or v.acronym == key:
                return v.triple()
        return None

class ConfigurationObject(object):

    def __init__(self):
        self.fields = {}
        self.names = {}
        self.groups = {}
        self.id = None
        self.created = None
        self.creator = None
        self.transfers = []
        self.manualdata = []

    def __repr__(self):
        return self.get_type()+'_'+self.id+(' '+self.fields['acronym']) if 'acronym' in self.fields else ''

    def floats(self, field):
        v = self.fields[field]
        if v:
            try:
                return float(v)
            except:
                return 0.0
        else:
            return 0.0

    def save(self, configuration, anUser=""):
        self.fields["begin"] = useful.now()
        if anUser != "":
            self.fields["user"] = anUser.fields['u_id']
        allObjects = configuration.findAllFromObject(self)
        with open(allObjects.file_of_objects, "a") as csvfile:
            writer = unicodecsv.DictWriter(csvfile,
                                           delimiter='\t',
                                           fieldnames=allObjects.fieldnames,
                                           encoding="utf-8")
            writer.writerow(self.fields)
        self.saveName(configuration, anUser)
        return self

    def saveName(self, configuration, anUser):
        allObjects = configuration.findAllFromObject(self)
        for key in self.names:
            with open(allObjects.file_of_names, "a") as csvfile:
                writer = unicodecsv.DictWriter(csvfile,
                                               delimiter='\t',
                                               fieldnames=allObjects.fieldtranslate,
                                               encoding="utf-8")
                writer.writerow(self.names[key])

##    def saveCode(self, configuration, barcode, anUser):
##        allObjects = configuration.findAllFromObject(self)
##        with open(configuration.file_of_codes, "a") as csvfile:
##            tmpCode = {}
##            tmpCode['begin'] = useful.now()
##            tmpCode['type'] = self.get_type()
##            tmpCode['idobject'] = self.fields[allObjects.keyColumn]
##            tmpCode['code'] = unicode(barcode)
##            tmpCode["user"] = anUser.fields['u_id']
##            writer = unicodecsv.DictWriter(csvfile,
##                                           delimiter='\t',
##                                           fieldnames=configuration.fieldcode,
##                                           encoding="utf-8")
##            writer.writerow(tmpCode)

    def initialise(self, fieldsname):
        for field in fieldsname:
            self.fields[field] = ''

    def getImagePath(self, ensure=False, ext="jpg"):
        thisType = self.get_type()
        if thisType in imagedTypes:
            directory = os.path.join(DIR_DOC,thisType)
            if ensure:
                if not os.path.exists(directory):
                    try:
                        os.makedirs(directory)
                    except OSError as e:
                        if e.errno != errno.EEXIST:
                            traceback.print_exc()
                            return None
            return os.path.join(directory,thisType + u'_'+unicode(self.id) + u'.' +ext)
        return None

    def getImageURL(self, ext="jpg"):
        thisType = self.get_type()
        if thisType in imagedTypes:
            return URL_DOC +thisType+u'/'+thisType+ u'_'+unicode(self.id) + u'.' +ext
        return ""

    def getDocumentDir(self, ensure=False):
        thisType = self.get_type()
        if thisType in imagedTypes:
            directory = os.path.join(DIR_DOC,
                                thisType,
                                thisType + u'_'+unicode(self.id))
            if ensure:
                if not os.path.exists(directory):
                    try:
                        os.makedirs(directory)
                    except OSError as e:
                        if e.errno != errno.EEXIST:
                            traceback.print_exc()
                            return None
            return directory
        return None

    def getDocumentList(self):
        thisType = self.get_type()
        if thisType in imagedTypes:
            directory = os.path.join(DIR_DOC,
                                thisType,
                                thisType + u'_'+unicode(self.id))
            if not os.path.exists(directory):
                return []
            return os.listdir(directory)
        return []

    def getDocumentURL(self,filename=u''):
        thisType = self.get_type()
        if thisType in imagedTypes:
            return URL_DOC +thisType+u'/'+thisType+ u'_'+unicode(self.id) + u'/'+filename
        return ""

    def isImaged(self):
        fileName = self.getImagePath(False,u"png")
        if fileName is None:
            return None
        elif os.path.isfile(fileName):
            return u"png"
        else:
            fileName = self.getImagePath(False,u"jpg")
            if os.path.isfile(fileName):
                return u"jpg"
            else:
                return None
                

    def setName(self, key, value, user, keyColumn):
        if value != '' and value is not None:
            newName = {}
            newName["begin"] = useful.now()
            newName['user'] = user.fields['u_id']
            newName['lang'] = key
            newName['name'] = value
            newName[keyColumn] = self.fields[keyColumn]
            self.names[key] = newName

    def getName(self, lang):
        if not lang:
	    lang = 'EN'
        else:
            lang = lang.upper()
        if lang == 'DISCONNECTED':
            lang = 'EN'
        if lang in self.names:
            return self.names[lang]['name']
        elif 'EN' in self.names:
            return self.names['EN']['name']
        elif 'FR' in self.names:
            return self.names['FR']['name']
        elif 'DE' in self.names:
            return self.names['DE']['name']
        elif len(self.names) > 0:
            return self.names.values()[0]['name']
        elif 'default' in self.fields:
            return self.fields['default']
        elif 'acronym' in self.fields:
            return self.fields['acronym']
        else:
            return "Record "+unicode(self.id)+": no name"

    def getNameHTML(self, lang):
	return cgi.escape(self.getName(lang),True).replace("'","&#39;");

    def get_real_name(self, lang):
        if lang in self.names:
            return self.names[lang]['name']
        return ''

    def getID(self):
        return self.id

    def getTimestamp(self):
        # time = editable time fields
        if 'time' in self.fields:
            stamp = self.fields['time']
        else: # begin = record creation
            stamp = self.fields['begin']
        if not stamp:
            return 0
        else:
            return useful.date_to_timestamp(stamp)

    def get_hash_type(self):
        obj_type = self.get_type()
        hash = 10 * (ord(obj_type[0]) - ord('a'))
        if len(obj_type) > 1:
            hash += ((ord(obj_type[1]) - ord('a'))+1) % 10
        return hash

    def write_group(self, groupid, configuration, user, active):
        allObjects = configuration.findAllFromObject(self)
        with open(configuration.file_of_relations, "a") as csvfile:
            tmpCode = {}
            tmpCode['begin'] = useful.now()
            tmpCode['g_id'] = groupid
            tmpCode['idobject'] = self.fields[allObjects.keyColumn]
            tmpCode['type'] = self.get_type()
            tmpCode["user"] = user.fields['u_id']
            tmpCode['active'] = active
            writer = unicodecsv.DictWriter(csvfile,
                                           delimiter='\t',
                                           fieldnames=configuration.fieldrelations,
                                           encoding="utf-8")
            writer.writerow(tmpCode)

    def validate_form(self, data, configuration, lang):
        tmp = ''
        if 'acronym' not in data:
            tmp = configuration.getMessage('acronymrequired',lang) + '\n'
        try:
            cond = data['acronym'] == re.sub('[^\w]+', '', data['acronym'])
            if not cond:
                tmp += configuration.getMessage('acronymrules',lang) + '\n'
        except:
            tmp += configuration.getMessage('acronymrules',lang) + '\n'

        allObjects = configuration.findAllFromObject(self)
        if not allObjects.unique_acronym(data['acronym'], self.id):
            tmp += configuration.getMessage('acronymunique',lang) + '\n'
        else:
            try:
                if 'code' in data and len(data['code']) > 0:
                    some_code = int(data['code'])
                    if not configuration.AllBarcodes.validate_barcode(
                        some_code, self.id, self.get_type()) :
                        tmp += configuration.getMessage('barcoderules',lang) + '\n'
            except:
                tmp += configuration.getMessage('barcoderules',lang) + '\n'
        if tmp == '':
            return True
        return tmp

    def set_value_from_data(self, data, c, user):
        self.fields['acronym'] = data['acronym']

        for key in c.AllLanguages.elements:
            if key in data:
                self.setName(key, data[key], user, c.getKeyColumn(self))

        if 'active'in data:
            self.set_active('1')
        else:
            self.set_active('0')

        if 'placeImg' in data and data['placeImg'] != {}:
            if data.placeImg.filename != '':
                filepath = data.placeImg.filename.replace('\\', '/')
                ext = ((filepath.split('/')[-1]).split('.')[-1])
                if ext and ext.lower() in [u'jpg',u'jpeg',u'png']:
                    with open(self.getImagePath(True,ext=("png" if ext.lower() == u"png" else u"jpg")), 'w') as fout:
                        fout.write(data.placeImg.file.read())
        # linkedDocs is treated by caller because "web" object is needed...
                        
        if 'code' in data:
            lenCode = len(data['code'])
            if lenCode < 14 and lenCode > 11:
                some_code = int(data['code'])
                c.AllBarcodes.add_barcode(self, some_code, user)
            elif lenCode == 0:
                # Defaut barcode: 99hhT1234567x
                some_code = 990000000000 + (self.get_hash_type()*10000000)+int(self.id)
                ean = c.AllBarcodes.EAN(unicode(some_code))
                c.AllBarcodes.add_barcode(self, ean.get_fullcode(), user)

        self.fields['remark'] = data['remark']

        if self.creator is None:
            self.creator = user.fields['u_id']
            self.created = self.fields['begin']

    def get_events(self,c):
        events = []
        if self.manualdata:
            for kevent in self.manualdata:
                if kevent in c.AllManualData.elements:
                    events.append(c.AllManualData.elements[kevent])
        if self.transfers:
            for kevent in self.transfers:
                if kevent in c.AllTransfers.elements:
                    events.append(c.AllTransfers.elements[kevent])
        if self.source:
            for kevent in self.source:
                if kevent in c.AllPourings.elements:
                    events.append(c.AllPourings.elements[kevent])
        if self.destination:
            for kevent in self.destination:
                if kevent in c.AllPourings.elements:
                    events.append(c.AllPourings.elements[kevent])
        return sorted(events, key=lambda t: t.fields['time'])

    def add_data(self, manualdata):
        self.remove_data(manualdata)
        if len(self.manualdata) == 0:
            self.manualdata.append(manualdata.getID())
        else:
            time = manualdata.getTimestamp()
            insert = False
            for i in range(len(self.manualdata)):
                tmp = self.config.AllManualData.elements[self.manualdata[i]]
                tmptime = tmp.getTimestamp()
                if time < tmptime:
                    insert = True
                    self.manualdata.insert(i, manualdata.getID())
                    break
            if insert is False:
                self.manualdata.append(manualdata.getID())

    def remove_data(self, manualdata):
        if manualdata.getID() in self.manualdata:
            self.manualdata.remove(manualdata.getID())

    def get_transfers_in_time_interval(self, begin, end):
        tmp = []
        first = True
        count = 0
        while count < len(self.transfers):
            t = self.config.AllTransfers.elements[self.transfers[count]]
            time = t.getTimestamp()
            if begin < time and time < end:
                if first is True:
                    first = False
                    if count > 0:
                        if self.config.AllTransfers.elements[self.transfers[count-1]].getTimestamp() > begin:
                            tmp.append(self.transfers[count - 1])
                tmp.append(t)
            elif time <= begin and (first is True
                    or count == len(self.transfers)-1):
                tmp.append(t)
                first = False
            count += 1
        return tmp

    def delete(self, configuration):
        allObjects = configuration.findAllFromObject(self)
        allObjects.delete(self.id)

    def set_active(self, active):
        if 'active' in self.fields:
            self.fields['active'] = active

    def add_position(self, transfer):
        self.remove_position(transfer)
        if len(self.transfers) == 0:
            self.transfers.append(transfer.getID())
        else:
            time = transfer.getTimestamp()
            insert = False
            for i in range(len(self.transfers)):
                tmp = self.config.AllTransfers.elements[self.transfers[i]]
                tmptime = tmp.getTimestamp()
                if time < tmptime:
                    insert = True
                    self.transfers.insert(i, transfer.getID())
                    break
            if insert is False:
                self.transfers.append(transfer.getID())

    def remove_position(self, transfer):
        if transfer.getID() in self.transfers:
            self.transfers.remove(transfer.getID())

    def get_last_transfer(self):
        if len(self.transfers) > 0:
            return self.transfers[-1]
        return None

    def get_actual_position_here(self,configuration):
	currObj = None
	tmp = self.get_last_transfer()
	if tmp is not None:
	    tmp = configuration.AllTransfers.elements[tmp]
            currObj = configuration.get_object (tmp.fields['cont_type'], tmp.fields['cont_id'])
        return currObj

    def get_actual_position_hierarchy(self, configuration, result=[]):
        if not (self in result):
            result.append(self)
            currObj = self.get_actual_position_here(configuration)
            if currObj:
                return currObj.get_actual_position_hierarchy(configuration, result)
        return result

    def is_actual_position(self, type, id, configuration):
        tmp = self.get_last_transfer()
        if tmp is not None:
            tmp = configuration.AllTransfers.elements[tmp]
            if type == tmp.fields['cont_type'] \
                    and unicode(id) == tmp.fields['cont_id']:
                return True
        return False

    def get_name_listing(self):
        return self.get_class_acronym()+'s'

    def get_acronym(self):
        return self.fields['acronym']

    # overriden for groups !
    def get_acronym_hierarchy(self):
        return self.fields['acronym']

    def get_batch_in_component(self, configuration):
        batches = []
        type = self.get_type()
        id = self.getID()
        for k, v in configuration.AllBatches.elements.items():
            if v.is_actual_position(type, id, configuration):
                batches.append(v)
        return batches

    def get_position_on_time(self, configuration, time):
        time = useful.date_to_timestamp(time)
        if self.transfers == []:
            return None
        count = 1
        while count < len(self.transfers):
            tmp = configuration.AllTransfers.elements[self.transfers[count]]
            tmptime = tmp.getTimestamp()
            if time < tmptime:
                return configuration.AllTransfers \
                                    .elements[self.transfers[count-1]]
        return configuration.AllTransfers.elements[self.transfers[-1]]

    def get_all_in_component(self, config, begin, end, infos=None):
        if infos is None:
            infos = {}
        sensors = self.get_sensors_in_component(config)
        tmp = self.get_transfers_in_time_interval(begin, end)
        if len(tmp) > 0:
            for t in tmp:
                infos = t.get_component(config).get_all_in_component(
                    config, begin, end, infos)
        for a in sensors:
            if a not in infos.keys():
                infos[a] = config.AllSensors.elements[a].fetch(begin, end)
        return infos

    def isActive(self):
        if not 'active' in self.fields:
            return True
        else:
            return self.fields['active'] != '0'

    def getImage(self, height=36):
        ext = self.isImaged()
        if ext:
            return "<img src=\""+self.getImageURL(ext)+"\" alt=\""+unicode(self)+"\" height="+unicode(height)+">"
        else:
            return ""

    def isModeling(self):
        return None
    
    def isExpired(self):
        return None
    
    def isAlarmed(self,c):
        if 'al_id' in self.fields:
            if self.fields['al_id']:
                if self.get_type() != 'al':
                    allog = c.AllAlarmLogs.get(self.fields['al_id'])
                    if allog and allog.isActive() and not allog.isComplete():
                        return True
            return False
        #TODO: Check this when implementing alarms for timed transfers and for incorrect pourings...
        if self.transfers:
            for k in self.transfers:
                t = c.AllTransfers.get(k)
                if t and t.isAlarmed(c):
                    return True
        if self.manualdata:
            for k in self.manualdata:
                dd = c.AllManualData.get(k)
                if dd and dd.isAlarmed(c):
                    return True
        return False
    
    def statusIcon(self, configuration, pic=None,inButton=False):
        allObjects = configuration.findAllFromObject(self)
        supp_classes = ""
        if not inButton:
            if self.isModeling():
                supp_classes = " text-info"
            elif self.isExpired():
                supp_classes = " text-danger"
        result = configuration.getAllHalfling(allObjects,supp_classes)
        if 'active' in self.fields and self.fields['active'] == '0':
            result = '<span class="icon-combine">'+result+'<span class="halflings halflings-remove text-danger"></span></span>'
        #result = '<span class="icon-combine">'+result+'<span class="halflings halflings-time text-danger"></span></span>'
        if pic:
            result += self.getImage(36)
        return result

    def getTypeAlarm(self, value, model=None):
        if (value == None) or (value==''):
            return valueCategs[3].triple()
        value = value if type(value) is float else float(value)
        bounds = model.fields if model else self.fields
        if bounds['minmin'] and value <= float(bounds['minmin']):
            return valueCategs[-2].triple()
        elif bounds['min'] and value <= float(bounds['min']):
            return valueCategs[-1].triple()
        elif bounds['maxmax'] and value >= float(bounds['maxmax']):
            return valueCategs[2].triple()
        elif bounds['max'] and value >= float(bounds['max']):
            return valueCategs[1].triple()
        else:
            return valueCategs[0].triple()

    def get_quantity(self):
        return 0.0;

    def get_measure(self,c):
	if 'm_id' in self.fields and self.fields['m_id'] and self.fields['m_id'] in c.AllMeasures.elements:
            return c.AllMeasures.elements[self.fields['m_id']]
        return None;

    def get_unit(self,c):
        aMeasure = self.get_measure(c)
        if aMeasure:
            return aMeasure.fields['unit']
        return "";
        
    def getQtyUnit(self,c):
        result = u'?'
        quantity = self.get_quantity()
        if quantity:
            result = unicode(quantity)
        unit = self.get_unit(c)
	if unit:
            result += u' '+unit
        if result == '?':
            return ''
        return result

    def updateAllowed(self,user,c):
        user_group = user.get_group()
        if user_group and user_group in c.AllGrFunction.elements:
            key_upd = u"upd_"+self.get_type()
            aGroup = c.AllGrFunction.elements[user_group]
            if aGroup.fields["acronym"].lower() == KEY_ADMIN:
                return True
            if aGroup.fields["acronym"].lower() == key_upd:
                return True
            for user_group in aGroup.get_all_parents([],c.AllGrFunction):
                bGroup = c.AllGrFunction.elements[user_group]
                if bGroup.fields["acronym"].lower() == KEY_ADMIN:
                    return True
                if bGroup.fields["acronym"].lower() == key_upd:
                    return True
        return False

class UpdateThread(threading.Thread):

    def __init__(self, config):
        threading.Thread.__init__(self)
        self.config = config
    
    def run(self):
        if self.config.HardConfig.owfs == 'yes':
                self.config.owproxy = pyownet.protocol.proxy(host="localhost",
                                                             port=4304)
        while self.config.isThreading is True:
            timer = 0
            now = useful.get_timestamp()
            if len(self.config.AllSensors.elements) > 0:
                self.config.AllSensors.update(now)
            while self.config.isThreading is True and timer < 60:
                time.sleep(1)           
                timer = timer + 1


class RadioThread(threading.Thread):

    def __init__(self, config):
        threading.Thread.__init__(self)
        self.config = config

    def run(self):
        if self.config.HardConfig.ela != 'yes':
            print "No Radio reception configured."
            return
        print "Radio at "+unicode(self.config.HardConfig.ela_bauds)+" bauds on "+DIR_TTY
        noDots = {ord(' '): None, ord('.'): None}
        try:
            elaSerial = serial.Serial(
                DIR_TTY, self.config.HardConfig.ela_bauds, timeout=0.1)
            time.sleep(0.1)
            elaSerial.write(str(self.config.HardConfig.ela_reset))
            line = None
            while self.config.isThreading is True:
                try:
                    data = elaSerial.read()
                    if data == '[':
                        line = []
                    elif line is not None:
                        if data == ']':
                            if len(line) == 10:
                                now = useful.get_timestamp()
                                RSS = int(line[0]+line[1], 16)
                                HEX = line[2]+line[3]+line[4]
                                # ADDRESS = int(HEX,16)
                                VAL = int(line[5]+line[6]+line[7], 16)
                                print ("ELA="
                                        + HEX
                                        + ", RSS="
                                        + unicode(RSS)
                                        + ", val="+unicode(VAL))
                                currSensor = None
                                value = VAL
                                for sensor in self.config.AllSensors.elements:
                                    currSensor = self.config.AllSensors.elements[sensor]
                                    if currSensor.isActive():
                                        try:
                                            if (unicode(currSensor.fields['sensor']).translate(noDots) == unicode(HEX).translate(noDots)):
                                                if not currSensor.fields['formula'] == '':
                                                    value = unicode(
                                                        eval(currSensor.fields['formula']))
                                                print(
                                                    u"Sensor ELA-" + currSensor.fields['sensor'] + u": " + currSensor.fields['acronym'] + u" = "+unicode(value))
                                                currSensor.update(now, value, self.config)
                                        except:
                                            traceback.print_exc()
                                            print "Error in formula, "+currSensor.fields['acronym']+": "+currSensor.fields['formula']
                            line = None
                        else:
                            line.append(data)
                except:
                    traceback.print_exc()
        except:
            traceback.print_exc()

class AllObjects(object):

    def __init__(self, obj_type, obj_name, config):
        self.obj_type = obj_type
        self.obj_classname = obj_name
        self.elements = {}
        self.file_of_objects = os.path.join(DIR_DATA_CSV, obj_type.upper()) + ".csv"
        self.file_of_names = os.path.join(DIR_DATA_CSV, obj_type.upper()) + "names.csv"
        self.keyColumn = obj_type + "_id"
        self.config = config
        self.count = 0
        #TODO: Strange, some classes do not list the fields they contain...
        self.fieldnames = None
        config.registry[obj_type] = self
        config.registry[obj_name] = self
        if self.get_class_acronym():
            config.registry[self.get_class_acronym()] = self

    def get_type(self):
        return self.obj_type

    def load(self):
        self.check_csv(self.file_of_objects)
        self.loadFields()
        if self.file_of_names is not None:
            self.check_csv(self.file_of_names)
            self.loadNames()

    def isModeling(self):
        return None
    
    def check_csv(self, filename):
        if not os.path.exists(filename):
            if not os.path.exists(os.path.dirname(filename)):
                os.makedirs(os.path.dirname(filename))
            if copy_default_csv(filename) == False:
                self.create_csv(filename)

    def create_csv(self, fname):
        with open(fname, 'w') as csvfile:
            csvfile.write(self.fieldnames[0])
            tmp = 1
            while tmp < len(self.fieldnames):
                csvfile.write('\t'+self.fieldnames[tmp])
                tmp = tmp + 1
            csvfile.write('\n')
        if self.file_of_names is not None:
            with open(self.file_of_names, 'w') as csvfile:
                csvfile.write(self.fieldtranslate[0])
                tmp = 1
                while tmp < len(self.fieldtranslate):
                    csvfile.write('\t'+self.fieldtranslate[tmp])
                    tmp = tmp + 1
                csvfile.write('\n')

    def loadFields(self):
        conformant = None
        conformantFile = None
        conformantWriter = None
        with open(self.file_of_objects) as csvfile:
            reader = unicodecsv.DictReader(csvfile, delimiter="\t")
            for row in reader:
                if conformant is None:
                    if self.fieldnames is None:
                        conformant = True
                    else:
                        conformant = self.fieldnames == reader.fieldnames
                        if not conformant:
                            conformantFile = open(self.file_of_objects+".NEW",'w')
                            print (self.file_of_objects+" will be made conformant")
                            conformantWriter = unicodecsv.DictWriter(conformantFile,
                                                           delimiter='\t',
                                                           fieldnames=self.fieldnames,
                                                           encoding="utf-8")
                            conformantWriter.writeheader()
                if conformantWriter is not None:
                    conformantWriter.writerow(row)
                key = row[self.keyColumn]
                currObject = self.newObject()
                currObject.fields = row
                currObject.id = key
                if key in self.elements:
                    tmp = self.elements[key]
                    currObject.created = tmp.created
                    currObject.creator = tmp.creator
                    if tmp.get_type() == 't':
                        self.config \
                            .get_object(tmp.fields['object_type'],tmp.fields['object_id']) \
                            .remove_position(tmp)
                    elif tmp.get_type() == 'd':
                        self.config \
                            .get_object(tmp.fields['object_type'],tmp.fields['object_id']) \
                            .remove_data(tmp)
                    elif tmp.get_type() == 'v':
                        objects = self.config.AllBatches
                        objects.elements[tmp.fields['src']].remove_source(tmp)
                        objects.elements[tmp.fields['dest']].remove_destination(tmp)
                    elif tmp.get_type() == 'tm':
                        self.config \
                            .AllCheckPoints.elements[tmp.fields['h_id']] \
                            .remove_tm(tmp)
                    elif tmp.get_type() == 'vm':
                        self.config \
                            .AllCheckPoints.elements[tmp.fields['h_id']] \
                            .remove_vm(tmp)
                    elif tmp.get_type() == 'dm':
                        self.config \
                            .AllCheckPoints.elements[tmp.fields['h_id']] \
                            .remove_dm(tmp)
                else:
                    currObject.created = currObject.fields['begin']
                    if 'user' in row:
                        currObject.creator = row['user']
                    else:
                        currObject.creator = None
                self.elements[key] = currObject
                if currObject.get_type() == 't':
                    if currObject.isActive():
                        self.config.get_object(currObject.fields['object_type'], \
                                currObject.fields['object_id']) \
                               .add_position(currObject)
                    else:
                        self.config.get_object(currObject.fields['object_type'], \
                                currObject.fields['object_id']) \
                               .remove_position(currObject)
                elif currObject.get_type() == 'd':
                    if currObject.isActive():
                        self.config.get_object(currObject.fields['object_type'], \
                                currObject.fields['object_id']) \
                               .add_data(currObject)
                    else:
                        self.config.get_object(currObject.fields['object_type'], \
                                currObject.fields['object_id']) \
                                .remove_data(currObject)
                elif currObject.get_type() == 'dm':
                    objects = self.config.AllCheckPoints
                    if currObject.isActive():
                        objects.elements[currObject.fields['h_id']] \
                               .add_dm(currObject)
                    else:
                        objects.elements[currObject.fields['h_id']] \
                               .remove_dm(currObject)
                elif currObject.get_type() == 'tm':
                    objects = self.config.AllCheckPoints
                    if currObject.isActive():
                        objects.elements[currObject.fields['h_id']] \
                               .add_tm(currObject)
                    else:
                        objects.elements[currObject.fields['h_id']] \
                               .remove_tm(currObject)
                elif currObject.get_type() == 'vm':
                    objects = self.config.AllCheckPoints
                    if currObject.isActive():
                        objects.elements[currObject.fields['h_id']] \
                               .add_vm(currObject)
                    else:
                        objects.elements[currObject.fields['h_id']] \
                               .remove_vm(currObject)
                elif currObject.get_type() == 'v':
                    objects = self.config.AllBatches
                    if currObject.isActive():
                        objects.elements[currObject.fields['src']] \
                               .add_source(currObject)
                        objects.elements[currObject.fields['dest']] \
                               .add_destination(currObject)
                    else:
                        objects.elements[currObject.fields['src']] \
                               .remove_source(currObject)
                        objects.elements[currObject.fields['dest']] \
                               .remove_destination(currObject)
        if conformantFile is not None:
            conformantFile.close()
            #TODO: Rename current file to timestamped one, rename .NEW to actual file...
            os.rename(self.file_of_objects,self.file_of_objects+'.'+useful.timestamp_to_ISO(useful.get_timestamp()).translate(None," :./-"))
            os.rename(self.file_of_objects+".NEW",self.file_of_objects)

    def loadNames(self):
        with open(self.file_of_names) as csvfile:
            reader = unicodecsv.DictReader(csvfile, delimiter="\t")
            for row in reader:
                keyObj = row[self.keyColumn]
                keyLang = row['lang']
                currObject = self.elements[keyObj]
                currObject.names[keyLang] = row

    def newObject(self):
        return None

    def initCount(self):
        for k, v in self.elements.items():
            if self.count < int(v.fields[self.keyColumn]):
                self.count = int(v.fields[self.keyColumn])

    def getNewId(self):
        if self.count == 0:
            self.initCount()
        self.count += 1
        return self.count

    def createObject(self):
        currObject = self.newObject()
        currObject.initialise(self.fieldnames)
        self.initCount()
        tmp = unicode(self.getNewId())
        currObject.fields[self.keyColumn] = tmp
        currObject.id = tmp
        self.elements[tmp] = currObject
        currObject.fields["begin"] = useful.now()
        return currObject

    def unique_acronym(self, acronym, myID ):
        acronym = acronym.lower()
        for k, element in self.elements.items():
            if element.fields['acronym'].lower() == acronym \
                    and unicode(myID)!=unicode(element.fields[self.keyColumn]):
                return False
        return True

    def get(self, iditem):
        if iditem and iditem in self.elements.keys():
            return self.elements[iditem]
        return None

    def getItem(self, iditem):
        if iditem:
            iditem = unicode(iditem)
            if iditem == u'new':
                return self.createObject()
            elif (iditem.endswith(u".")):
                try:
                    element = config.AllBarcodes.barcode_to_item(
                        iditem[:len(iditem)-1])
                    if element.get_type() == self.get_type():
                        return element
                except:
                    return None
            elif (iditem.endswith(u"!")):
                acronym = iditem[:len(iditem)-1]
                for k, element in self.elements.items():
                    if element.fields['acronym'] == acronym:
                        return element
                return None
            elif iditem in self.elements.keys():
                return self.elements[iditem]
        return None

    def delete(self, anID):
        del self.elements[unicode(anID)]
    
    def get_class_acronym(self):
        return None

    def getName(self,lang):
        return self.config.getName(self,lang)

    def get_sorted(self):
        return collections.OrderedDict(sorted(self.elements.items(),
                                       key=lambda t: t[1].get_acronym().upper())).keys()

    def get_sorted_hierarchy(self):
        return sorted(self.elements,
#                      key=lambda t: t[1].get_acronym_hierarchy() )
                      key=lambda t: self.elements[t].get_acronym_hierarchy().upper() )

    def findAcronym(self, acronym):
        for k, element in self.elements.items():
            if element.fields['acronym'] == acronym:
                return element
        return None

    def findBarcode(self, barcode):
        try:
            elem = config.AllBarcodes.barcode_to_item(barcode)
        except:
            return None

class AllUsers(AllObjects):

    def __init__(self, config):
        AllObjects.__init__(self, 'u', User.__name__, config)
        self.fieldnames = ['begin', 'u_id', 'active', 'acronym', 'remark',
                           'registration', 'phone', 'mail', 'password',
                           'language', 'gf_id', 'user']
        self.fieldtranslate = ['begin', 'lang', 'u_id', 'name', 'user']

    def newObject(self):
        return User()

    def checkUser(self, mail, password):
        user = self.getUser(mail)
        if user:
            return user.checkPassword(password)
        return False

    def getUser(self, mail):
        mail = mail.lower()
        for myId, user in self.elements.items():
            if user.fields['mail'].lower() == mail:
                return user
        return None

    def get_class_acronym(self):
        return 'user'

    def get_group_type(self):
        return 'gf'


class AllEquipments(AllObjects):

    def __init__(self, config):
        AllObjects.__init__(self, 'e', Equipment.__name__, config)
        self.fieldnames = ["begin", "e_id", "active",
                           "acronym", "remark", 'colorgraph', 'gu_id', "user"]
        self.fieldtranslate = ['begin', 'lang', 'e_id', 'name', 'user']

    def newObject(self):
        return Equipment(self.config)

    def get_class_acronym(self):
        return 'equipment'

    def get_group_type(self):
        return 'gu'


class AllContainers(AllObjects):

    def __init__(self, config):
        AllObjects.__init__(self, 'c', Container.__name__, config)
        self.fieldnames = ["begin", "c_id", "active",
                           "acronym", "remark", 'colorgraph', 'gu_id', "user"]
        self.fieldtranslate = ['begin', 'lang', 'c_id', 'name', 'user']

    def newObject(self):
        return Container(self.config)

    def get_class_acronym(self):
        return 'container'

    def get_group_type(self):
        return 'gu'


class AllPlaces(AllObjects):

    def __init__(self, config):
        AllObjects.__init__(self, 'p', Place.__name__, config)
        self.fieldnames = ['begin', 'p_id', 'active',
                           'acronym', 'remark', 'colorgraph', 'gu_id', 'user']
        self.fieldtranslate = ['begin', 'lang', 'p_id', 'name', 'user']

    def newObject(self):
        return Place(self.config)

    def get_class_acronym(self):
        return 'place'

    def get_group_type(self):
        return 'gu'


#TODO: AlarmLog n'enregistre que les alarmes des senseurs.
#TODO: Celles des Observations et des Versements devraient l'être aussi: il faut pouvoir les listers dans le contexte de leur lot.
#TODO: durée de séjour d'un lot: aussi possibilité d'alarmes? les logger...
#TODO: Notion d'ACTION CORRECTIVE enregistrée: remarque par qui, quand? Statut de cloture?
class AllAlarmLogs(AllObjects):

    def __init__(self, config):
        AllObjects.__init__(self, 'al', AlarmLog.__name__, config)
        self.file_of_objects = os.path.join(DIR_DATA_CSV, "alarmlogs.csv")
        self.file_of_names = None
        self.fieldnames = ['begin', 'al_id', 'cont_id', 'cont_type',
                           's_id', 's_type', 'value', 'typealarm', 'a_id', 'begintime',
                           'alarmtime', 'degree', 'completedtime', 'remark', 'active', 'user']
        self.fieldtranslate = None

    def newObject(self):
        return AlarmLog()

    def get_logs_for_source(self, component, begin, end):
        logs = []
        sid = component.getID()
        stype = component.get_type()
        if begin or end:
            for kal in self.elements.keys():
                e = self.elements[kal]
                time = e.getTimestamp()
                if (sid == e.fields['s_id']) and ( (e.fields['s_type'] ==  stype) or (e.fields['s_type']=='' and stype=='s') ) :
                    if ( not begin or (time >= begin) ) and ( not end or (time < end) ):
                        logs.append(e)
        else:
            for kal in self.elements.keys():
                e = self.elements[kal]
                if (sid == e.fields['s_id']) and ( (e.fields['s_type'] ==  stype) or (e.fields['s_type']=='' and stype=='s') ) :
                    logs.append(e)
        return sorted(logs, key=lambda t: t.fields['begintime'])

    def get_logs_for_component(self, component, begin, end):
        logs = []
        sid = component.getID()
        stype = component.get_type()
        if begin or end:
            for kal in self.elements.keys():
                e = self.elements[kal]
                time = e.getTimestamp()
                if (sid == e.fields['cont_id']) and ( e.fields['cont_type'] == stype ):
                    if ( not begin or (time >= begin) ) and ( not end or (time < end) ):
                        logs.append(e)
        else:
            for kal in self.elements.keys():
                e = self.elements[kal]
                if (sid == e.fields['cont_id']) and ( e.fields['cont_type'] == stype ):
                    logs.append(e)
        return sorted(logs, key=lambda t: t.fields['begintime'])

    def get_class_acronym(self):
        return 'alarmlog'

    def get_group_type(self):
        return 'a'

class AllHalflings(AllObjects):

    def __init__(self, config):
        AllObjects.__init__(self, "halfling", Halfling.__name__, config)
        self.file_of_objects = os.path.join(DIR_APP_CSV, "halflings.csv")
        self.file_of_names = None
        self.keyColumn = "classname"
        self.fieldnames = ['begin', 'classname', 'glyphname', 'user']
        self.fieldtranslate = None

    def newObject(self):
        return Halfling()

    def getString(self):
        tmp = ''
        for k, v in self.elements.items():
            tmp = tmp + k + '/' + v.fields['glyphname'] + ' '
        return tmp[0:-1]

    def get_class_acronym(self):
        return 'halfling'

    def getHalfling(self,acronym, supp_classes = ""):
        try:
            return self.elements[acronym].getHalfling(supp_classes)
        except:
            traceback.print_exc()
            return "<H1>"+acronym+" not found</H1>"

class AllAlarms(AllObjects):

    def __init__(self, config):
        AllObjects.__init__(self, 'a', Alarm.__name__, config)
        self.fieldnames = ['begin', 'a_id', 'active', 'acronym', 'o_sms1',
                           'o_sms2', 'o_email1', 'o_email2', 'o_sound1',
                           'o_sound2', 'relay1', 'relay2', 'remark', 'user']
        self.fieldtranslate = ['begin', 'lang', 'a_id', 'name', 'user']

    def newObject(self):
        return Alarm()

    def get_class_acronym(self):
        return 'alarm'

class AllManualData(AllObjects):

    def __init__(self, config):
        AllObjects.__init__(self, 'd', ManualData.__name__, config)
        self.file_of_names = None
        self.fieldnames = ['begin', 'd_id', 'dm_id', 'object_id', 'object_type',
                           'time', 'h_id', 'remark', 'm_id', 'value', 'al_id', 'active',
                           'user']
        self.fieldtranslate = None

    def newObject(self):
        return ManualData()

    def get_class_acronym(self):
        return 'manualdata'


class AllPourings(AllObjects):

    def __init__(self, config):
        AllObjects.__init__(self, 'v', Pouring.__name__, config)
        self.file_of_names = None
        self.fieldnames = ['begin', 'v_id', 'vm_id', 'src', 'dest', 'time',
                           'h_id', 'quantity', 'm_id', 'remark', 'al_id',
                           'active', 'user']
        self.fieldtranslate = None

    def newObject(self):
        return Pouring()

    def get_class_acronym(self):
        return 'pouring'


class AllGroups(AllObjects):
    def __init__(self, obj_type, class_name, config):
        AllObjects.__init__(self, obj_type, class_name, config)
        self.fieldrelations = ['begin', 'parent_id',
                               'child_id', 'active', 'user']

    def load(self):
        AllObjects.load(self)
        self.check_relation()
        self.load_relation()

    def check_relation(self):
        filename = self.file_of_relations
        if not os.path.exists(filename):
            self.create_relation(filename)

    def create_relation(self, fname):
        with open(fname, 'w') as csvfile:
            csvfile.write(self.fieldrelations[0])
            tmp = 1
            while tmp < len(self.fieldrelations):
                csvfile.write('\t'+self.fieldrelations[tmp])
                tmp = tmp + 1
            csvfile.write('\n')

    def get_master_groups(self):
        children = {}
        for k, group in self.elements.items():
            if group.fields['g_parent'] == '':
                children[k] = group
        return children

    def load_relation(self):
        with open(self.file_of_relations) as csvfile:
            reader = unicodecsv.DictReader(csvfile, delimiter="\t")
            for row in reader:
                parent = row['parent_id']
                child = row['child_id']
                currObject = self.elements[child]
                if 'active' in row and (row['active'] == '0'):
                    currObject.add_relation(self.elements[parent])
                else:
                    currObject.remove_relation(self.elements[parent])
        self.load_family()

    def load_family(self):
        for k, g in self.elements.items():
            g.parents = []
            g.children = []
            g.siblings = []
            g.load_parents()
            g.load_children()
            g.load_siblings()

    def get_hierarchy_str(self, g=None, myString=None):
        if myString is None:
            myString = []
        for k, group in self.elements.items():
            cond1 = (g == None and len(group.related) == 0)
            cond2 = (g is not None and g.getID() in group.related)
            if cond1 or cond2:
                myString.append(k)
                myString.append('>>')
                self.get_hierarchy_str(group, myString)
                myString.append('<<')
        return myString

    def get_fullmap_str(self):
        objMap = []
        # find groups without parents
        for k, group in self.elements.items():
            parents = group.get_parents()
            if not parents or len(parents) == 0:
                objMap.append(group)
        objMap = sorted(objMap,key=lambda t: t.get_acronym().upper())
        # go down the hierarchy...
        fullmap = []
        for group in objMap:
                k = group.getID()
                fullmap.append(k)
                fullmap += group.get_submap_str()
        return fullmap

    def get_class_acronym(self):
        return 'group'

class AllGrUsage(AllGroups):
    def __init__(self, config):
        AllGroups.__init__(self, 'gu', GrUsage.__name__, config)
        self.fieldnames = ["begin", "gu_id",
                           "active", "acronym", "rank", "remark", "user"]
        self.fieldtranslate = ['begin', 'lang', 'gu_id', 'name', 'user']
        self.file_of_relations = os.path.join(DIR_DATA_CSV, "GUrelations.csv")

    def newObject(self):
        return GrUsage(self.config)

    def get_class_acronym(self):
        return 'guse'

    def get_group_type(self):
        return 'gu'

    def get_usages_for_recipe(self, recipes):
        usages = set()
        for krecipe in recipes:
            if krecipe in self.config.AllGrRecipe.elements:
                recipe = self.config.AllGrRecipe.elements[krecipe]
                if recipe.fields['gu_id'] in self.elements:
                    usage = self.elements[recipe.fields['gu_id']]
                    if usage.isActive():
                        usages.add(usage)
        checkpoints = self.config.AllCheckPoints.get_checkpoints_for_recipe(recipes)
        for e in checkpoints:
            if e.fields['gu_id'] in self.elements:
                usage = self.elements[e.fields['gu_id']]
                if usage.isActive():
                    usages.add(usage)
            listtm = e.get_hierarchy_tm([],None)
            for t in listtm:
                if t in self.config.AllTransferModels.elements:
                    tm = self.config.AllTransferModels.elements[t];
                    if tm.fields['gu_id'] in self.elements:
                        usage = self.elements[tm.fields['gu_id']]
                        if usage.isActive():
                            usages.add(usage)
        usages = list(usages)         
        usages.sort(key=lambda x: int(x.fields['rank']), reverse=False)
        return usages

class AllGrRecipe(AllGroups):
    def __init__(self, config):
        AllGroups.__init__(self, 'gr', GrRecipe.__name__, config)
        self.fieldnames = ["begin", "gr_id", "gu_id", 
                           "basicqt", "m_id", "cost", "fixed_cost", "lifespan",
                           "active", "acronym", "remark", "user"]
        self.fieldtranslate = ['begin', 'lang', 'gr_id', 'name', 'user']
        self.file_of_relations = os.path.join(DIR_DATA_CSV, "GRrelations.csv")

    def newObject(self):
        return GrRecipe(self.config)

    def get_class_acronym(self):
        return 'grecipe'

    def get_group_type(self):
        return 'gr'

class AllCheckPoints(AllGroups):
    def __init__(self, config):
        AllGroups.__init__(self, 'h', CheckPoint.__name__, config)
        self.fieldnames = ["begin", "h_id", "active", "acronym",
                           'rank', 'abstract', "remark", 'gr_id',
                           'gu_id', "user"]
        self.fieldtranslate = ['begin', 'lang', 'h_id', 'name', 'user']
        self.fieldcontrols = ['begin', 'h_id',
                              'object_type', 'object_id', 'user']
        self.file_of_relations = os.path.join(DIR_DATA_CSV, "Hrelations.csv")
        self.file_of_controls = os.path.join(DIR_DATA_CSV, "Hcontrols.csv")

    def newObject(self):
        return CheckPoint(self.config)

    def get_class_acronym(self):
        return 'checkpoint'

    def get_group_type(self):
        return 'h'

    def load(self):
        AllGroups.load(self)
        self.check_controls()
        self.load_controls()

    def check_controls(self):
        filename = self.file_of_controls
        if not os.path.exists(filename):
            self.create_control(filename)

    def create_control(self, fname):
        with open(fname, 'w') as csvfile:
            csvfile.write(self.fieldcontrols[0])
            tmp = 1
            while tmp < len(self.fieldcontrols):
                csvfile.write('\t'+self.fieldcontrols[tmp])
                tmp = tmp + 1
            csvfile.write('\n')

    def load_controls(self):
        with open(self.file_of_controls) as csvfile:
            reader = unicodecsv.DictReader(csvfile, delimiter="\t")
            for row in reader:
                type = row['object_type']
                id = row['object_id']
                if id:
                    currObject = self.config.get_object(type,id)
                    if currObject:
                        currObject.add_checkpoint(row['h_id'],row['time'] if 'time' in row else row['begin'] )

    def get_checkpoints_for_recipe(self, recipes):
        checkpoints = []
        for k, e in self.elements.items():
            if e.fields['gr_id'] in recipes and e.isActive() and e.fields['abstract'] == '0':
                checkpoints.append(e)
        checkpoints.sort(key=lambda x: int(x.fields['rank']), reverse=False)
        return checkpoints

    def get_checkpoints_for_usage(self, usages):
        checkpoints = []
        for k, e in self.elements.items():
            if e.fields['gu_id'] in usages and e.isActive() and e.fields['abstract'] == '0':
                checkpoints.append(e)
        checkpoints.sort(key=lambda x: int(x.fields['rank']), reverse=False)
        return checkpoints

    def get_checkpoints_for_recipe_usage(self, recipes, usages):
        checkpoints = []
        for k, e in self.elements.items():
            if e.fields['abstract'] == '0' and e.isActive():
##                if not e.fields['gr_id'] or (e.fields['gr_id'] in recipes):
##                    if not e.fields['gu_id'] or (e.fields['gu_id'] in usages):
                if e.fields['gr_id'] in recipes:
                    if e.fields['gu_id'] in usages:
                        checkpoints.append(e)
        checkpoints.sort(key=lambda x: int(x.fields['rank']), reverse=False)
        return checkpoints


class AllGrFunction(AllGroups):
    def __init__(self, config):
        AllGroups.__init__(self, 'gf', GrFunction.__name__, config)
        self.fieldnames = ["begin", "gf_id",
                           "active", "acronym", "remark", "user"]
        self.fieldtranslate = ['begin', 'lang', 'gf_id', 'name', 'user']
        self.file_of_relations = os.path.join(DIR_DATA_CSV, "GFrelations.csv")

    def newObject(self):
        return GrFunction(self.config)

    def get_class_acronym(self):
        return 'gfunction'

    def get_group_type(self):
        return 'gf'


class AllMeasures(AllObjects):

    def __init__(self, config):
        AllObjects.__init__(self, 'm', Measure.__name__, config)
        self.fieldnames = ['begin', 'm_id', 'active',
                           'acronym', 'unit', 'remark', 'min', 'step', 'max', 'user']
        self.fieldtranslate = ['begin', 'lang', 'm_id', 'name', 'user']

    def newObject(self):
        return Measure()

    def get_class_acronym(self):
        return 'measure'


iteration_cache = None

class AllSensors(AllObjects):
    
# We dynamically append all [input.xxx] from hardconfig to _queryChannels
    _queryChannels = ['wire',
                      'radio',
                      'http',
                      'json',
                      'cputemp',
                      'system']
    
    def __init__(self, config):
        AllObjects.__init__(self, 's', Sensor.__name__, config)
        self.fieldnames = ['begin', 's_id', 'c_id', 'p_id', 'e_id', 'm_id',
                           'active', 'acronym', 'remark', 'channel', 'sensor',
                           'subsensor', 'valuetype', 'formula', 'minmin',
                           'min', 'typical', 'max', 'maxmax', 'a_minmin',
                           'a_min', 'a_typical', 'a_max', 'a_maxmax', 'lapse1',
                           'lapse2', 'lapse3', 'a_none', 'user']
        self.fieldtranslate = ['begin', 'lang', 's_id', 'name', 'user']
        self.add_query_channels_from_hardconfig()

    def newObject(self):
        return Sensor()

    def get_class_acronym(self):
        return 'sensor'

    def add_query_channel(self, channel):
        '''
        Supposed to be used when reading HardConfig, to add the [input.xxx]
        fields
        '''
        self._queryChannels.append(channel)

    def get_query_channels(self):
        return self._queryChannels
    
    def add_query_channels_from_hardconfig(self):
        for key in self.config.HardConfig.inputs:
            self.add_query_channel(key)

    def getColor(self, ids):
        color = "#006600"
        if ids in self.elements:
            sensor = self.elements[ids]
            if not sensor.fields['p_id'] == '':
                pid = sensor.fields['p_id']
                if not (self.config
                            .AllPlaces
                            .elements[pid]
                            .fields['colorgraph'] == ''):
                    color = (self.config
                                 .AllPlaces
                                 .elements[pid]
                                 .fields['colorgraph'])
            elif not sensor.fields['c_id'] == '':
                cid = sensor.fields['c_id']
                if not (self.config
                            .AllContainers
                            .elements[cid]
                            .fields['colorgraph'] == ''):
                    color = (self.config
                                 .AllContainers
                                 .elements[cid]
                                 .fields['colorgraph'])
            elif not sensor.fields['e_id'] == '':
                eid = sensor.fields['e_id']
                if not (self.config
                            .AllEquipments
                            .elements[eid]
                            .fields['colorgraph'] == ''):
                    color = (self.config
                                 .AllEquipments
                                 .elements[eid]
                                 .fields['colorgraph'])
        return color

    def correctValueAlarm(self):
        for k, sensor in self.elements.items():
            sensor.setCorrectAlarmValue()
    
    def update(self, now):
        iteration_cache = {}
        def set_cache(self, cache):
            channel = self.fields['channel']
            field = self.fields['sensor']
            if not channel in iteration_cache:
                iteration_cache[channel] = {}
            iteration_cache[channel][field] = cache
            
        def get_cache(self):
            '''
            Returns the data from iteration_cache for at the coresponding field.
            May return None
            '''
            channel = self.fields['channel']
            field = self.fields['sensor']
            try:
                return iteration_cache[channel][field]
            except KeyError:
                return None

        for k, sensor in self.elements.items():
            if sensor.fields['channel'] in self._queryChannels \
                                        and sensor.isActive():
                value, cache = sensor.get_value_sensor(self.config, get_cache(sensor))
                if value is not None:
                    sensor.update(now, value, self.config)
                if cache is not None:
                    set_cache(sensor, cache)

    def check_rrd(self):
        for k, v in self.elements.items():
            filename = os.path.join(DIR_RRD, v.getRRDName())
            if not os.path.exists(filename):
                v.createRRD()


class AllBatches(AllObjects):

    def __init__(self, config):
        AllObjects.__init__(self, 'b', Batch.__name__, config)
        self.fieldnames = ["begin", "b_id", "active", "acronym",
                           "basicqt", "m_id", "time", "cost", "fixed_cost", "remark",
                           'gr_id', 'expirationdate', 'completedtime', "user"]
        self.fieldtranslate = ['begin', 'lang', 'b_id', 'name', 'user']

    def newObject(self):
        return Batch(self.config)

    def get_class_acronym(self):
        return 'batch'

    def get_group_type(self):
        return 'gr'

    def get_batches_for_recipes(self, recipes):
        batches = []
        #print recipes
        #print usages
        for k, e in self.elements.items():
            if e.fields['gr_id'] in recipes:
                batches.append(e)
        return batches

    def get_batches_for_recipe_usage(self, recipes, usages):
        batches = []
        #print recipes
        #print usages
        for k, e in self.elements.items():
            if e.isActive() and (not e.fields['gr_id'] or (e.fields['gr_id'] in recipes)):
                #print "key="+k+", recipe=",e.fields['gr_id']
                tmp = e.get_last_transfer()
                if tmp is not None:
                    tmp = self.config.AllTransfers.elements[tmp]
                    currObj = self.config.get_object(tmp.fields['cont_type'], tmp.fields['cont_id'])
                    #print currObj.__repr__()+"="+currObj.get_group()
                    if currObj.get_group() in usages:
                        batches.append(e)
        return batches

    def findNextAcronym(self,prefix,totalLen,count=0):
        while True:
            tmp = totalLen - len(prefix) - len(unicode(count))
            if tmp < 0:
                return None
            tmpname = prefix + ('0' * tmp) + unicode(count)
            cond = self.unique_acronym(tmpname, -1)
            if cond:
                return tmpname
            count += 1

class AllTransfers(AllObjects):

    def __init__(self, config):
        AllObjects.__init__(self, 't', Transfer.__name__, config)
        self.file_of_names = None
        self.fieldnames = ["begin", "t_id", 'tm_id', 'time', 'h_id', "cont_id",
                           "cont_type", "object_id", "object_type", "remark",
                           'al_id', 'active', "user"]
        self.fieldtranslate = None

    def newObject(self):
        return Transfer(self.config)

    def get_class_acronym(self):
        return 'transfer'


class AllTransferModels(AllObjects):

    def __init__(self, config):
        AllObjects.__init__(self, 'tm', TransferModel.__name__, config)
        self.fieldnames = ["begin", "tm_id", 'acronym',
                           'gu_id', 'h_id', 'rank', "remark", 'active', "user"]
        self.fieldtranslate = ['begin', 'lang', 'tm_id', 'name', 'user']

    def newObject(self):
        return TransferModel(self.config)

    def get_class_acronym(self):
        return 'transfermodel'

    def get_group_type(self):
        return 'h'

    def isModeling(self):
        return "t"    

class AllPouringModels(AllObjects):

    def __init__(self, config):
        AllObjects.__init__(self, 'vm', PouringModel.__name__, config)
        self.fieldnames = ["begin", "vm_id", 'acronym', 'src', 'dest',
                           'quantity', 'h_id', 'rank', "in", "remark", 'active',
                           "user"]
        self.fieldtranslate = ['begin', 'lang', 'vm_id', 'name', 'user']

    def newObject(self):
        return PouringModel(self.config)

    def get_class_acronym(self):
        return 'pouringmodel'

    def get_group_type(self):
        return 'h'

    def isModeling(self):
        return "v"
    
class AllManualDataModels(AllObjects):

    def __init__(self, config):
        AllObjects.__init__(self, 'dm', ManualDataModel.__name__, config)
        self.fieldnames = ["begin", "dm_id", 'acronym', 'm_id', 'h_id', 'rank',
                           "remark", 'active', 'minmin',
                           'min', 'typical', 'max', 'maxmax', 'a_minmin',
                           'a_min', 'a_typical', 'a_max', 'a_maxmax', 'a_none', "user"]
        self.fieldtranslate = ['begin', 'lang', 'dm_id', 'name', 'user']

    def newObject(self):
        return ManualDataModel(self.config)

    def get_class_acronym(self):
        return 'manualdatamodel'

    def get_group_type(self):
        return 'h'

    def isModeling(self):
        return "d"
    
class AllBarcodes(AllObjects):

    def __init__(self, config):
        AllObjects.__init__(self, 'barcode', Barcode.__name__, config)
        self.file_of_objects = os.path.join(DIR_DATA_CSV, "codes.csv")
        self.file_of_names = None
        self.keyColumn = "code"
        self.fieldnames = ['begin', 'type',
                           'idobject', 'code', 'active', 'user']
        self.fieldtranslate = None
        self.EAN = barcode.get_barcode_class('ean13')

    def load(self):
        AllObjects.check_csv(self, self.file_of_objects)
        with open(self.file_of_objects) as csvfile:
            reader = unicodecsv.DictReader(csvfile, delimiter="\t")
            for row in reader:
                key = row[self.keyColumn]
                if row['active'] == '0':
                    del self.elements[key]
                elif len(row['code']) > 0:
                    currObject = self.newObject(
                        self.config.getObject(row['idobject'], row['type']))
                    currObject.fields = row
                    currObject.id = key
                    self.elements[key] = currObject
        #self.to_pictures()

    def newObject(self, item):
        return Barcode(item)

    def get_barcode(self, myType, myID):
        for k in self.elements.keys():
            if self.elements[k].element:
                if self.elements[k].element.get_type() == myType \
                        and unicode(self.elements[k].element.getID()) == myID:
                    #self.elements[k].barcode_picture()
                    return k
        return ''

    def unique_barcode(self, some_code, myID, myType):
        some_code = int(some_code)
        for k, v in self.elements.items():
            if ( some_code == int(k)
                    and not myID == v.getID()
                    and not myType == v.fields['type']):
                return False
        return True

    def add_barcode(self, item, some_code, user):
        if self.unique_barcode(some_code, item.getID(), item.get_type()):
            oldBarcode = self.get_barcode(item.get_type(), item.getID())
            if not oldBarcode == some_code and not oldBarcode == '':
                self.delete_barcode(oldBarcode, user)
            self.elements[some_code] = self.create_barcode(item, some_code, user)

    def delete_barcode(self, oldBarcode, user):
        self.write_csv(oldBarcode, 0, user)
        del self.elements[oldBarcode]

    def write_csv(self, some_code, active, user):
        with open(self.file_of_objects, "a") as csvfile:
            tmpCode = self.create_fields(some_code, active, user)
            writer = unicodecsv.DictWriter(csvfile,
                                           delimiter='\t',
                                           fieldnames=self.fieldnames,
                                           encoding="utf-8")
            writer.writerow(tmpCode)

    def create_barcode(self, item, some_code, user):
        tmp = self.newObject(item)
        fields = self.create_fields(some_code, 1, user, item)
        tmp.fields = fields
        self.elements[some_code] = tmp
        tmp.element = item
        self.write_csv(some_code, 1, user)
        return tmp

    def create_fields(self, some_code, active, user, item=None):
        fields = {}
        fields['begin'] = useful.now()
        if item is None:
            fields['type'] = self.elements[some_code].element.get_type()
            fields['idobject'] = self.elements[some_code].element.id
        else:
            fields['type'] = item.get_type()
            fields['idobject'] = item.id
        fields['code'] = some_code
        fields['active'] = active
        fields["user"] = user.fields['u_id']
        return fields

    def validate_barcode(self, some_code, anID, aType):
        some_code = unicode(some_code)
        if len(some_code) < 12 or len(some_code) > 13:
            return False
        try:
            ean = self.EAN(some_code)
        except:
            traceback.print_exc()
            return False
        if self.unique_barcode(some_code, anID, aType) is not True:
            return False
        return True

##    def to_pictures(self):
##        for k, v in self.elements.items():
##            v.barcode_picture()

    def barcode_to_item(self, some_code):
        for k, barcode in self.elements.items():
            if barcode.fields['code'] == some_code:
                return self.config.get_object(barcode.fields['type'],barcode.fields['idobject'])

    def get_class_acronym(self):
        return 'barcode'


class ConnectedUser():

    def __init__(self, user):
        self.cuser = user
        self.datetime = time.time()

    def update(self):
        self.datetime = time.time()


class AllConnectedUsers():

    def __init__(self):
        self.users = {}

    def __getitem__(self, key):
        return self.users[key]

    def addUser(self, user):
        self.update()
        mail = user.fields['mail'].lower()
        if mail not in self.users:
            self.users[mail] = ConnectedUser(user)
        else:
            self.users[mail].update()

    def update(self):
        updatetime = time.time()
        for mail, connecteduser in self.users.items():
            if (updatetime - connecteduser.datetime) > 900:
                del self.users[mail]

    def isConnected(self, mail, password):
        self.update()
        mail = mail.lower()
        if mail in self.users:
            user = self.users[mail].cuser
            if user.fields['password'] == password:
                self.users[mail].update()
                return True
        return False

    def getLanguage(self, mail):
        mail = mail.lower()
        if mail in self.users:
            return self.users[mail].cuser.fields['language']
        return 'english'

    def disconnect(self, mail):
        mail = mail.lower()
        if mail in self.users:
            del self.users[mail]


class AllLanguages(AllObjects):

    def __init__(self, config):
        AllObjects.__init__(self, 'l', Language.__name__, config)
        self.file_of_objects = os.path.join(DIR_APP_CSV, "language.csv")
        self.file_of_names = None
        self.nameColumn = "name"

    def newObject(self):
        return Language()

    def __getitem__(self, key):
        return self.elements[key]

    def get_class_acronym(self):
        return 'language'


class AllMessages(AllObjects):

    def __init__(self, config):
        AllObjects.__init__(self, 'message', Message.__name__, config)
        self.elements = {}
        self.names = {}
        self.file_of_objects = os.path.join(DIR_APP_CSV + "mess.csv")
        self.file_of_names = os.path.join(DIR_APP_CSV + "messages.csv")
        self.nameColumn = "name"

    def newObject(self):
        return Message()

    def __getitem__(self, key):
        return self.elements[key]

    def get_class_acronym(self):
        return 'message'


class Language(ConfigurationObject):

    def __init__(self):
        ConfigurationObject.__init__(self)

    def __str__(self):
        string = "\nLanguage :"
        for field in self.fields:
            string = string + "\n" + field + " : " + self.fields[field]
        return string + "\n"

    def get_type(self):
        return 'language'


class Message(ConfigurationObject):

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

    def __str__(self):
        string = "\nUtilisateur :"
        for field in self.fields:
            string = string + "\n" + field + \
                " : " + unicode(self.fields[field])
        return string + "\n"

    def checkPassword(self, password):
        return self.fields['password'] == password

    def get_type(self):
        return 'u'

    def get_class_acronym(self):
        return 'user'

    def validate_form(self, data, configuration, lang):
        tmp = super(User, self).validate_form(data, configuration, lang)
        if tmp is True:
            tmp = ''
        if tmp is True:
            tmp = ''
        if data['password'] and len(data['password']) < 8:
            tmp += configuration.getMessage('passwordrules',lang) + '\n'

        if tmp == '':
            return True
        return tmp

    def set_value_from_data(self, data, c, user):
        super(User, self).set_value_from_data(data, c, user)
        tmp = ['phone', 'mail', 'language']
        for elem in tmp:
            self.fields[elem] = data[elem]
        self.fields['registration'] = self.created
        if data['password']:
            self.fields['password'] = useful.encrypt(
                data['password'], self.fields['registration'])
        self.fields['gf_id'] = data['group']
        self.save(c, user)

    def get_group(self):
        return self.fields['gf_id']

    def adminAllowed(self,c):
        user_group = self.get_group()
        if user_group and user_group in c.AllGrFunction.elements:
            aGroup = c.AllGrFunction.elements[user_group]
            if aGroup.fields["acronym"].lower() == KEY_ADMIN:
                return True
            for user_group in aGroup.get_all_parents([],c.AllGrFunction):
                bGroup = c.AllGrFunction.elements[user_group]
                if bGroup.fields["acronym"].lower() == KEY_ADMIN:
                    return True
        return False

    def updateAllowed(self,c,type):
        user_group = self.get_group()
        if user_group and user_group in c.AllGrFunction.elements:
            key_upd = u"upd_"+type
            aGroup = c.AllGrFunction.elements[user_group]
            if aGroup.fields["acronym"].lower() == KEY_ADMIN:
                return True
            if aGroup.fields["acronym"].lower() == key_upd:
                return True
            for user_group in aGroup.get_all_parents([],c.AllGrFunction):
                bGroup = c.AllGrFunction.elements[user_group]
                if bGroup.fields["acronym"].lower() == KEY_ADMIN:
                    return True
                if bGroup.fields["acronym"].lower() == key_upd:
                    return True
        return False

    def allowed(self,c):
        user_group = self.get_group()
        result = " "
        if user_group and user_group in c.AllGrFunction.elements:
            key_upd = u"upd_"+self.get_type()
            aGroup = c.AllGrFunction.elements[user_group]
            result += aGroup.fields["acronym"].lower() + " "
            for user_group in aGroup.get_all_parents([],c.AllGrFunction):
                bGroup = c.AllGrFunction.elements[user_group]
                result += bGroup.fields["acronym"].lower() + " "
        if " admin " in result: # all is updatable then !
            result += " upd_a upd_al upd_b upd_c upd_d upd_dm upd_e upd_gf upd_gr upd_gu upd_h upd_m upd_p upd_s upd_t upd_tm upd_u upd_v upd_vm "
        return result


class Equipment(ConfigurationObject):

    def __init__(self, config):
        ConfigurationObject.__init__(self)
        self.config = config

    def __str__(self):
        string = "\nEquipement :"
        for field in self.fields:
            string = string + "\n" + field + " : " + self.fields[field]
        return string + "\n"

    def get_type(self):
        return 'e'

    def getID(self):
        return self.fields['e_id']

    def get_class_acronym(self):
        return 'equipment'

    def get_sensors_in_component(self, config):
        listSensor = []
        for k, sensor in config.AllSensors.elements.items():
            if sensor.is_in_component('e', self.id):
                listSensor.append(k)
        return listSensor

    def isAlarmed(self,c):
        for kSensor,aSensor in c.AllSensors.elements.items():
            if aSensor.isAlarmed(c) and aSensor.is_in_component('e',self.id):
                return True
        return False

    def validate_form(self, data, configuration, lang):
        return super(Equipment, self).validate_form(data, configuration, lang)

    def set_value_from_data(self, data, c, user):
        super(Equipment, self).set_value_from_data(data, c, user)
        self.fields['colorgraph'] = data['colorgraph']
        self.fields['gu_id'] = data['group']
        self.save(c, user)

    def get_group(self):
        return self.fields['gu_id']


class Container(ConfigurationObject):

    def __init__(self, config):
        ConfigurationObject.__init__(self)
        self.config = config

    def __str__(self):
        string = "\nContainer :"
        for field in self.fields:
            string = string + "\n" + field + " : " + self.fields[field]
        return string + "\n"

    def get_type(self):
        return 'c'

    def get_class_acronym(self):
        return 'container'

    def get_sensors_in_component(self, config):
        listSensor = []
        for k, sensor in config.AllSensors.elements.items():
            if sensor.is_in_component('c', self.id):
                listSensor.append(k)
        return listSensor

    def isAlarmed(self,c):
        for kSensor,aSensor in c.AllSensors.elements.items():
            if aSensor.isAlarmed(c) and aSensor.is_in_component('c',self.id):
                return True
        return False

    def validate_form(self, data, configuration, lang):
        return super(Container, self).validate_form(data, configuration, lang)

    def set_value_from_data(self, data, c, user):
        super(Container, self).set_value_from_data(data, c, user)
        self.fields['colorgraph'] = data['colorgraph']
        self.fields['gu_id'] = data['group']
        self.save(c, user)

    def get_group(self):
        return self.fields['gu_id']

class AlarmingObject(ConfigurationObject):

    def __init__(self):
        ConfigurationObject.__init__(self)
        self.actualAlarm = 'typical'
        self.countActual = 0
        self.degreeAlarm = 0
        self.colorAlarm = valueCategs[0].color
        self.colorTextAlarm = valueCategs[0].text_color
        self.lastvalue = None
        self.time = 0

    def get_alarm(self,model=None):
        bounds = model.fields if model else self.fields
	if self.actualAlarm == 'typical':
	    return bounds['a_typical']
	elif self.actualAlarm == 'minmin':
	    return bounds['a_minmin']
	elif self.actualAlarm == 'min':
	    return bounds['a_min']
	elif self.actualAlarm == 'max':
	    return bounds['a_max']
	elif self.actualAlarm == 'maxmax':
	    return bounds['a_maxmax']
	elif self.actualAlarm == 'none':
	    return bounds['a_none'] #TODO:a_none field would be better

    def setCorrectAlarmValue(self,model=None):
        bounds = model.fields if model else self.fields
        if bounds['lapse1'] == '':
            bounds['lapse1'] = "99999999"
        if bounds['lapse2'] == '':
            bounds['lapse2'] = "99999999"
        if bounds['lapse3'] == '':
            bounds['lapse3'] = "99999999"

class ManualData(AlarmingObject):

    def __init__(self):
        AlarmingObject.__init__(self)

    def __str__(self):
        string = "\nManual Data :"
        for field in self.fields:
            string = string + "\n" + field + " : " + self.fields[field]
        return string + "\n"

    def get_type(self):
        return 'd'

    def get_quantity(self):
        return self.floats('value')

    def add_component(self, component):
        type = component.split('_')[0]
        id = component.split('_')[1]
        self.fields['object_id'] = id
        self.fields['object_type'] = type

    def add_measure(self, measure):
        if not measure == 'None':
            self.fields['m_id'] = unicode(measure)
        else:
            self.fields['m_id'] = ''

    def validate_form(self, data, configuration, lang):
        tmp = ''
        try:
            value = useful.date_to_ISO(data['time'])
        except:
            traceback.print_exc()
            tmp += configuration.getMessage('timerules',lang) + '\n'

        if 'value' in data and data['measure'] == u'None':
            if not data['value'] == '':
                tmp += configuration.getMessage('datarules',lang) + '\n'
        elif 'value' in data:
            try:
                value = float(data['value'])
            except:
                tmp += configuration.getMessage('floatrules',lang) + ' '+data['value']+'\n'
        try:
            aType = data['component'].split('_')[0]
            anId = data['component'].split('_')[1]
            if not configuration.is_component(aType):
                tmp += configuration.getMessage('componentrules',lang) + ' '+data['component']+'\n'
        except:
            tmp += configuration.getMessage('componentrules',lang) + '\n'

        if tmp == '':
            return True
        return tmp

    def set_value_from_data(self, data, c, user):
        #SUPER is NOT called, beware!
        if self.fields['object_type'] != '' \
                and self.fields['object_id'] != '':
            c.get_object(self.fields['object_type'],self.fields['object_id']) \
             .remove_data(self)
        tmp = ['time', 'value', 'remark']
        for elem in tmp:
            self.fields[elem] = data[elem]
        self.add_component(data['component'])
        self.add_measure(data['measure'])
        if 'h_id' in data:
            self.fields['h_id'] = data['h_id']
        else:
            self.fields['h_id'] = ''
        if 'active' in data:
            self.fields['active'] = '1'
        else:
            self.fields['active'] = '0'
        alarmCode = ""
        if ('origin' in data) and data['origin']:
            self.fields['dm_id'] = data['origin']
            model = c.AllManualDataModels.elements[data['origin']]
            typeAlarm, symbAlarm, self.colorAlarm,self.colorTextAlarm = self.getTypeAlarm(data['value'],model)
            self.actualAlarm = typeAlarm
            alarmCode = self.get_alarm(model);
        if ('a_id' in data) and data['a_id']:
            #TODO: Manual Alarm, not so "typical"
            if not self.actualAlarm:
                self.actualAlarm = "typical"
            alarmCode = data['a_id']
        if alarmCode and alarmCode in c.AllAlarms.elements:
            self.fields['al_id'] = c.AllAlarms.elements[alarmCode].launch_alarm(self, c)
        if self.isActive():
            c.get_object(self.fields['object_type'],self.fields['object_id']) \
             .add_data(self)
        else:
            c.get_object(self.fields['object_type'],self.fields['object_id']) \
             .remove_data(self)
        self.save(c, user)

    def get_class_acronym(self):
        return 'manualdata'

    # WHERE the observation was done
    def get_component(self,config):
        if not self.fields['object_id']:
            return None
        if self.fields['object_type']:
            allObjs =config.findAll(self.fields['object_type'])
        else:
            allObjs = config.AllBatches
        if self.fields['object_id'] in allObjs.elements:
            return allObjs.elements[self.fields['object_id']]
        else:
            return None

#TODO: AlarmingObject and check on Quantity ?
class Pouring(ConfigurationObject):
    def __init__(self):
        ConfigurationObject.__init__(self)

    def __str__(self):
        string = "\nPouring :"
        for field in self.fields:
            string = string + "\n" + field + " : " + self.fields[field]
        return string + "\n"

    def get_type(self):
        return 'v'

    def get_quantity(self):
        return self.floats('quantity')

    def add_measure(self, measure):
        tmp = measure.split('_')
        self.fields['m_id'] = tmp[-1]

    def validate_form(self, data, configuration, lang):
        tmp = ''
        try:
            value = useful.date_to_ISO(data['time'])
        except:
            tmp += configuration.getMessage('timerules',lang) + '\n'
        try:
            value = float(data['quantity'])
        except:
            tmp += configuration.getMessage('floatrules',lang) + '\n'
        try:
            b_id = data['src']
            if not b_id in configuration.AllBatches.elements.keys():
                tmp += configuration.getMessage('batchrules1',lang) + '\n'
        except:
            tmp += configuration.getMessage('batchrules1',lang) + '\n'
        try:
            b_id = data['dest']
            if not b_id in configuration.AllBatches.elements.keys():
                tmp += configuration.getMessage('batchrules2',lang) + '\n'
        except:
            tmp += configuration.getMessage('batchrules2',lang) + '\n'
        if data['src'] == data['dest']:
            tmp += configuration.getMessage('batchrules3',lang) + '\n'

        if tmp == '':
            return True
        return tmp

    def get_measure_in_context(self,c, currObject):
        if self.fields['src']:
            if self.fields['src'] in c.AllBatches.elements:
                aBatch = c.AllBatches.elements[self.fields['src']]
                return aBatch.get_measure(c)
        elif currObject:
            return currObject.get_measure(c)
        return ""

    def get_unit_in_context(self,c, currObject):
        if self.fields['src']:
            if self.fields['src'] in c.AllBatches.elements:
                aBatch = c.AllBatches.elements[self.fields['src']]
                return aBatch.get_unit(c)
        elif currObject:
            return currObject.get_unit(c)
        return ""

    def set_value_from_data(self, data, c, user):
        #SUPER is NOT called, beware!
        if self.fields['src'] != '' and self.fields['dest'] != '':
            c.AllBatches.elements[self.fields['src']].remove_source(self)
            c.AllBatches.elements[self.fields['dest']].remove_destination(self)
        tmp = ['time', 'remark', 'src', 'dest', 'quantity']
        for elem in tmp:
            self.fields[elem] = data[elem]
        self.fields['m_id'] = c.AllBatches.elements[data['src']].fields['m_id']
        if 'h_id' in data:
            self.fields['h_id'] = data['h_id']
        else:
            self.fields['h_id'] = ''
        alarmCode = ""
        if ('origin' in data) and data['origin']:
            self.fields['vm_id'] = data['origin']
##            model = c.AllPouringModels.elements[data['origin']]
##            typeAlarm, symbAlarm, self.colorAlarm,self.colorTextAlarm = self.getTypeAlarm(data['quantity'],model)
##            self.actualAlarm = typeAlarm
##            alarmCode = self.get_alarm(model);
        if ('a_id' in data) and data['a_id']:
            #TODO: Manual Alarm, not so "typical"
            self.actualAlarm = "typical"
            alarmCode = data['a_id']
        if alarmCode and alarmCode in c.AllAlarms.elements:
            self.fields['al_id'] = c.AllAlarms.elements[alarmCode].launch_alarm(self, c)

        if 'active' in data:
            self.fields['active'] = '1'
        else:
            self.fields['active'] = '0'
        if self.fields['active'] == '1':
            c.AllBatches.elements[data['src']].add_source(self)
            c.AllBatches.elements[data['dest']].add_destination(self)
        else:
            c.AllBatches.elements[data['src']].remove_source(self)
            c.AllBatches.elements[data['dest']].remove_destination(self)
        self.save(c, user)

    def get_class_acronym(self):
        return 'pouring'

    # WHAT is moved
    def get_source(self,config):
        if not self.fields['src']:
            return None
        allObjs = config.AllBatches
        if self.fields['src'] in allObjs.elements:
            return allObjs.elements[self.fields['src']]
        else:
            return None

    # WHERE it is moved
    def get_component(self,config):
        if not self.fields['dest']:
            return None
        allObjs = config.AllBatches
        if self.fields['dest'] in allObjs.elements:
            return allObjs.elements[self.fields['dest']]
        return None


class Group(ConfigurationObject):
    def __init__(self, config):
        ConfigurationObject.__init__(self)
        self.classes = {}
        self.groups = {}
        self.config = config
        self.parents = []
        self.children = []
        self.related = []

    def __str__(self):
        string = "\nGroup :"
        for field in self.fields:
            string = string + "\n" + field + " : " + self.fields[field]
        return string + "\n"

    def get_type(self):
        return 'g'

    def containsGroup(self, oGroup):
        if len(self.groups) > 0:
            for k, v in self.groups.items():
                if self.keyColumn in oGroup.fields.keys():
                    if k == oGroup.fields[self.keyColumn]:
                        return True
                elif v.containsGroup(oGroup):
                    return True
        return False

    def get_class_acronym(self):
        return 'group'

    def validate_form(self, data, configuration, lang):
        tmp = super(Group, self).validate_form(data, configuration, lang)
        if tmp is True:
            tmp = ''
        for k, v in configuration.findAllFromObject(self).elements.items():
            if k in data:
                if self.getID() in v.parents or self.getID() in v.siblings:
                    tmp += configuration.getMessage('grouprules',lang) + '\n'
                    return tmp
        if tmp == '':
            return True
        return tmp

    def set_value_from_data(self, data, c, user):
        super(Group, self).set_value_from_data(data, c, user)
        self.parents = []
        self.children = []
        self.siblings = []
        for a in self.related:
            if a not in data:
                self.write_group(a, c, user, '1')
                self.related.remove(a)
        for k in c.findAllFromObject(self).elements.keys():
            if k in data and k not in self.related:
                self.related.append(k)
                self.write_group(k, c, user, '0')
        c.findAllFromObject(self).load_family()

    def write_group(self, parentid, configuration, user, active):
        with open(configuration.findAllFromObject(self)
                               .file_of_relations, "a") as csvfile:
            tmpCode = {}
            tmpCode['begin'] = useful.now()
            tmpCode['parent_id'] = parentid
            tmpCode['child_id'] = self.getID()
            tmpCode["user"] = user.fields['u_id']
            tmpCode['active'] = active
            writer = unicodecsv.DictWriter(csvfile,
                                           delimiter='\t',
                                           fieldnames=configuration.findAllFromObject(self).fieldrelations, encoding="utf-8")
            writer.writerow(tmpCode)

    def get_related(self):
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

    def load_parents(self):
        for i in self.related:
            if i not in self.parents:
                self.parents.append(i)
                self.config \
                    .get_object(self.get_type(),i) \
                    .load_parents()
##            else:
##                print "Error Group "+self.get_type()+"_"+i+": GROUPE EN RELATION CIRCLAIRE DANS "+self.getID()

    def load_children(self):
        for k, group in self.config \
                            .findAll(self.get_type()) \
                            .elements \
                            .items():
            if self.getID() in group.related:
                if group.getID() not in self.children:
                    self.add_child(group)
                    group.load_children()
##                else:
##                    print "Error Group "+group.get_type()+"_"+group.getID()+": GROUPE EN RELATION CIRCLAIRE DANS "+self.getID()

    def load_siblings(self):
        for k, group in self.config \
                            .findAll(self.get_type()) \
                            .elements \
                            .items():
            for rel in group.related:
                if rel in self.related and k != self.getID():
                    self.siblings.append(k)

    def get_all_parents(self,parents=[],allObj=None):
        if not allObj:
            allObj =  self.config.findAll(self.get_type()) 
        for e in self.parents:
	    if e and e not in parents:
                parents.append(e)
                rec = allObj.get(e)
                if rec:
                    parents = rec.get_all_parents(parents, allObj)
        return parents

    def get_acronym_hierarchy(self):
        allObj =  self.config.findAll(self.get_type()) 
        parents = self.get_all_parents([],allObj)
        result = ""
        for key in reversed(parents):
            e = allObj.elements[key]    
            result += e.get_acronym()+" "
        return result+self.get_acronym()

    # Looking DOWN
    def get_submap_str(self):
        children = self.get_children()
        #print self.fields['acronym']+", children="+unicode(children)
        submap = []                      
        submap.append('>>')
        if children and len (children) > 0:
            allObj =  self.config.findAll(self.get_type())
            childObj = []
            for k in children:
                if k and k in allObj.elements:
                    childObj.append(allObj.elements[k])
            if len(childObj):
                childObj = sorted(childObj,key=lambda t: t.get_acronym().upper())
                for elem in childObj:
                    k = elem.getID()
                    submap.append(k)
                    submap += elem.get_submap_str()
        submap.append('<<')
        return submap

    # Looking UP
    def get_supermap_str(self):
        children = self.get_parents()
        submap = []                      
        submap.append('>>')
        if children and len (children) > 0:
            allObj =  self.config.findAll(self.get_type())
            childObj = []
            for k in children:
                if k and k in allObj.elements:
                    childObj.append(allObj.elements[k])
            if len(childObj):
                childObj = sorted(childObj,key=lambda t: t.get_acronym().upper())
                for elem in childObj:
                    k = elem.getID()
                    submap.append(k)
                    submap += elem.get_supermap_str()
        submap.append('<<')
        return submap

    def proposedMemberAcronym(self,configuration):
        prefix = self.fields['acronym']+u"_"

class GrUsage(Group):
    def __init__(self, config):
        Group.__init__(self, config)
        self.keyColumn = 'gu_id'

    def get_type(self):
        return 'gu'

    def get_class_acronym(self):
        return 'guse'

    def validate_form(self, data, configuration, lang):
        tmp = Group.validate_form(self, data, configuration, lang)
        if tmp == '':
            return True
        return tmp

    def set_value_from_data(self, data, c, user):
        super(GrUsage, self).set_value_from_data(data, c, user)
        self.fields['rank'] = data['rank']
        self.save(c, user)


class CheckPoint(Group):
    def __init__(self, config):
        Group.__init__(self, config)
        self.keyColumn = 'h_id'
        self.tm = []
        self.vm = []
        self.dm = []
        self.batches = []

    def get_type(self):
        return 'h'

    def get_class_acronym(self):
        return 'checkpoint'

    def validate_form(self, data, configuration, lang):
        tmp = Group.validate_form(self, data, configuration, lang)
        if tmp == '':
            return True
        return tmp

    def set_value_from_data(self, data, c, user):
        super(CheckPoint, self).set_value_from_data(data, c, user)
        self.fields['gr_id'] = data['recipe']
        self.fields['gu_id'] = data['usage']
        self.fields['rank'] = data['rank']
        if 'abstract' in data:
            self.fields['abstract'] = '1'
        else:
            self.fields['abstract'] = '0'
        self.save(c, user)

    def remove_tm(self, model):
        if model.fields['tm_id'] in self.tm:
            self.tm.remove(model.fields['tm_id'])

    def add_tm(self, model):
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
                    self.tm.insert(i, model.getID())
                    break
            if insert is False:
                self.tm.append(tm.getID())

    def remove_dm(self, model):
        if model.fields['dm_id'] in self.dm:
            self.dm.remove(model.fields['dm_id'])

    def add_dm(self, model):
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
                    self.dm.insert(i, model.getID())
                    break
            if insert is False:
                self.dm.append(model.getID())

    def remove_vm(self, model):
        if model.fields['vm_id'] in self.vm:
            self.vm.remove(model.fields['vm_id'])

    def add_vm(self, model):
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
                    self.vm.insert(i, model.getID())
                    break
            if insert is False:
                self.vm.append(model.getID())

    def get_model_sorted(self):
        listdm = self.get_hierarchy_dm([],self)
        listvm = self.get_hierarchy_vm([],self)
        listtm = self.get_hierarchy_tm([],self)
        tmp = []
        for e in listdm:
            tmp.append(self.config.AllManualDataModels.elements[e])
        for e in listvm:
            tmp.append(self.config.AllPouringModels.elements[e])
        for e in listtm:
            tmp.append(self.config.AllTransferModels.elements[e])
        tmp.sort(key=lambda x: int(x.fields['rank']), reverse=False)
        return tmp

    def get_local_model_sorted(self):
        tmp = []
        for e in self.dm:
            tmp.append(self.config.AllManualDataModels.elements[e])
        for e in self.vm:
            tmp.append(self.config.AllPouringModels.elements[e])
        for e in self.tm:
            tmp.append(self.config.AllTransferModels.elements[e])
        tmp.sort(key=lambda x: int(x.fields['rank']), reverse=False)
        return tmp

    def validate_control(self, data, lang):
        model = self.get_model_sorted()
        countdm = 1
        countvm = 1
        counttm = 1
        tmp = ''
        try:
            value = useful.date_to_ISO(data['time'])
        except:
            traceback.print_exc()
            tmp += self.config.getMessage('timerules',lang) + '\n'
        for m in model:
            type = m.get_type()
            if type == 'dm':
                try:
                    value = float(data['dm_value_'+unicode(countdm)])
                except:
                    tmp += self.config.getMessage('floatrules',lang) \
                            + ' '+data['dm_value_'+unicode(countdm)]+'\n'
                countdm += 1
            elif type == 'vm':
                try:
                    value = float(data['vm_quantity_'+unicode(countvm)])
                except:
                    tmp += self.config.getMessage('floatrules',lang) \
                           + ' '+data['vm_quantity_'+unicode(countvm)]+'\n'
                countvm += 1
        if tmp == '':
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
            tmp = None
            if type == 'dm':
                tmp = self.create_data(data, type, countdm)
                countdm += 1
            elif type == 'tm':
                tmp = self.create_data(data, type, counttm)
                counttm += 1
            elif type == 'vm':
                tmp = self.create_data(data, type, countvm)
                countvm += 1
            if tmp:
                currObject.set_value_from_data(tmp, self.config, user)
        type = data['batch'].split('_')[0]
        id = data['batch'].split('_')[1]
        self.write_control(type, id, user)
        self.config.get_object(type,id).add_checkpoint(self.getID(),data['time'])

    def create_data(self, data, type, count):
        batch = data['batch']
        time = data['time']
        tmp = {}
        tmp['time'] = time
        tmp['active'] = '1'
        tmp['h_id'] = self.getID()
        count = unicode(count)
        if type == 'dm':
            tmp['component'] = batch
            tmp['origin'] = data['dm_id_'+count]
            tmp['remark'] = data['dm_remark_'+count]
            tmp['measure'] = data['dm_measure_'+count]
            tmp['value'] = data['dm_value_'+count]
        elif type == 'tm':
            tmp['object'] = batch
            tmp['origin'] = data['tm_id_'+count]
            tmp['position'] = data['tm_position_'+count]
            tmp['remark'] = data['tm_remark_'+count]
        elif type == 'vm':
            tmp['origin'] = data['vm_id_'+count]
            if 'vm_src_'+count in data:
                tmp['src'] = data['vm_src_'+count]
                tmp['dest'] = batch.split('_')[1]
            else:
                tmp['dest'] = data['vm_dest_'+count]
                tmp['src'] = batch.split('_')[1]
            tmp['quantity'] = data['vm_quantity_'+count]
            tmp['remark'] = data['vm_remark_'+count]
        return tmp

    def write_control(self, type, id, user):
        with open(self.config.findAllFromObject(self).file_of_controls, "a") \
                as csvfile:
            tmpCode = {}
            tmpCode['begin'] = useful.now()
            tmpCode['h_id'] = self.getID()
            tmpCode['object_type'] = type
            tmpCode['object_id'] = id
            tmpCode["user"] = user.fields['u_id']
            writer = unicodecsv.DictWriter(csvfile,
                                           delimiter='\t',
                                           fieldnames=self.config
                                                          .findAllFromObject(self).fieldcontrols, encoding="utf-8")
            writer.writerow(tmpCode)

    def get_hierarchy_dm(self, list=None, group=None):
        if group == None:
            list = []
            group = self
        for e in group.dm:
            list.append(e)
        for e in group.parents:
            self.get_hierarchy_dm(list, self.config.AllCheckPoints.elements[e])
        return list

    def get_hierarchy_tm(self, list=None, group=None):
        if group == None:
            list = []
            group = self
        for e in group.tm:
            list.append(e)
        for e in group.parents:
            self.get_hierarchy_tm(list, self.config.AllCheckPoints.elements[e])
        return list

    def get_hierarchy_vm(self, list=None, group=None):
        if group == None:
            list = []
            group = self
        for e in group.vm:
            list.append(e)
        for e in group.parents:
            self.get_hierarchy_vm(list, self.config.AllCheckPoints.elements[e])
        return list

    def owns(self,type,id):
        elems = []
        if type == "dm":
            elems = self.get_hierarchy_dm([],self)
        elif type == "vm":
            elems = self.get_hierarchy_vm([],self)
        elif type == "tm":
            elems = self.get_hierarchy_tm([],self)
        return id in elems;

class GrRecipe(Group):
    def __init__(self, config):
        Group.__init__(self, config)
        self.keyColumn = 'gr_id'

    def get_type(self):
        return 'gr'

    def get_class_acronym(self):
        return 'grecipe'

    def get_quantity(self):
        return self.floats('basicqt')

    def get_total_cost(self):
        return self.floats('fixed_cost')+ (self.floats('cost')*self.floats('basicqt'))

    def validate_form(self, data, configuration, lang):
        tmp = super(GrRecipe, self).validate_form(data, configuration, lang)
        if tmp == '':
            return True
        return tmp

    def set_value_from_data(self, data, c, user):
        super(GrRecipe, self).set_value_from_data(data, c, user)
        self.fields['gu_id'] = data['usage']
        self.fields['basicqt'] = data['basicqt']
        self.fields['m_id'] = data['measure']
        self.fields['cost'] = data['cost']
        self.fields['fixed_cost'] = data['fixed_cost']
        self.fields['lifespan'] = data['lifespan']

        self.save(c, user)

    def proposedMemberAcronym(self,configuration):
        prefix = self.fields['acronym']+u"_"+useful.shortNow()+u"_"
        acro = configuration.AllBatches.findNextAcronym(prefix,len(prefix)+2,1)
        if acro:
            return acro
        else:
            return prefix

    def lifespan(self,c):
        if self.fields['lifespan']:
            return int(self.fields['lifespan'])
        else:
            for krecipe in self.parents:
                if krecipe in c.AllGrRecipe.elements:
                    recipe = c.AllGrRecipe.elements[krecipe]
                    days = recipe.lifespan(c)
                    if days:
                        return days
            return 0

class GrFunction(Group):
    def __init__(self, config):
        Group.__init__(self, config)
        self.keyColumn = 'gf_id'

    def get_type(self):
        return 'gf'

    def get_user_group(self):
        listusers = []
        for k, user in self.config.AllUsers.elements.items():
            if user.fields['gf_id'] in self.children \
                                        or user.fields['gf_id'] == self.fields['gf_id']:
                listusers.append(k)
        return listusers

    def get_class_acronym(self):
        return 'gfunction'

    def validate_form(self, data, configuration, lang):
        tmp = super(GrFunction, self).validate_form(data, configuration, lang)
        if tmp == '':
            return True
        return tmp

    def set_value_from_data(self, data, c, user):
        super(GrFunction, self).set_value_from_data(data, c, user)
        self.save(c, user)


class Place(ConfigurationObject):
    def __init__(self, config):
        ConfigurationObject.__init__(self)
        self.config = config

    def __str__(self):
        string = "\nPlace :"
        for field in self.fields:
            string = string + "\n" + field + " : " + self.fields[field]
        return string + "\n"

    def get_type(self):
        return 'p'

    def get_class_acronym(self):
        return 'place'

    def get_sensors_in_component(self, config):
        listSensor = []
        checklist = []
        checklist.append(['p', self.id])
        for k, v in config.AllEquipments.elements.items():
            transfer = v.get_last_transfer()
            if transfer is not None:
                transfer = config.AllTransfers.elements[transfer]
                if transfer.fields['cont_type'] == 'e' \
                        and transfer.fields['cont_id'] == self.id:
                    checklist.append(['e', k])
        for k, sensor in config.AllSensors.elements.items():
            for comp, id in checklist:
                if sensor.is_in_component(comp, id):
                    listSensor.append(k)
        return listSensor

    def isAlarmed(self,c):
        for kSensor,aSensor in c.AllSensors.elements.items():
            if aSensor.isAlarmed(c) and aSensor.is_in_component('p',self.id):
                return True
        return False

    def validate_form(self, data, configuration, lang):
        return super(Place, self).validate_form(data, configuration, lang)

    def set_value_from_data(self, data, c, user):
        super(Place, self).set_value_from_data(data, c, user)
        self.fields['colorgraph'] = data['colorgraph']
        self.fields['gu_id'] = data['group']
        self.save(c, user)

    def get_group(self):
        return self.fields['gu_id']

class AlarmLog(ConfigurationObject):

    def __init__(self):
        ConfigurationObject.__init__(self)

    def __str__(self):
        string = "\nAlarmLog :"
        for field in self.fields:
            string = string + "\n" + field + " : " + self.fields[field]
        return string + "\n"

    def isComplete(self):
        if self.fields['completedtime'] != '':
            return True
        return False

    def get_type(self):
        return 'al'

    def get_class_acronym(self):
        return 'alarmlog'

    def get_group(self):
        return self.fields['a_id']

    # WHAT is moved
    def get_source(self,config):
        if not self.fields['s_id']:
            return None
        if self.fields['s_type']:
            allObjs =config.findAll(self.fields['s_type'])
        else:
            allObjs = config.AllSensors
        return allObjs.get(self.fields['s_id'])

    # WHERE it is moved
    def get_component(self,config):
        if not self.fields['cont_id']:
            return None
        if self.fields['cont_type']:
            allObjs =config.findAll(self.fields['cont_type'])
            return allObjs.get(self.fields['cont_id'])
        return None

##        self.fieldnames = ['begin', 'al_id', 'cont_id', 'cont_type',
##                           's_id', 's_type', 'value', 'typealarm', 'a_id', 'begintime',
##                           'alarmtime', 'degree', 'completedtime', 'remark', 'active', 'user']

##    def validate_form(self, data, configuration, lang):
##        tmp = ''
##        try:
##            value = useful.date_to_ISO(data['begintime'])
##        except:
##            traceback.print_exc()
##            tmp += configuration.getMessage('timerules',lang) + '\n'
##
##        try:
##            aType = data['component'].split('_')[0]
##            anId = data['component'].split('_')[1]
##            if not configuration.is_component(aType):
##                tmp += configuration.getMessage('componentrules',lang) + ' '+data['component']+'\n'
##        except:
##            tmp += configuration.getMessage('componentrules',lang) + '\n'
##
##        if tmp == '':
##            return True
##        return tmp
##
##    def set_value_from_data(self, data, c, user):
##        #SUPER is NOT called, beware!
##        if self.fields['object_type'] != '' \
##                and self.fields['object_id'] != '':
##            c.get_object(self.fields['object_type'],self.fields['object_id']) \
##             .remove_data(self)
##        tmp = ['time', 'value', 'remark']
##        for elem in tmp:
##            self.fields[elem] = data[elem]
##        self.add_component(data['component'])
##        self.add_measure(data['measure'])
##        if 'h_id' in data:
##            self.fields['h_id'] = data['h_id']
##        else:
##            self.fields['h_id'] = ''
##        if 'active' in data:
##            self.fields['active'] = '1'
##        else:
##            self.fields['active'] = '0'
##        alarmCode = ""
##        if ('origin' in data) and data['origin']:
##            self.fields['dm_id'] = data['origin']
##            model = c.AllManualDataModels.elements[data['origin']]
##            typeAlarm, symbAlarm, self.colorAlarm,self.colorTextAlarm = self.getTypeAlarm(data['value'],model)
##            self.actualAlarm = typeAlarm
##            alarmCode = self.get_alarm(model);
##        if ('a_id' in data) and data['a_id']:
##            #TODO: Manual Alarm, not so "typical"
##            if not self.actualAlarm:
##                self.actualAlarm = "typical"
##            alarmCode = data['a_id']
##        if alarmCode and alarmCode in c.AllAlarms.elements:
##            self.fields['al_id'] = c.AllAlarms.elements[alarmCode].launch_alarm(self, c)
##        if self.isActive():
##            c.get_object(self.fields['object_type'],self.fields['object_id']) \
##             .add_data(self)
##        else:
##            c.get_object(self.fields['object_type'],self.fields['object_id']) \
##             .remove_data(self)
##        self.save(c, user)

class ExportData():
    def __init__(self, config, elem, cond, user):
        self.config = config
        self.fieldnames = ['timestamp', 'user', 'type', 'b_id', 'p_id', 'e_id',
                           'c_id', 'h_id', 'm_id', 'sensor', 'value', 'unit',
                           'category', 'duration', 'remark']
        self.history = []
        self.filename = os.path.join(DIR_DATA_CSV, "exportdata.csv")
        self.cond = cond
        self.elem = elem
        if elem.get_type() != 'b':
            self.batches = elem.get_batch_in_component(self.config)
        else:
            self.batches = []
            self.batches.append(self.elem)
        self.b = None
        self.user = user
        self.manualdata = []
        self.transfers = []
        self.pourings = []
        self.elements = []
        self.min = 99999999999
        self.max = -99999999999
        self.average = 0
        self.count = 0
        self.countt = 0

    def load_data(self):
        for d in self.b.manualdata:
            self.manualdata.append(self.config.AllManualData.elements[d])

    def load_transfers(self, component=None, begin=None, end=None):
        if component == None:
            self.transfers = []
            component = self.elem
            if len(component.transfers) > 0:
                begin = self.config.AllTransfers.elements[component.transfers[0]].getTimestamp()
                if len(component.transfers) > 1:
                    end = component.transfers[1]
                else:
                    end = useful.get_timestamp()
            else:
                return []
        tmpEND = end
        tmp = component.get_transfers_in_time_interval(begin, end)
        count = 0
        while count < len(tmp):
            begin = tmp[count].getTimestamp()
            if count < (len(tmp) - 1):
                end = tmp[count+1].getTimestamp()
            else:
                end = tmpEND
            tmpComponent = tmp[count].get_component(self.config)
            self.transfers.append(tmp[count])
            count += 1
            self.load_transfers(tmpComponent, begin, end)
        self.transfers.sort(key=lambda x: int(x.getTimestamp()), reverse=False)
        while self.transfers[0].fields['object_type'] != 'b':
            self.transfers.pop(0)
        return self.transfers

    def load_pourings(self):
        for t in self.b.destination:
            self.pourings.append(self.config.AllPourings.elements[t])
        for t in self.b.source:
            self.pourings.append(self.config.AllPourings.elements[t])

    def create_export(self):
        if self.elem.get_type() != 'b':
            if self.cond['manualdata'] is True:
                for data in self.elem.manualdata:
                    self.elements \
                        .append(self.transform_object_to_export_data(
                                self.config.AllManualData.elements[data]))
            if self.cond['transfer'] is True:
                for t in self.elem.transfers:
                    self.elements \
                        .append(self.transform_object_to_export_data(
                                self.config.AllTransfers.elements[t]))

        for self.b in self.batches:
            self.load_data()
            self.load_transfers()
            self.load_pourings()

            self.load_hierarchy()
            self.countt = 1

            bexport = self.transform_object_to_export_data(self.b)
            self.elements.append(bexport)
            count = 0
            while count < (len(self.history)):
                e = self.history[count]
                if e.get_type() == 't':
                    begin = e.getTimestamp()
                    if self.countt > (len(self.transfers)-1):
                        end = int(time.time())
                    else:
                        end = self.transfers[self.countt].getTimestamp()
                    self.countt += 1
                infos = None
                tmp = self.transform_object_to_export_data(e)
                if self.cond['manualdata'] is True and e.get_type() == 'd':
                    self.elements.append(tmp)
                elif self.cond['transfer'] is True and e.get_type() == 't':
                    tmp['duration'] = self.get_duration(begin, end)
                    self.elements.append(tmp)
                elif self.cond['pouring'] is True and e.get_type() == 'v':
                    self.elements.append(tmp)
                if e.get_type() == 't':
                    e = self.config.getObject(
                        e.fields['cont_id'], e.fields['cont_type'])
                    infos = e.get_all_in_component(self.config, begin, end, None)
                    lastSensor = e
                if infos is not None:
                    self.add_value_from_sensors(infos)
                count += 1

    def write_csv(self):
        with open(self.filename, 'w') as csvfile:
            csvfile.write(self.fieldnames[0])
            tmp = 1
            while tmp < len(self.fieldnames):
                csvfile.write('\t'+self.fieldnames[tmp])
                tmp = tmp + 1
            csvfile.write('\n')
        for e in self.elements:
            with open(self.filename, 'a') as csvfile:
                writer = unicodecsv.DictWriter(csvfile,
                                               delimiter="\t",
                                               fieldnames=self.fieldnames,
                                               encoding="utf-8")
                writer.writerow(e)

    def add_value_from_sensors(self, infos):
        for a in infos.keys():
            if a in self.config.AllSensors.elements:
                sensorDefinition = self.config.AllSensors.elements[a]
                self.min = 99999999999
                self.max = -99999999999
                self.average = 0.0
                timemin = ''
                timemax = ''
                self.count = 0
                if infos[a] is not None:
                    begin = infos[a][0][0]
                    for value in infos[a]:
                        tmp = value[1][0]
                        sensor = self.transform_object_to_export_data(sensorDefinition)
                        sensor['remark'] = ''
                        end = value[0]
                        sensor['timestamp'] = useful.timestamp_to_ISO(end)
                        sensor['value'] = export_float(tmp)
                        sensor['type'] = 'MES'
                        if tmp is not None:
                            tmp = float(value[1][0])
                            self.count += 1
                            self.average += tmp
                            if tmp < self.min:
                                self.min = tmp
                                timemin = end
                            if tmp > self.max:
                                self.max = tmp
                                timemax = end
                        # sensor['typevalue'] = 'DAT'
                        if self.cond['valuesensor'] is True:
                            self.elements.append(sensor)
                    if self.count > 0:
                        self.average /= self.count
                    if self.cond['specialvalue'] is True and self.count > 0:
                        sensor1 = self.transform_object_to_export_data(sensorDefinition)
                        sensor1['value'] = export_float(self.min)
                        # sensor1['typevalue'] = 'MIN'
                        sensor1['type'] = 'MIN'
                        sensor1['timestamp'] = useful.timestamp_to_ISO(timemin)
                        sensor1['remark'] = ''
                        self.elements.append(sensor1)
                        sensor2 = self.transform_object_to_export_data(sensorDefinition)
                        sensor2['value'] = export_float(self.max)
                        # sensor2['typevalue'] = 'MAX'
                        sensor2['type'] = 'MAX'
                        sensor2['timestamp'] = useful.timestamp_to_ISO(timemax)
                        sensor2['remark'] = ''
                        self.elements.append(sensor2)
                        sensor3 = self.transform_object_to_export_data(sensorDefinition)
                        sensor3['value'] = export_float(self.average)
                        # sensor3['typevalue'] = 'AVG'
                        sensor3['type'] = 'AVG'
                        sensor3['timestamp'] = useful.timestamp_to_ISO(end)
                        sensor3['duration'] = self.get_duration(begin, end)
                        sensor3['remark'] = ''
                        self.elements.append(sensor3)
                    if self.cond['alarm'] is True:
                        logs = self.config \
                                   .AllAlarmLogs \
                                   .get_logs_for_component(sensorDefinition, begin, end)
                        for log in logs:
                            tmp = self.transform_object_to_export_data(log)
                            self.elements.append(tmp)

    def load_hierarchy(self):
        self.history = []
        sum = len(self.manualdata) + len(self.transfers) + len(self.pourings)
        i = 0
        j = 0
        k = 0
        count = 0
        while count < sum:
            if i < len(self.manualdata):
                timed = self.manualdata[i].getTimestamp()
            else:
                timed = None

            if j < len(self.transfers):
                timet = self.transfers[j].getTimestamp()
            else:
                timet = None

            if k < len(self.pourings):
                timev = self.pourings[k].getTimestamp()
            else:
                timev = None

            if timed is not None:
                tmp = timed
                cond = 'd'
            elif timet is not None:
                tmp = timet
                cond = 't'
            elif timev is not None:
                tmp = timev
                cond = 'v'
            else:
                break

            if timet is not None:
                if timet < tmp:
                    cond = 't'
                    tmp = timet
            if timev is not None:
                if timev < tmp:
                    cond = 'v'
                    tmp = timev

            if cond == 'd':
                self.history.append(self.manualdata[i])
                i += 1
            elif cond == 't':
                self.history.append(self.transfers[j])
                j += 1
            elif cond == 'v':
                self.history.append(self.pourings[k])
                k += 1
            count += 1

    def get_all_in_component(self, component, begin, end, infos=None):
        if infos is None:
            infos = {}
        sensors = component.get_sensors_in_component(self.config)
        tmp = component.get_transfers_in_time_interval(begin, end)
        if len(tmp) > 0:
            for t in tmp:
                infos = self.get_all_in_component(
                    t.get_component(self.config), begin, end, infos)
        for a in sensors:
            infos[a] = self.config.AllSensors.elements[a].fetch(begin, end)
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
            tmp['timestamp'] = useful.date_to_ISO(elem.created)

        if elem.get_type() in 'bcpem':
            if elem.get_type() == 'b':
                tmp['timestamp'] = useful.date_to_ISO(elem.fields['time'])
                tmp['duration'] = self.get_duration(elem.getTimestamp(), useful.get_timestamp())
                tmp['unit'] = elem.get_unit(self.config)
                tmp['value'] = export_float(elem.get_quantity())

            if self.cond['acronym'] is True:
                tmp[elem.get_type()+'_id'] = elem.fields['acronym']
                if elem.get_type() == 'b':
                    tmp['m_id'] = elem.get_measure(self.config).fields['acronym']
            else:
                tmp[elem.get_type()+'_id'] = elem.getID()
                if elem.get_type() == 'b':
                    tmp['m_id'] = elem.fields['m_id']
            tmp['remark'] = elem.fields['remark']
            tmp['type'] = elem.get_type()
            if elem.get_type() == 'm':
                tmp['m_id'] = elem.getID()

        elif elem.get_type() == 's':
            if self.cond['acronym'] is True:
                if elem.fields['p_id'] != '':
                    tmp['p_id'] = self.config \
                                      .AllPlaces \
                                      .elements[elem.fields['p_id']] \
                                      .fields['acronym']
                else:
                    tmp['p_id'] = ''
                if elem.fields['e_id'] != '':
                    tmp['e_id'] = (self.config
                                       .AllEquipments
                                       .elements[elem.fields['e_id']]
                                       .fields['acronym'])
                else:
                    tmp['e_id'] = ''
                if elem.fields['c_id'] != '':
                    tmp['c_id'] = (self.config
                                       .AllContainers
                                       .elements[elem.fields['c_id']]
                                       .fields['acronym'])
                else:
                    tmp['c_id'] = ''
                tmp['sensor'] = elem.fields['acronym']
                tmp['m_id'] = elem.get_measure(self.config).fields['acronym']
            else:
                tmp['p_id'] = elem.fields['p_id']
                tmp['e_id'] = elem.fields['e_id']
                tmp['c_id'] = elem.fields['c_id']
                tmp['sensor'] = elem.fields['s_id']
                tmp['m_id'] = elem.fields['m_id']
            tmp['unit'] = elem.get_unit(self.config)
            tmp['remark'] = elem.fields['remark']

        elif elem.get_type() == 'al':
            sensor = (self.config
                          .AllSensors
                          .elements[elem.fields['s_id']])
            tmp['timestamp'] = useful.timestamp_to_ISO(elem.fields['begintime'])
            tmp['type'] = 'ALR'
            if self.cond['acronym'] is True:
                tmp[elem.fields['cont_type'] + '_id'] = self.config.get_object(elem.fields['cont_type'],elem.fields['cont_id']).fields['acronym']
                tmp['sensor'] = (self.config
                                     .AllSensors
                                     .elements[elem.fields['s_id']]
                                     .fields['acronym'])
                tmp['m_id'] = self.config.AllSensors.elements[elem.fields['s_id']].get_measure(self.config).fields['acronym']
            else:
                tmp[elem.fields['cont_type']+'_id'] = elem.fields['cont_id']
                tmp['sensor'] = elem.fields['s_id']
                tmp['m_id'] = elem.fields['m_id']
            tmp['duration'] = self.get_duration(int(elem.fields['begintime']), \
                                                useful.date_to_timestamp(elem.fields['begin']))
            tmp['category'] = elem.fields['degree']
            tmp['value'] = export_float(elem.fields['value'])
            tmp['unit'] = sensor.get_unit(self.config)

        elif elem.get_type() == 'd':
            tmp['type'] = 'MAN'
            if self.cond['acronym'] is True and elem.fields['h_id'] != '':
                tmp['h_id'] = (self.config
                                   .AllCheckPoints
                                   .elements[elem.fields['h_id']]
                                   .fields['acronym'])
            else:
                tmp['h_id'] = elem.fields['h_id']
            tmp['timestamp'] = useful.date_to_ISO(elem.fields['time'])
            if elem.fields['m_id'] != '':
                tmp['value'] = export_float(elem.get_quantity())
                tmp['unit'] = elem.get_unit(self.config)
                if self.cond['acronym'] is True:
                    tmp['m_id'] = elem.get_measure(self.config).fields['acronym']
                else:
                    tmp['m_id'] = elem.fields['m_id']
            if self.cond['acronym'] is True and elem.fields['m_id'] != '':
                tmp['m_id'] = elem.get_measure(self.config).fields['acronym']
                tmp[elem.fields['object_type']+'_id'] = self.config.get_object(elem.fields['object_type'],elem.fields['object_id']).fields['acronym']
            else:
                tmp['m_id'] = elem.fields['m_id']
                tmp[elem.fields['object_type']+'_id'] = elem.fields['object_id']
            tmp['remark'] = elem.fields['remark']
            if self.cond['acronym'] is True:
                tmp['user'] = (self.config
                                   .AllUsers
                                   .elements[elem.fields['user']]
                                   .fields['acronym'])
                tmp[elem.fields['object_type']+'_id'] = self.config.get_object(elem.fields['object_type'],elem.fields['object_id']).fields['acronym']
            else:
                tmp['user'] = elem.fields['user']
                tmp[elem.fields['object_type']+'_id'] = elem.fields['object_id']

        elif elem.get_type() == 't':
            tmp['type'] = 'TRF'
            if self.cond['acronym'] is True and elem.fields['h_id'] != '':
                tmp['h_id'] = (self.config
                                   .AllCheckPoints
                                   .elements[elem.fields['h_id']]
                                   .fields['acronym'])
            else:
                tmp['h_id'] = elem.fields['h_id']

            tmp['timestamp'] = useful.date_to_ISO(elem.fields['time'])
            tmp['remark'] = elem.fields['remark']
            if self.cond['acronym'] is True:
                tmp[elem.fields['cont_type']+'_id'] = self.config.get_object(elem.fields['cont_type'],elem.fields['cont_id']).fields['acronym']
                if elem.fields['object_type'] != 'b':
                    tmp[elem.fields['object_type']+'_id'] = self.config.get_object(elem.fields['object_type'],elem.fields['object_id']).fields['acronym']
                elemtmp = elem.get_component(self.config).get_position_on_time(
                    self.config, elem.fields['time'])
                while elemtmp is not None:
                    tmp[elemtmp.fields['cont_type']+'_id'] = self.config.get_object(elemtmp.fields['cont_type'],elemtmp.fields['cont_id']).fields['acronym']
                    elemtmp = elemtmp.get_component(self.config).get_position_on_time(
                        self.config, elemtmp.fields['time'])
            else:
                tmp[elem.fields['cont_type']+'_id'] = elem.fields['cont_id']
                if elem.fields['object_type'] != 'b':
                    tmp[elem.fields['object_type'] + '_id'] = elem.fields['object_id']
                elemtmp = elem.get_component(self.config).get_position_on_time(
                    self.config, elem.fields['time'])
                while elemtmp is not None:
                    tmp[elemtmp.fields['cont_type'] +
                        '_id'] = elem.fields['object_id']
                    elemtmp = elemtmp.get_component(self.config).get_position_on_time(
                        self.config, elemtmp.fields['time'])

        elif elem.get_type() == 'v':
            if self.cond['acronym'] is True and elem.fields['h_id'] != '':
                tmp['h_id'] = (self.config
                                   .AllCheckPoints
                                   .elements[elem.fields['h_id']]
                                   .fields['acronym'])
            else:
                tmp['h_id'] = elem.fields['h_id']
            tmp['timestamp'] = useful.date_to_ISO(elem.fields['time'])
            tmp['remark'] = elem.fields['remark']
            tmp['value'] = export_float(elem.get_quantity())
            tmp['unit'] = elem.get_unit(self.config)
            if elem.fields['src'] == self.b.getID():
                tmp['type'] += 'OUT'
                if self.cond['acronym'] is True:
                    tmp['b_id'] = (self.config
                                       .AllBatches
                                       .elements[elem.fields['dest']]
                                       .fields['acronym'])
                    tmp['m_id'] = elem.get_measure(self.config).fields['acronym']
                else:
                    tmp['b_id'] = elem.fields['dest']
                    tmp['m_id'] = elem.fields['m_id']
            else:
                tmp['type'] += 'INP'
                if self.cond['acronym'] is True:
                    tmp['b_id'] = (self.config
                                       .AllBatches
                                       .elements[elem.fields['src']]
                                       .fields['acronym'])
                    tmp['m_id'] = elem.get_measure(self.config).fields['acronym']
                else:
                    tmp['b_id'] = elem.fields['src']
                    tmp['m_id'] = elem.fields['m_id']
        return tmp 

    def get_duration(self, begin, end):
        #timestamp = int(end) - int(begin)
        #return useful.timestamp_to_time(timestamp)
        return int(end) - int(begin)

    def get_new_line(self):
        tmp = {}
        tmp['timestamp'] = ''
        tmp['user'] = ''
        tmp['type'] = ''
        tmp['b_id'] = ''
        tmp['p_id'] = ''
        tmp['e_id'] = ''
        tmp['c_id'] = ''
        tmp['h_id'] = ''
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

    def __str__(self):
        string = "\nHalfling :"
        for field in self.fields:
            string = string + "\n" + field + " : " + self.fields[field]
        return string + "\n"

    def get_type(self):
        return 'halfling'

    def getHalfling(self, supp_classes):
        return '<span class="halflings halflings-'+self.fields['glyphname']+supp_classes+'"></span>'

    def get_class_acronym(self):
        return 'halfling'


class Alarm(ConfigurationObject):

    def __init__(self):
        ConfigurationObject.__init__(self)

    def __str__(self):
        string = "\nAlarm :"
        for field in self.fields:
            string = string + "\n" + field + " : " + self.fields[field]
        return string + "\n"

    def get_type(self):
        return 'a'

    def validate_form(self, data, configuration, lang):
        tmp = super(Alarm, self).validate_form(data, configuration, lang)
        return tmp

    def set_value_from_data(self, data, c, user):
        super(Alarm, self).set_value_from_data(data, c, user)
        tmp = alarm_fields_for_groups + ['relay1', 'relay2']
        for elem in tmp:
            self.fields[elem] = data[elem]
        self.save(c, user)

    def get_alarm_message(self, alarmedObject, config, lang, saveit):
        newFields = {}
        newFields['s_id'] = alarmedObject.getID()
        newFields['s_type'] = alarmedObject.get_type()
        newFields['a_id'] = self.getID()
        newFields['alarmtime'] = useful.now()
        newFields['user'] = alarmedObject.fields['user']
        newFields['remark'] = ''
        newFields['active'] = '1'
        specmess = self.getName(lang)
        if alarmedObject.get_type() == 's':
            mess = config.getMessage('alarmmessage',lang)
            cpe = ''
            elem = ''
            if not alarmedObject.fields['p_id'] == '':
                cpe = config.getMessage('place',lang)
                elem = config.AllPlaces.elements[alarmedObject.fields['p_id']]
                newFields['cont_type'] = 'p'
            elif not alarmedObject.fields['e_id'] == '':
                cpe = config.getMessage('equipment',lang)
                elem = config.AllEquipments.elements[alarmedObject.fields['e_id']]
                newFields['cont_type'] = 'e'
            elif not alarmedObject.fields['c_id'] == '':
                cpe = config.getMessage('container',lang)
                elem = config.AllContainers.elements[alarmedObject.fields['c_id']]
                newFields['cont_type'] = 'c'
            newFields['cont_id'] = elem.getID()
            newFields['value'] = unicode(alarmedObject.lastvalue)
            newFields['begintime'] = alarmedObject.time
            newFields['typealarm'] = unicode(alarmedObject.actualAlarm)
            newFields['degree'] = unicode(alarmedObject.degreeAlarm)
            newFields['remark'] = unicode.format(mess,
                                  config.HardConfig.hostname,
                                  specmess,
                                  cpe,
                                  elem.getName(lang),
                                  elem.fields['acronym'],
                                  alarmedObject.getName(lang),
                                  alarmedObject.fields['acronym'],
                                  unicode(alarmedObject.lastvalue),
                                  alarmedObject.actualAlarm,
                                  alarmedObject.time,
                                  unicode(alarmedObject.degreeAlarm))
        elif alarmedObject.get_type() == 'd':
            mess = config.getMessage('alarmmanual',lang)
            elem = config.get_object(
                alarmedObject.fields['object_type'],alarmedObject.fields['object_id'])
            name = config.getMessage(elem.get_class_acronym(),lang)
            unit_measure = alarmedObject.get_unit(config)
            newFields['begintime'] = alarmedObject.fields['time']
            newFields['cont_type'] = elem.get_type()
            newFields['cont_id'] = elem.getID()
            newFields['value'] = unicode(alarmedObject.fields['value'])
            newFields['typealarm'] = unicode(alarmedObject.actualAlarm)
            newFields['degree'] = '2'
            newFields['remark'] = unicode.format(mess,
                                  config.HardConfig.hostname,
                                  specmess,
                                  name,
                                  elem.getName(lang),
                                  elem.fields['acronym'],
                                  unicode(alarmedObject.fields['value']),
                                  unit_measure,
                                  alarmedObject.fields['remark'],
                                  alarmedObject.fields['time'])
        elif alarmedObject.get_type() == 'v':
            mess = config.getMessage('alarmpouring',lang)
            elemid = ''
            elemin = None
            if alarmedObject.fields['src']:
                elemid = alarmedObject.fields['src']
                elemin = config.AllBatches.elements[elemid]
            elemout = None
            if alarmedObject.fields['dest']:
                elemid = alarmedObject.fields['dest']
                elemout = config.AllBatches.elements[elemid]
            unit_measure = alarmedObject.get_unit(config)
            newFields['begintime'] = alarmedObject.fields['time']
            newFields['cont_type'] = 'b'
            newFields['cont_id'] = elemid
            newFields['value'] = unicode(alarmedObject.get_quantity())
            #TODO: check quantities and automate alarm launch...
            newFields['typealarm'] = 'typical'
            newFields['degree'] = '2'
            newFields['remark'] = unicode.format(mess,
                                  config.HardConfig.hostname,
                                  specmess,
                                  elemout.getName(lang),
                                  elemout.fields['acronym'],
                                  elemin.getName(lang),
                                  elemin.fields['acronym'],
                                  unicode(alarmedObject.get_quantity()),
                                  unit_measure,
                                  alarmedObject.fields['remark'],
                                  alarmedObject.fields['time'])
        if saveit:
            currObject = config.AllAlarmLogs.createObject()
            currObject.fields.update(newFields)
            currObject.save(config)        
            return currObject.fields
        else:
            return newFields

    def get_alarm_title(self, alarmedObject, config, lang):
        if alarmedObject.get_type() == 's':
            title = config.getMessage('alarmtitle',lang)
            code = ''
            equal = ''
            if alarmedObject.actualAlarm == 'minmin':
                code = '---'
                equal = '<'
            elif alarmedObject.actualAlarm == 'min':
                code = '-'
                equal = '<'
            elif alarmedObject.actualAlarm == 'max':
                code = '+'
                equal = '>'
            elif alarmedObject.actualAlarm == 'maxmax':
                code = '+++'
                equal = '>'
            elif alarmedObject.actualAlarm == 'none':
                code = '???'
                equal = '>'
            return unicode.format(title,
                                  code,
                                  unicode(alarmedObject.degreeAlarm),
                                  alarmedObject.fields['acronym'],
                                  unicode(alarmedObject.lastvalue),
                                  equal,
                                  alarmedObject.fields[alarmedObject.actualAlarm],
                                  alarmedObject.get_unit(config),
                                  alarmedObject.getName(lang))
        elif alarmedObject.get_type() == 'd':
            title = config.getMessage('alarmmanualtitle',lang)
            elem = config.get_object(
                alarmedObject.fields['object_type'],alarmedObject.fields['object_id'])
            unit_measure = alarmedObject.get_unit(config)
            return unicode.format(title,
                                  alarmedObject.fields['value'],
                                  unit_measure,
                                  elem.getName(lang))
        #TODO: timed transfers...
        elif alarmedObject.get_type() == 'v':
            title = config.getMessage('alarmpouringtitle',lang)
            elemin = config.AllBatches.elements[alarmedObject.fields['src']]
            elemout = config.AllBatches.elements[alarmedObject.fields['dest']]
            return unicode.format(title, elemout.fields['acronym'], elemout.getName(lang), elemin.fields['acronym'], elemin.getName(lang))

    def alarm_by_email(self, alarmedObject, e_mail, config):
        alid = ""
        if (e_mail != '') and e_mail in config.AllGrFunction.elements:
            userlist = config.AllGrFunction.elements[e_mail].get_user_group()
            first = True
            for user in userlist:
                lang = config.AllUsers.elements[user].fields['language']
                allog = self.get_alarm_message(alarmedObject, config, lang, first)
                if first:
                    alid = allog['al_id']
                title = self.get_alarm_title(alarmedObject, config, lang)
                useful.send_email(config.AllUsers
                                        .elements[user].fields['mail'],
                                        title,
                                        allog['remark'])
                first = False
        return alid
        
    def launch_alarm(self, alarmedObject, config):
        alid = ""
        if alarmedObject.get_type() == 's':
            level = alarmedObject.degreeAlarm
            if level == 1:
                alid = self.alarm_by_email(alarmedObject, self.fields['o_email1'], config)
            elif level == 2:
                alid = self.alarm_by_email(alarmedObject, self.fields['o_email2'], config)
        elif alarmedObject.get_type() == 'd':
            alid = self.alarm_by_email(alarmedObject, self.fields['o_email2'], config)
##        elif alarmedObject.get_type() == 't':
##            alid = self.alarm_by_email(alarmedObject, self.fields['o_email2'], config)
        elif alarmedObject.get_type() == 'v':
            alid = self.alarm_by_email(alarmedObject, self.fields['o_email2'], config)
        return alid

    def get_user_groups(self,model=None):
        groups = []
        for gr in alarm_fields_for_groups:
            if not self.fields[gr] in groups:
                groups.append(self.fields[gr])
        return groups

    def get_class_acronym(self):
        return 'alarm'


class Measure(ConfigurationObject):

    def __init__(self):
        ConfigurationObject.__init__(self)
        self.sensors = sets.Set()

    def __str__(self):
        string = "\nMeasure :"
        for field in self.fields:
            string = string + "\n" + field + " : " + self.fields[field]
        return string + "\n"

    def get_html_step(self):
        step = self.fields['step']
        try:
            step_dec = {'-3':'1000', '-2':'100', '-1':'10', '0':'1', '1':'0.1',
                        '2':'0.01', '3':'0.001', '4':'0.0001', '5':'0.00001',
                        '6':'0.000001'}[step]
        except:
            step_dec = 'any'
        return step_dec

    def integers_count(self):
        step = self.fields['step']
        if not self.fields['min']:
            return 0
        if not self.fields['max']:
            return 0
        if not step or step=='0': # one by one
            return int(self.fields['max'])-int(self.fields['min']) + 1
        else:
            return 0
        
    def valuesRange(self):
        step = self.get_html_step()
        if step != 'any':
            if self.fields['min'] and self.fields['max']:
                step = int(step)
                i = int(self.fields['min'])
                end = int(self.fields['max'])
                while i <= end:
                    yield i
                    i+=step
    
    def get_select_str(self, lang):
        acr = self.fields['acronym']
        name = self.getName(lang)
        min = self.fields['min']
        max = self.fields['max']
        unit = self.fields['unit']
        
        return(unicode(acr) + ' - '
                        + name
                        + ': '
                        + min 
                        + u' ±'
                        + self.get_html_step()
                        + ' <= '
                        + max
                        + ' '
                        + unit)

    def get_type(self):
        return 'm'

    def get_class_acronym(self):
        return 'measure'

    def get_sensors_in_component(self, config):
        listSensor = []
        for k, sensor in config.AllSensors.elements.items():
            if sensor.is_in_component('m', self.id):
                listSensor.append(k)
        return listSensor

    def validate_form(self, data, configuration, lang):
        tmp = super(Measure, self).validate_form(data, configuration, lang)
        if tmp is True:
            tmp = ''
        try:
            if 'formula' in data and len(data['formula']) > 0:
                value = 1
                owData = unicode(eval(data['formula']))
                value = 0
                owData = unicode(eval(data['formula']))
        except:
            tmp += configuration.getMessage('formularules',lang) + '\n'

        try:
            if not len(data['unit']) > 0:
                tmp += configuration.getMessage('unitrules',lang) + '\n'
        except:
            tmp += configuration.getMessage('unitrules',lang) + '\n'

        valueMin = 0.0
        try:
            if not len(data['min']) > 0:
                tmp += configuration.getMessage('minrules',lang) + '\n'
            else:
                valueMin = float(data['min'])
        except:
            tmp += configuration.getMessage('minrules',lang) + '\n'

        try:
            if not len(data['max']) > 0:
                tmp += configuration.getMessage('maxrules',lang) + '\n'
            else:
                valueMax = float(data['max'])
                if valueMax < valueMin:
                    tmp += configuration.getMessage('maxrules',lang) + '\n'
        except:
            tmp += configuration.getMessage('maxrules',lang) + '\n'
        
        try:
            if not len(data['step']) > 0:
                tmp += configuration.getMessage('steprules',lang) + '\n'
            else:
                value = int(data['step'])
        except ValueError:
            tmp += configuration.getMessage('steprules',lang) + '\n'

        if tmp == '':
            return True
        return tmp

    def set_value_from_data(self, data, c, user):
        super(Measure, self).set_value_from_data(data, c, user)
        tmp = ['unit','min','max','step']
        for elem in tmp:
            self.fields[elem] = data[elem]
        self.save(c, user)

    def get_measure(self,c):
	return self;

    def get_unit(self,c):
        return self.fields['unit']
        
class Sensor(AlarmingObject):
    def __init__(self):
        AlarmingObject.__init__(self)

    def __str__(self):
        string = "\nSensor :"
        for field in self.fields:
            string = string + "\n" + field + \
                " : " + unicode(self.fields[field])
        string = string + ' Actual Alarm : ' + self.actualAlarm
        string = string + ' Count Actual : ' + unicode(self.countActual)
        string = string + ' Degree Alarm : ' + unicode(self.degreeAlarm)
        return string + "\n"

    def get_type(self):
        return 's'

    def get_class_acronym(self):
        return 'sensor'

    def get_quantity(self):
        if self.lastvalue is None:
            return 0.0
        return self.lastvalue

    def getRRDName(self):
        name = 's_' + self.id
        name += '.rrd'
        return name

    def add_component(self, data):
        tmp = data.split('_')
        typeComponent = tmp[-2][-1]
        if typeComponent == 'p':
            self.fields['p_id'] = tmp[-1]
            self.fields['e_id'] = ''
            self.fields['c_id'] = ''
        elif typeComponent == 'c':
            self.fields['c_id'] = tmp[-1]
            self.fields['e_id'] = ''
            self.fields['p_id'] = ''
        elif typeComponent == 'e':
            self.fields['e_id'] = tmp[-1]
            self.fields['p_id'] = ''
            self.fields['c_id'] = ''
        elif typeComponent == 'm':
            self.fields['m_id'] = tmp[-1]

    def add_measure(self, data):
        tmp = data.split('_')
        self.fields['m_id'] = tmp[-1]

    def add_phase(self, data):
        self.fields['h_id'] = data

    def nextAlarm(self, config, now, no_change):
        alid = ""
        if not no_change: # Alarm just changed !
            self.degreeAlarm = 0
        if self.degreeAlarm == 0:
            self.degreeAlarm = 1
            self.countAlarm = 0
            self.time = useful.timestamp_to_date(now)
            alarmCode = self.get_alarm()
            if int(self.floats('lapse1')) == 0:
                if alarmCode and alarmCode in config.AllAlarms.elements:
                    alid = config.AllAlarms.elements[alarmCode].launch_alarm(self, config)
                self.degreeAlarm = 2
        else:
            self.countAlarm = self.countAlarm + 1
            alarmCode = self.get_alarm()
            if self.degreeAlarm == 1 \
                    and self.countAlarm >= int(self.fields['lapse1']):
                if alarmCode and alarmCode in config.AllAlarms.elements:
                    alid = config.AllAlarms.elements[alarmCode].launch_alarm(self, config)
                self.degreeAlarm = 2
                self.countAlarm = 0
            elif self.degreeAlarm == 2 \
                    and self.countAlarm >= int(self.fields['lapse2']):
                if alarmCode and alarmCode in config.AllAlarms.elements:
                    alid = config.AllAlarms \
                        .elements[alarmCode].launch_alarm(self, config)
                self.degreeAlarm = 3
                self.countAlarm = 0
            elif self.degreeAlarm == 3 \
                    and self.countAlarm >= int(self.fields['lapse3']):
                if alarmCode and alarmCode in config.AllAlarms.elements:
                    alid = config.AllAlarms.elements[alarmCode].launch_alarm(self, config)
                self.degreeAlarm = 4 # Do nothing after this!
        print 'Alarm #'+alid+' ['+self.actualAlarm+'] level '+unicode(self.degreeAlarm)+' for ' + self.__repr__()

    def update(self, now, value, config):
        self.lastvalue = value
        self.updateRRD(now, value)

        minutes = int(now / 60)
        # GMT + DST
        hours = (int(minutes / 60) % 24)+100 + 2
        minutes = (minutes % 60)+100
        strnow = unicode(hours)[1:3]+":"+unicode(minutes)[1:3]
        if config.screen is not None:
            pos = config.screen.show(config.screen.begScreen, strnow)
            pos = config.screen.showBW(pos+2, self.get_acronym())
            pos = (config.screen
                         .show(pos+2,
                               unicode(round(float(value), 1))))
            unit_measure = self.get_unit(config)
            if unit_measure:
                pos = config.screen.show(pos, unit_measure)

        prvAlarm = self.actualAlarm
        typeAlarm, symbAlarm, self.colorAlarm,self.colorTextAlarm = self.getTypeAlarm(value)
##        if typeAlarm == 'typical':
##            self.setTypicalAlarm()
##        else:
##            if not ((typeAlarm == 'min' and self.actualAlarm == 'minmin')
##                    or (typeAlarm == 'max'
##                                and self.actualAlarm == 'maxmax')):
        self.actualAlarm = typeAlarm
        self.nextAlarm(config, now, prvAlarm == self.actualAlarm)

    def updateRRD(self, now, value):
        value = float(value)
        print self.getRRDName() + " " + useful.timestamp_to_ISO(now) +"."+ unicode(now)+"="+ unicode(value)
        rrdtool.update(str(DIR_RRD + self.getRRDName()), '%d:%f' % (now, value))

    def fetchRRD(self,period=None):
        filename = str(DIR_RRD + self.getRRDName())
        
        start = "end-1month"
        if period:
            if period == "300":
                start ="end-360sdays"
            elif period == "1800":
                start = "end-5years"
            result = rrdtool.fetch(filename, 'AVERAGE',"-s",start,"-r",str(period) )
        else:    
            result = rrdtool.fetch(filename, 'LAST',"-s",start )
        start,end,step = result[0]
        rows = result[2]
        out = u""
        for a_value in rows:
            if a_value[0]:
                a_date = datetime.datetime.fromtimestamp(start)
                out += a_date.isoformat(sep=' ') + u"\t" + export_float(a_value[0]) + u"\n"
            start += step
        return out

    def createRRD(self):
        name = re.sub('[^\w]+', '', self.fields['acronym'])
        now = str(int(time.time())-60)
        if self.fields['channel'] != 'radio':
            data_sources = str('DS:'+name+':GAUGE:120:U:U')
            rrdtool.create(str(DIR_RRD+self.getRRDName()),
                           "--step", "60",
                           '--start', now,
                           data_sources,
                           'RRA:LAST:0.5:1:43200',
                           'RRA:AVERAGE:0.5:5:103680',
                           'RRA:AVERAGE:0.5:30:86400')
        elif self.fields['channel'] == 'radio':
            data_sources = str('DS:'+name+':GAUGE:360:U:U')
            rrdtool.create(str(DIR_RRD+self.getRRDName()),
                           "--step", "180",
                           '--start', now,
                           data_sources,
                           'RRA:LAST:0.5:1:14400',
                           'RRA:AVERAGE:0.5:5:34560',
                           'RRA:AVERAGE:0.5:30:28800')
    
    def get_mesure_humidity_campbell(self, config):
        input = config.HardConfig.inputs[self.fields['channel']]
        input_device = config.HardConfig.devices[input['device']]
        try:
            output = config.HardConfig.outputs[input['poweroutput']]
            output_device = config.HardConfig.devices[output['device']]
        except IOError:
            print('Unable to control output_device!' + ' channel : '
                                                     + self.fields['channel']
                                                     + ', i2c address : '
                                                     + device['i2c'])
            return None
        try:
            output_gpio = abe_iopi.IOPi(int(output_device['i2c'], 16))
            output_gpio.set_pin_direction(int(output['channel']), 0)
            adc = abe_adcpi.ADCPi(int(input_device['i2c'], 16),
                                  int(input_device['i2c'], 16) + 1,
                                  int(input['resolution']))
        except IOError:
            print('Unable to read sensor !' + ' channel : '
                                            + self.fields['channel']
                                            + ', i2c address : '
                                            + device['i2c'])
            return None
# TODO: manage invertion for output
        # Stimulate
        output_gpio.write_pin(int(output['channel']), 1)
        time.sleep(int(input['delayms'])*0.001)
        
        output_val = adc.read_voltage(int(input['channel']))
        # End stimulation
        output_gpio.write_pin(int(output['channel']), 0)
        return output_val
    
    def sanitize_reading(self, config, value):
        '''
        Rounds to the value of 'step'.
        If outside of 'min' - 'max', returns None
        '''
        if type(value) not in (float, int, long, bool):
            print('Received non number sensor reding for channel '
                  + self.fields['channel'] + '. Ignoring.')
            return None
        measure = self.get_measure(config)
        minimum = int(measure.fields['min'])
        maximum = int(measure.fields['max'])
        step = int(measure.fields['step'])
       
        if (minimum <= value <= maximum):
            return round(value, step)
        else:
            print('Ignoring value of ' + self.fields['channel'] + ' with value '
                + unicode(value) + ' because it is out of bounds')
            return None
         
    def get_value_sensor(self, config, cache=None):
        def parse_atmos_data(self, input):
            '''
            Given a single string '+a+b-c+d', returns ['+a','+b','-c','+d']
            Used to parse the data returned from the Atmos41 weather station
            '''
            return reduce(lambda acc, elem:
                                acc[:-1] + [acc[-1] + elem]
                                if elem != '+' and elem != '-'
                                else acc + [elem],
                                    re.split("([+,-])", input.strip())[1:], [])
        
        output_val = None
        debugging = u""
        if self.fields['channel'] == 'wire':
            try:
                sensorAdress = u'/' + \
                    unicode(self.fields['sensor'])+u'/' + \
                    unicode(self.fields['subsensor'])
                output_val = float(config.owproxy.read(sensorAdress))
            except:
                debugging = (u"Device=" + sensorAdress
                                        + u", Message="
                                        + traceback.format_exc())
        elif self.fields['channel'] == 'radio':
            # Look at RadioThread
            pass
        elif self.fields['channel'] == 'cputemp':
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') \
                    as sensorfile:
                info = sensorfile.read()
                output_val = float(info)/1000.0
        elif self.fields['channel'] == 'http':
            url = self.fields['sensor']
            code = 0
            info = cache
            if info is not None:
                try:
                    output_val = eval(self.fields['subsensor'])
                except:
                    debugging = (u"URL=" + url
                                         + u", code="
                                         + unicode(code)
                                         + u", Response="
                                         + unicode(info)
                                         + u", Subsensor="
                                         + self.fields['subsensor']
                                         + u", Message="
                                         + traceback.format_exc())
                    traceback.print_exc()
            else:
                sensorfile = None
                try: #urlopen not usable with "with"
                    sensorfile = urllib2.urlopen(self.fields['sensor'], None, 20)
                    info = sensorfile.read(80000)
                    cache = info
                    output_val = eval(self.fields['subsensor'])
                except:
                    debugging = u"URL="+(url if url else "")+u", code=" + \
                        (unicode(code) if code else "")+u", Response="+(info if info else "") + \
                        u", Message="+traceback.format_exc()
                if sensorfile:
                    sensorfile.close()
        elif self.fields['channel'] == 'json':
            url = self.fields['sensor']
            code = 0
            info = cache
            if info is not None:
                try:
                    output_val = eval(self.fields['subsensor'])
                except:
                    debugging = (u"URL=" + url
                                         + u", code="
                                         + unicode(code)
                                         + u", Response="
                                         + unicode(info)
                                         + u", Subsensor="
                                         + self.fields['subsensor']
                                         + u", Message="
                                         + traceback.format_exc())
                    traceback.print_exc()
            else:
                sensorfile = None
                try: # urlopen not compatible with "with"
                    sensorfile = urllib2.urlopen(self.fields['sensor'], None, 20)
                    #print sensorfile.getcode()
                    info = sensorfile.read()
                    info = json.loads(info)
                    cache = info
                    output_val = eval(self.fields['subsensor'])
                except:
                    debugging = (u"URL=" + (url if url else "")
                                         + u", code="
                                         + (unicode(code) if code else "")
                                         + u", Response="
                                         + (unicode(info) if info else "")
                                         + u", Subsensor="
                                         + (self.fields['subsensor'] if self.fields['subsensor'] else "")
                                         + u", Message="
                                         + traceback.format_exc())
                if sensorfile:
                    sensorfile.close()
        elif self.fields['channel'] == 'system':
            try:
                sensorAdress = self.fields['sensor']
                with open(sensorAdress, 'r') as sensorfile:
                    info = sensorfile.read()
                    output_val = eval(self.fields['subsensor'])
            except:
                debugging = u"Device="+sensorAdress+u", field=" + \
                    self.fields['subsensor']+u", data=" + \
                    unicode(info)+u", Message="+traceback.format_exc()
        elif self.fields['channel'] == 'battery':
            input = config.HardConfig.inputs[self.fields['channel']]
            device = config.HardConfig.devices[input['device']]
            if device['install'] == "mcp3423":
                try:
                    adc = abe_mcp3423.ADCPi(int(device['i2c'], 16),
                                          int(input['resolution']))
                    output_val = adc.read_voltage(int(input['channel']))
                except IOError:
                    print('Unable to read sensor !' + ' channel : '
                                                    + self.fields['channel']
                                                    + ', i2c address : '
                                                    + device['i2c'])
            elif device['install'] == "abe_expanderpi":
                adc = abe_expanderpi.ADC()
                output_val = adc.read_adc_voltage(int(input['channel']), 0)
                adc.close()
            else:
                print("Error : device.install : "
                      + device.install
                      + " not supported for type battery.")
        elif self.fields['channel'].startswith('lightsensor'):
            input = config.HardConfig.inputs[self.fields['channel']]
            device = config.HardConfig.devices[input['device']]
            try:    
                adc = abe_mcp3424.ADCDifferentialPi(int(device['i2c'], 16),
                                                    int(device['i2c'], 16) + 1,
                                                    int(input['resolution']))
                adc.set_pga(int(device['amplification']))
                output_val = adc.read_voltage(int(input['channel']))
            except IOError:
                print('Unable to read sensor !' + ' channel : '
                                                + self.fields['channel']
                                                + ', i2c address : '
                                                + device['i2c'])
        elif self.fields['channel'].startswith('humiditysensor'):
            output_val = self.get_mesure_humidity_campbell(config)
        elif self.fields['channel'] == 'atmos41':
            input = config.HardConfig.inputs[self.fields['channel']]
	    if cache is [] or cache is None :
                try:
                    ser = serial.Serial(input['serialport'],
                                        baudrate=9600,
                                        timeout=10)
                    time.sleep(2.5) # Leave some time to initialize
                    ser.write(input['sdiaddress'].encode() + b'R0!')
                    cache = parse_atmos_data(self, ser.readline())
                except serial.SerialException:
                    print('Tried to read several times back to back ?')
                    raise
                finally:
                    if ser:
                        ser.close()
            try:
                output_val = float(cache[int(self.fields['subsensor'])])
            except ValueError:
                print('Subsensor should be a number')
            except IndexError:
                print('Subsensor for atmos is out of range: '
                      + self.fields['subsensor']
                      + '. Range starts at 0')
        else:
            print('Error: no sensor channel for ' + self.fields['channel'])
            return None, None
       
        if (debugging != ''):
            print(debugging) 
        try:
            assert output_val != None
        except AssertionError:
            if self.fields['channel'] != 'radio':
                print("output_val has not been set for channel: "
                      + self.fields['channel']
                      + '. Ignoring.')
            return None, None
        else:
            try:
                value = float(output_val)
                if self.fields['formula']:
                    output_val = float(eval(self.fields['formula']))
                else:
                    output_val = value
            except:
                print(u"Device="+self.fields['sensor']+u" / "+self.fields['subsensor'] + \
                    u", Formula="+self.fields['formula'] + \
                    u", Message="+traceback.format_exc() )
            return self.sanitize_reading(config, output_val), cache
        return None, None

    def count_logs(self,c):
        count = 0
        sID = self.getID()
        for kal,e in c.AllAlarmLogs.elements.items():
            if (sID == e.fields['s_id']) and ( (e.fields['s_type'] == 's') or (e.fields['s_type'] == '') ):
                count += 1
        return count

    def isAlarmed(self,c):
        return self.actualAlarm != 'typical'

    def is_in_component(self, type, id):
        if type in 'pecm':
            return id == self.fields[type+'_id']
        return False

    def get_component(self, config):
        compo = config.AllPlaces.get(self.fields['p_id'])
        if not compo:
            compo = config.AllEquipments.get(self.fields['e_id'])
            if not compo:
                compo = config.AllContainers.get(self.fields['c_id'])
        return compo

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
        if end - start > resolution:
            end -= end % resolution
            start -= start % resolution
            time_span, _, values = rrdtool.fetch(str(DIR_RRD+self.getRRDName(
            )), 'AVERAGE', '-s', str(int(start)), '-e', str(int(end)), '-r', str(resolution))
            ts_start, ts_end, ts_res = time_span
            times = range(ts_start, ts_end, ts_res)
            return zip(times, values)
        return None

    def validate_form(self, data, configuration, lang):
        tmp = super(Sensor, self).validate_form(data, configuration, lang)
        if tmp is True:
            tmp = ''
        try:
            if 'formula' in data and len(data['formula']) > 0:
                value = 1
                owData = unicode(eval(data['formula']))
                value = 0
                owData = unicode(eval(data['formula']))
        except:
            tmp += configuration.getMessage('formularules',lang) + '\n'

        try:
            if not len(data['component']) > 0:
                tmp += configuration.getMessage('componentrules',lang) + '\n'
        except:
            tmp += configuration.getMessage('componentrules',lang) + '\n'
        try:
            if not len(data['measure']) > 0:
                tmp += configuration.getMessage('measurerules',lang) + '\n'
        except:
            tmp += configuration.getMessage('measurerules',lang) + '\n'
        try:
            if not len(data['channel']) > 0:
                tmp += configuration.getMessage('channelrules',lang) + '\n'
        except:
            tmp += configuration.getMessage('channelrules',lang) + '\n'
        try:
            if not len(data['sensor']) > 0:
                tmp += configuration.getMessage('sensorrules',lang) + '\n'
        except:
            tmp += configuration.getMessage('sensorrules',lang) + '\n'

        if tmp == '':
            return True
        return tmp

    def set_value_from_data(self, data, c, user):
        super(Sensor, self).set_value_from_data(data, c, user)
        tmp = ['channel', 'sensor', 'subsensor', 'valuetype', 'formula', 'minmin', 'min', 'typical', 'max',
               'maxmax', 'a_minmin', 'a_min', 'a_typical', 'a_max', 'a_maxmax', 'lapse1', 'lapse2', 'lapse3', 'a_none']
        for elem in tmp:
            self.fields[elem] = data[elem]
        self.add_component(data['component'])
        self.add_measure(data['measure'])

        #self.createRRD()
        # Check if RRD exists but do not erase all previous data without reason!
        filename = os.path.join(DIR_RRD, self.getRRDName())
        if not os.path.exists(filename):
            self.createRRD()

        self.save(c, user)


class Batch(ConfigurationObject):
    def __init__(self, config):
        ConfigurationObject.__init__(self)
        self.config = config
        self.source = []
        self.destination = []
        self.checkpoints = []
        self.lastCheckPoint = None

    def __str__(self):
        string = "\nBatch :"
        for field in self.fields:
            string = string + "\n" + field + " : " + self.fields[field]
        return string + "\n"

    def get_type(self):
        return 'b'

    def get_name_listing(self):
        return 'batches'

    def get_class_acronym(self):
        return 'batch'

    def isExpired(self):
        return self.fields['expirationdate'] and (self.fields['expirationdate'] < (useful.now()[:10]))

    def add_measure(self, data):
        tmp = data.split('_')
        self.fields['m_id'] = tmp[-1]

    def get_total_cost(self):
        return self.floats('fixed_cost')+ (self.floats('cost')*self.floats('basicqt'))

    def get_quantity(self):
        return self.floats('basicqt')

    def get_quantity_used(self):
        qt = 0
        for e in self.source:
            qt += self.config.AllPourings.elements[e].floats('quantity')
        return qt

    def get_lifetime(self):
        if self.floats('basicqt') == 0.0:
            self.fields['basicqt'] = "0"
        else:
            qt = self.get_quantity_used()
            tmp = self.get_quantity() - qt
            if tmp < 0:
                return self.pourings.getTimestamp() - uself.getTimestamp()
        return useful.get_timestamp() - self.getTimestamp()

    def isComplete(self):
        if self.fields['completedtime'] != '':
            return True
        return False

    def add_source(self, pouring):
        self.remove_source(pouring)
        if len(self.source) == 0:
            self.source.append(pouring.getID())
        else:
            time = pouring.getTimestamp()
            insert = False
            for i in range(len(self.source)):
                tmp = self.config.AllPourings.elements[self.source[i]]
                tmptime = tmp.getTimestamp()
                if time < tmptime:
                    insert = True
                    self.source.insert(i, pouring.getID())
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
            time = pouring.getTimestamp()
            insert = False
            for i in range(len(self.destination)):
                tmp = self.config.AllPourings.elements[self.destination[i]]
                tmptime = tmp.getTimestamp()
                if int(time) < int(tmptime):
                    insert = True
                    self.destination.insert(i, pouring.getID())
                    break
            if insert is False:
                self.destination.append(pouring.getID())

    def remove_destination(self, pouring):
        if pouring.getID() in self.destination:
            self.destination.remove(pouring.getID())

    def add_checkpoint(self, cp, now):
        if cp not in self.checkpoints and cp in self.config.AllCheckPoints.elements:
            self.checkpoints.append(cp)
            self.lastCheckPoint = now
            aCP = self.config.AllCheckPoints.elements[cp]
            if self.id not in aCP.batches:
                aCP.batches.append(self.id)

    def fromModel(self,c,model):
        result = []
        id = model.getID()
        type = model.get_type()
        if type == 'tm':
            if self.transfers:
                for t in self.transfers:
                    if t in c.AllTransfers.elements:
                        e = c.AllTransfers.elements[t]
                        if id == e.fields['tm_id']:
                            result.append(e)
        elif type == 'dm':
            if self.manualdata:
                for t in self.manualdata:
                    e = c.AllManualData.elements[t]
                    if id == e.fields['dm_id']:
                        result.append(e)
        elif type == 'vm':
            if self.destination:
                for t in self.destination:
                    e = c.AllPourings.elements[t]
                    if id == e.fields['vm_id']:
                        result.append(e)
            if self.source:
                for t in self.source:
                    e = c.AllPourings.elements[t]
                    if id == e.fields['vm_id']:
                        result.append(e)
        return sorted(result, key=lambda e: e.fields['time'])

    def get_residual_quantity(self):
        val = self.get_quantity_used()
        if self.floats('basicqt') == 0.0:
            self.fields['basicqt'] = "0"
        return self.get_quantity()- val

    def clone(self, user, name=1):
        b = self.config.getObject('new', 'b')
        b.fields['active'] = self.fields['active']
        allObjects = self.config.findAllFromObject(self)
        posSuffix = self.fields['acronym'].rfind('_')+1
        lenAcro = len(self.fields['acronym'])
        prefix = self.fields['acronym'][0:posSuffix]
        tmpname = allObjects.findNextAcronym(prefix,lenAcro,name)
        if not tmpname:
            return False
        b.fields['acronym'] = tmpname
        b.fields['basicqt'] = self.fields['basicqt']
        b.fields['m_id'] = self.fields['m_id']
        b.fields['time'] = self.fields['time']
        b.fields['cost'] = self.fields['cost']
        b.fields['fixed_cost'] = self.fields['fixed_cost']
        b.fields['remark'] = self.fields['remark']
        b.fields['gr_id'] = self.fields['gr_id']
        for lang in self.config.AllLanguages.elements:
            b.setName(lang, self.get_real_name(lang),
                      user, self.config.getKeyColumn(b))
        b.creator = user.fields['u_id']
        b.created = b.fields['begin']
        b.save(self.config, user)
        return True

    def validate_form(self, data, configuration, lang):
        tmp = super(Batch, self).validate_form(data, configuration, lang)
        if tmp is True:
            tmp = ''
        try:
            value = useful.date_to_ISO(data['time'])
        except:
            traceback.print_exc()
            tmp += configuration.getMessage('timerules',lang) + '\n'

##        if 'completedtime' in data and data['completedtime']:
##            try:
##                value = useful.date_to_ISO(data['completedtime'])
##            except:
##                traceback.print_exc()
##                tmp += configuration.getMessage('timerules',lang) + '\n'

        try:
            value = float(data['cost'])
            if value < 0.0:
                tmp += configuration.getMessage('costrules',lang) + '\n'
        except:
            tmp += configuration.getMessage('costrules',lang) + '\n'

        try:
            value = float(data['fixed_cost'])
            if value < 0.0:
                tmp += configuration.getMessage('costrules',lang) + '\n'
        except:
            tmp += configuration.getMessage('costrules',lang) + '\n'

        try:
            value = float(data['basicqt'])
            if value < 0.0:
                tmp += configuration.getMessage('quantityrules',lang) + '\n'
        except:
            tmp += configuration.getMessage('quantityrules',lang) + '\n'

        if data['measure'] == '':
            tmp += configuration.getMessage('measurerules',lang) + '\n'

        if tmp == '':
            return True
        return tmp

    def lifespan(self,c):
        krecipe = self.get_group()
        if krecipe and krecipe in c.AllGrRecipe.elements:
            return c.AllGrRecipe.elements[krecipe].lifespan(c)
        return 0
    
    def set_value_from_data(self, data, c, user):
        super(Batch, self).set_value_from_data(data, c, user)
        tmp = ['basicqt', 'time', 'cost', 'fixed_cost']
        
        for elem in tmp:
            self.fields[elem] = data[elem]

        completed = None
        if 'completedtime' in data and data['completedtime']:
            try:
                completed= useful.date_to_ISO(data['completedtime'])
            except:
                completed= useful.now()
        if 'iscompleted' in data and data['iscompleted']:
            if completed:
                self.fields['completedtime']= completed
            else:
                self.fields['completedtime']= useful.now()
        else:
            self.fields['completedtime']= ""

        expdate = ""
        if 'expirationdate' in data and data['expirationdate']:
            try:
                expdate= useful.date_to_ISO(data['expirationdate'])[:10]
            except:
                if self.fields['time']:
                    expdate= (useful.string_to_date(self.fields['time'])+datetime.timedelta(days=self.lifespan(c))).isoformat()[:10]
        self.fields['expirationdate']= expdate

        self.add_measure(data['measure'])
        self.fields['gr_id'] = data['group']
        self.save(c, user)

    def count_logs(self,c):
        count = 0
        bID = self.getID()
        for kal,e in c.AllAlarmLogs.elements.items():
            if (bID == e.fields['cont_id']) and ( e.fields['cont_type'] == 'b' ):
                count += 1
        return count

    def get_group(self):
        return self.fields['gr_id']


class PouringModel(ConfigurationObject):
    def __init__(self, config):
        ConfigurationObject.__init__(self)
        self.config = config

    def __str__(self):
        string = "\nPouring Model :"
        for field in self.fields:
            string = string + "\n" + field + " : " + self.fields[field]
        return string + "\n"

    def get_type(self):
        return 'vm'

    def isModeling(self):
        return "v"

    def get_class_acronym(self):
        return 'pouringmodel'

    def get_group(self):
        return self.fields['h_id']

    def get_quantity(self):
        return self.floats('quantity')

    def get_unit_in_context(self,c, currObject):
        if self.fields['src']:
            if self.fields['src'] in c.AllGrRecipe.elements:
                aRecipe = c.AllGrRecipe.elements[self.fields['src']]
                return aRecipe.get_unit(c)
        elif currObject:
            return currObject.get_unit(c)
        return ""

    def validate_form(self, data, configuration, lang):
        return super(PouringModel, self).validate_form(data, configuration, lang)

    def set_value_from_data(self, data, c, user):
        if self.fields['h_id'] != '':
            self.config.AllCheckPoints.elements[self.fields['h_id']].remove_vm(self)
        super(PouringModel, self).set_value_from_data(data, c, user)
        self.fields['quantity'] = data['quantity']
        self.fields['in'] = data['in']
        if self.fields['in'] == '1':
            self.fields['src'] = data['recipe']
            self.fields['dest'] = ''
        else:
            self.fields['src'] = ''
            self.fields['dest'] = data['recipe']            
##        if data['src'] != 'current':
##            self.fields['src'] = data['src']
##        else:
##            self.fields['src'] = ''
##            self.fields['in'] = '0'
##        if data['dest'] != 'current':
##            self.fields['dest'] = data['dest']
##        else:
##            self.fields['dest'] = '1'
##            self.fields['in'] = ''
        self.fields['h_id'] = data['checkpoint']
        self.fields['rank'] = data['rank']
        if 'active' in data:
            self.config.AllCheckPoints.elements[self.fields['h_id']].add_vm(self)
        self.save(c, user)

class ManualDataModel(ConfigurationObject):
    def __init__(self, config):
        ConfigurationObject.__init__(self)
        self.config = config

    def __str__(self):
        string = "\nManual Data Model :"
        for field in self.fields:
            string = string + "\n" + field + " : " + self.fields[field]
        return string + "\n"

    def setCorrectAlarmValue(self):
        return

    def get_type(self):
        return 'dm'

    def isModeling(self):
        return "d"

    def get_classe_acronym(self):
        return 'manualdatamodel'

    def get_group(self):
        return self.fields['h_id']

    def get_quantity(self):
        return self.floats('typical')

    def validate_form(self, data, configuration, lang):
        return super(ManualDataModel, self).validate_form(data, configuration, lang)

    def set_value_from_data(self, data, c, user):
        if self.fields['h_id'] != '':
            self.config.AllCheckPoints.elements[self.fields['h_id']].remove_dm(
                self)
        super(ManualDataModel, self).set_value_from_data(data, c, user)
	tmp = ['rank', 'minmin', 'min', 'typical', 'max', 'maxmax', 'a_minmin', 'a_min', 'a_typical', 'a_max', 'a_maxmax', 'a_none']
	for elem in tmp:
	    self.fields[elem] = data[elem]
        self.fields['m_id'] = data['measure']
        self.fields['h_id'] = data['checkpoint']
        if 'active' in data:
            self.config.AllCheckPoints.elements[self.fields['h_id']].add_dm(
                self)
        self.save(c, user)

class TransferModel(ConfigurationObject):
    def __init__(self, config):
        ConfigurationObject.__init__(self)
        self.config = config

    def __str__(self):
        string = "\nModelTransfer :"
        for field in self.fields:
            string = string + "\n" + field + " : " + self.fields[field]
        return string + "\n"

    def get_type(self):
        return 'tm'

    def isModeling(self):
        return "t"

    def get_class_acronym(self):
        return 'transfermodel'

    def validate_form(self, data, configuration, lang):
        return super(TransferModel, self).validate_form(data, configuration, lang)

    def set_value_from_data(self, data, c, user):
        if self.fields['h_id'] != '':
            self.config.AllCheckPoints.elements[self.fields['h_id']].remove_tm(
                self)
        super(TransferModel, self).set_value_from_data(data, c, user)
        self.fields['gu_id'] = data['position']
        self.fields['h_id'] = data['checkpoint']
        self.fields['rank'] = data['rank']
        if 'active' in data:
            self.config.AllCheckPoints.elements[self.fields['h_id']].add_tm(
                self)
        self.save(c, user)

    def get_group(self):
        return self.fields['h_id']


class Transfer(ConfigurationObject):
    def __init__(self, config):
        ConfigurationObject.__init__(self)
        self.config = config

    def __str__(self):
        string = "\nBatchTransfer :"
        for field in self.fields:
            string = string + "\n" + field + " : " + self.fields[field]
        return string + "\n"

    def get_type(self):
        return 't'

    # WHERE it is moved
    def get_type_container(self):
        return self.fields['cont_type']

    def get_id_container(self):
        return self.fields['cont_id']

    # WHAT is moved
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
        objects = self.config.get_object(self.fields['object_type'],self.fields['object_id']).add_position(self)

    def validate_form(self, data, configuration, lang):
        tmp = ''
        if 'position' in data:
            objtype = data['object'].split('_')[0]
            objid = data['object'].split('_')[1]
            postype = data['position'].split('_')[0]
            posid = data['position'].split('_')[1]
            objet = configuration.get_object(objtype, objid)
            if (objet.is_actual_position(postype, posid, configuration) is True and objet.get_last_transfer() != self.id):
                tmp += configuration.getMessage('transferrules',lang) + '\n'
            if (objtype == 'e' and postype != 'p') or(objtype == 'c' and postype not in 'ep'):
                tmp += configuration.getMessage('transferhierarchy',lang) + '\n'
        else:
            tmp += configuration.getMessage('transferrules',lang) + '\n'
        if tmp == '':
            return True
        return tmp

    def set_value_from_data(self, data, c, user):
        if self.fields['object_type'] != '' and self.fields['object_id'] != '':
            self.get_source(c).remove_position(self)
        tmp = ['time', 'remark']
        for elem in tmp:
            self.fields[elem] = data[elem]
        if 'active' in data:
            self.fields['active'] = '1'
        else:
            self.fields['active'] = '0'
        if 'h_id' in data:
            self.fields['h_id'] = data['h_id']
        else:
            self.fields['h_id'] = ''
        self.set_position(data['position'])
        self.set_object(data['object'])
        if ('origin' in data) and data['origin']:
            self.fields['tm_id'] = data['origin']
        if self.fields['active'] == '1':
            self.get_source(c).add_position(self)
        else:
            self.get_source(c).remove_position(self)
        #TODO: Alarms should be checked and recorded in fields['al_id']
        self.save(c, user)
        if 'expirationdate' in data and data['expirationdate'] and self.get_type_container() == 'b':
            kbatch = self.get_id_container;
            if kbatch and kbatch in c.AllBatches.elements:
                batch = c.AllBatches.elements[kbatch]
                if not batch.fields['expirationdate']:
                    lifedays = batch.lifespan(c)
                    if lifedays:
                        batch.fields['expirationdate'] = (useful.string_to_date(self.fields['time'])+timedelta(days=lifedays)).isoformat()[:10]
                        batch.save(c, user)

    # WHAT is moved
    def get_source(self,config):
        if not self.fields['object_id']:
            return None
        if self.fields['object_type']:
            allObjs =config.findAll(self.fields['object_type'])
        else:
            allObjs = config.AllBatches
        return allObjs.get(self.fields['object_id'])

    # WHERE it is moved
    def get_component(self,config):
        return config.get_object(self.fields['cont_type'],self.fields['cont_id'])

    def get_class_acronym(self):
        return 'transfer'


class Barcode(ConfigurationObject):
    def __init__(self, item):
        ConfigurationObject.__init__(self)
        self.element = item

    def __repr__(self):
        return self.fields['code']

    def __str__(self):
        string = "\nCode barre :"
        for field in self.fields:
            string = string + "\n" + field + " : " + self.fields[field]
        return string + "\n"

##    def barcode_picture(self):
##        EAN = barcode.get_barcode_class('ean13')
##        self.fields['code'] = unicode(self.fields['code'])
##        ean = EAN(self.fields['code'])
##        # ean.save(os.path.join(DIR_BARCODES, self.fields['code']))

##    def get_picture_name(self):
##        return self.fields['code']+'.png'

##Now created locally using Javascript
##    def get_picture(self):
##        location = os.path.join(DIR_BARCODES, self.fields['code'])
##        if not os.path.exists(location):
##            self.barcode_picture()
##        return location

    def get_class_acronym(self):
        return 'barcode'

    def get_type(self):
        return 'barcode'
