#!/usr/bin/env python
# -*- coding: utf-8 -*-
import cgi
import collections
import datetime
import errno
import os
import os.path
import re
import rrdtool
import sets
import shutil
import socket
import subprocess
import sys
import threading
import time
import traceback
import urllib2

import barcode
import pyownet
import requests
import serial
import unicodecsv
import web.net as webnet

import HardConfig as hardconfig
import abe_adcpi
import abe_expanderpi
import abe_iopi
import abe_mcp3423
import abe_mcp3424
import myuseful as useful

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

KEY_ADMIN = "admin"  # Omnipotent user

CONNECTION_TIMEOUT = 900  # seconds = 15 minutes before reasking password

imagedTypes = [u'u', u'e', u'p', u'g', u'gf', u'gr', u'gu', u'c', u'b', u'h', u's', u'm', u'a', u'al']

alarmFields = ['minmin', 'min', 'typical', 'max', 'maxmax', 'a_minmin', \
               'a_min', 'a_typical', 'a_max', 'a_maxmax', 'a_none']
alarm_fields_for_groups = ['o_sms1', 'o_sms2', 'o_email1', 'o_email2', 'o_sound1', 'o_sound2']

ALL_UPDATE_GROUPS = u" upd_a upd_al upd_b upd_c upd_d upd_dm upd_e upd_gf upd_gr upd_gu upd_h upd_m upd_p upd_s upd_t upd_tm upd_u upd_v upd_vm upd_nfc"
ALL_TYPES = ['a', 'al', 'b', 'c', 'd', 'dm', 'e', 'gf', 'gr', 'gu', 'h', 'm', 'p', 's', 't', 'tm', 'u', 'v', 'vm']
ALL_NAMED_TYPES = ['a', 'b', 'c', 'dm', 'e', 'gf', 'gr', 'gu', 'h', 'm', 'p', 's', 'tm', 'u', 'vm']
COMPONENT_TYPES = ['p', 'e', 'c']
TRANSFERABLE_TYPES = ['e', 'c', 'b']
OBSERVABLE_TYPES = ['p', 'e', 'c', 'b']
POURABLE_TYPES = ['b']
TRANSACTION_TYPES = ['d', 't', 'v']

_lock_socket = None

buttonClasses = ""  # " btn-warning btn btn-md"

color_violet = "FF00FF"
color_blue = "0000FF"
color_green = "00FF00"
color_orange = "FFFF00"
color_red = "FF0000"
color_grey = "808080"
color_black = "000000"
color_white = "FFFFFF"

HALFLING_UNICODE = { "adjust" : "\ue063", #xe063
"alert" : "\ue209", #xe209
"align-center" : "\ue053", #xe053
"align-justify" : "\ue055", #xe055
"align-left" : "\ue052", #xe052
"align-right" : "\ue054", #xe054
"apple" : "\uf8ff", #xf8ff
"arrow-down" : "\ue094", #xe094
"arrow-left" : "\ue091", #xe091
"arrow-right" : "\ue092", #xe092
"arrow-up" : "\ue093", #xe093
"asterisk" : "\u2a", #x2a
"baby-formula" : "\ue216", #xe216
"backward" : "\ue071", #xe071
"ban-circle" : "\ue090", #xe090
"barcode" : "\ue040", #xe040
"bed" : "\ue219", #xe219
"bell" : "\ue123", #xe123
"bishop" : "\ue214", #xe214
"bitcoin" : "\ue227", #xe227
"blackboard" : "\ue218", #xe218
"bold" : "\ue048", #xe048
"book" : "\ue043", #xe043
"bookmark" : "\ue044", #xe044
"briefcase" : "\ue139", #xe139
"bullhorn" : "\ue122", #xe122
"calendar" : "\ue109", #xe109
"camera" : "\ue046", #xe046
"cd" : "\ue201", #xe201
"certificate" : "\ue124", #xe124
"check" : "\ue067", #xe067
"chevron-down" : "\ue114", #xe114
"chevron-left" : "\ue079", #xe079
"chevron-right" : "\ue080", #xe080
"chevron-up" : "\ue113", #xe113
"circle-arrow-down" : "\ue134", #xe134
"circle-arrow-left" : "\ue132", #xe132
"circle-arrow-right" : "\ue131", #xe131
"circle-arrow-up" : "\ue133", #xe133
"cloud" : "\u2601", #x2601
"cloud-download" : "\ue197", #xe197
"cloud-upload" : "\ue198", #xe198
"cog" : "\ue019", #xe019
"collapse-down" : "\ue159", #xe159
"collapse-up" : "\ue160", #xe160
"comment" : "\ue111", #xe111
"compressed" : "\ue181", #xe181
"console" : "\ue254", #xe254
"copy" : "\ue205", #xe205
"copyright-mark" : "\ue194", #xe194
"credit-card" : "\ue177", #xe177
"cutlery" : "\ue179", #xe179
"dashboard" : "\ue141", #xe141
"download-alt" : "\ue025", #xe025
"download" : "\ue026", #xe026
"duplicate" : "\ue224", #xe224
"earphone" : "\ue182", #xe182
"edit" : "\ue065", #xe065
"education" : "\ue233", #xe233
"eject" : "\ue078", #xe078
"envelope" : "\u2709", #x2709
"equalizer" : "\ue210", #xe210
"erase" : "\ue221", #xe221
"eur" : "\u20ac", #x20ac
"euro" : "\u20ac", #x20ac
"exclamation-sign" : "\ue101", #xe101
"expand" : "\ue158", #xe158
"export" : "\ue170", #xe170
"eye-close" : "\ue106", #xe106
"eye-open" : "\ue105", #xe105
"facetime-video" : "\ue059", #xe059
"fast-backward" : "\ue070", #xe070
"fast-forward" : "\ue076", #xe076
"file" : "\ue022", #xe022
"film" : "\ue009", #xe009
"filter" : "\ue138", #xe138
"fire" : "\ue104", #xe104
"flag" : "\ue034", #xe034
"flash" : "\ue162", #xe162
"floppy-disk" : "\ue172", #xe172
"floppy-open" : "\ue176", #xe176
"floppy-remove" : "\ue174", #xe174
"floppy-save" : "\ue175", #xe175
"floppy-saved" : "\ue173", #xe173
"folder-close" : "\ue117", #xe117
"folder-open" : "\ue118", #xe118
"font" : "\ue047", #xe047
"forward" : "\ue075", #xe075
"fullscreen" : "\ue140", #xe140
"gbp" : "\ue149", #xe149
"gift" : "\ue102", #xe102
"glass" : "\ue001", #xe001
"globe" : "\ue135", #xe135
"grain" : "\ue239", #xe239
"hand-down" : "\ue130", #xe130
"hand-left" : "\ue128", #xe128
"hand-right" : "\ue127", #xe127
"hand-up" : "\ue129", #xe129
"hdd" : "\ue121", #xe121
"hd-video" : "\ue187", #xe187
"header" : "\ue180", #xe180
"headphones" : "\ue035", #xe035
"heart" : "\ue005", #xe005
"heart-empty" : "\ue143", #xe143
"home" : "\ue021", #xe021
"hourglass" : "\u231b", #x231b
"ice-lolly" : "\ue231", #xe231
"ice-lolly-tasted" : "\ue232", #xe232
"import" : "\ue169", #xe169
"inbox" : "\ue028", #xe028
"indent-left" : "\ue057", #xe057
"indent-right" : "\ue058", #xe058
"info-sign" : "\ue086", #xe086
"italic" : "\ue049", #xe049
"king" : "\ue211", #xe211
"knight" : "\ue215", #xe215
"lamp" : "\ue223", #xe223
"leaf" : "\ue103", #xe103
"level-up" : "\ue204", #xe204
"link" : "\ue144", #xe144
"list-alt" : "\ue032", #xe032
"list" : "\ue056", #xe056
"lock" : "\ue033", #xe033
"log-in" : "\ue161", #xe161
"log-out" : "\ue163", #xe163
"magnet" : "\ue112", #xe112
"map-marker" : "\ue062", #xe062
"menu-down" : "\ue259", #xe259
"menu-hamburger" : "\ue236", #xe236
"menu-left" : "\ue257", #xe257
"menu-right" : "\ue258", #xe258
"menu-up" : "\ue260", #xe260
"minus" : "\u2212", #x2212
"minus-sign" : "\ue082", #xe082
"modal-window" : "\ue237", #xe237
"move" : "\ue068", #xe068
"music" : "\ue002", #xe002
"new-window" : "\ue164", #xe164
"object-align-bottom" : "\ue245", #xe245
"object-align-horizontal" : "\ue246", #xe246
"object-align-left" : "\ue247", #xe247
"object-align-right" : "\ue249", #xe249
"object-align-top" : "\ue244", #xe244
"object-align-vertical" : "\ue248", #xe248
"off" : "\ue017", #xe017
"oil" : "\ue238", #xe238
"ok-circle" : "\ue089", #xe089
"ok" : "\ue013", #xe013
"ok-sign" : "\ue084", #xe084
"open" : "\ue167", #xe167
"open-file" : "\ue203", #xe203
"option-horizontal" : "\ue234", #xe234
"option-vertical" : "\ue235", #xe235
"paperclip" : "\ue142", #xe142
"paste" : "\ue206", #xe206
"pause" : "\ue073", #xe073
"pawn" : "\ue213", #xe213
"pencil" : "\u270f", #x270f
"phone-alt" : "\ue183", #xe183
"phone" : "\ue145", #xe145
"picture" : "\ue060", #xe060
"piggy-bank" : "\ue225", #xe225
"plane" : "\ue108", #xe108
"play-circle" : "\ue029", #xe029
"play" : "\ue072", #xe072
"plus" : "\u2b", #x2b
"plus-sign" : "\ue081", #xe081
"print" : "\ue045", #xe045
"pushpin" : "\ue146", #xe146
"qrcode" : "\ue039", #xe039
"queen" : "\ue212", #xe212
"question-sign" : "\ue085", #xe085
"random" : "\ue110", #xe110
"record" : "\ue165", #xe165
"refresh" : "\ue031", #xe031
"registration-mark" : "\ue195", #xe195
"remove-circle" : "\ue088", #xe088
"remove" : "\ue014", #xe014
"remove-sign" : "\ue083", #xe083
"repeat" : "\ue030", #xe030
"resize-full" : "\ue096", #xe096
"resize-horizontal" : "\ue120", #xe120
"resize-small" : "\ue097", #xe097
"resize-vertical" : "\ue119", #xe119
"retweet" : "\ue115", #xe115
"road" : "\ue024", #xe024
"ruble" : "\u20bd", #x20bd
"save" : "\ue166", #xe166
"saved" : "\ue168", #xe168
"save-file" : "\ue202", #xe202
"scale" : "\ue230", #xe230
"scissors" : "\ue226", #xe226
"screenshot" : "\ue087", #xe087
"sd-video" : "\ue186", #xe186
"search" : "\ue003", #xe003
"send" : "\ue171", #xe171
"share-alt" : "\ue095", #xe095
"share" : "\ue066", #xe066
"shopping-cart" : "\ue116", #xe116
"signal" : "\ue018", #xe018
"sort-by-alphabet-alt" : "\ue152", #xe152
"sort-by-alphabet" : "\ue151", #xe151
"sort-by-attributes-alt" : "\ue156", #xe156
"sort-by-attributes" : "\ue155", #xe155
"sort-by-order-alt" : "\ue154", #xe154
"sort-by-order" : "\ue153", #xe153
"sort" : "\ue150", #xe150
"sound-5-1" : "\ue191", #xe191
"sound-6-1" : "\ue192", #xe192
"sound-7-1" : "\ue193", #xe193
"sound-dolby" : "\ue190", #xe190
"sound-stereo" : "\ue189", #xe189
"star" : "\ue006", #xe006
"star-empty" : "\ue007", #xe007
"stats" : "\ue185", #xe185
"step-backward" : "\ue069", #xe069
"step-forward" : "\ue077", #xe077
"stop" : "\ue074", #xe074
"subscript" : "\ue256", #xe256
"subtitles" : "\ue188", #xe188
"sunglasses" : "\ue240", #xe240
"superscript" : "\ue255", #xe255
"tag" : "\ue041", #xe041
"tags" : "\ue042", #xe042
"tasks" : "\ue137", #xe137
"tent" : "\u26fa", #x26fa
"text-background" : "\ue243", #xe243
"text-color" : "\ue242", #xe242
"text-height" : "\ue050", #xe050
"text-size" : "\ue241", #xe241
"text-width" : "\ue051", #xe051
"th" : "\ue011", #xe011
"th-large" : "\ue010", #xe010
"th-list" : "\ue012", #xe012
"thumbs-down" : "\ue126", #xe126
"thumbs-up" : "\ue125", #xe125
"time" : "\ue023", #xe023
"tint" : "\ue064", #xe064
"tower" : "\ue184", #xe184
"transfer" : "\ue178", #xe178
"trash" : "\ue020", #xe020
"tree-conifer" : "\ue199", #xe199
"tree-deciduous" : "\ue200", #xe200
"triangle-bottom" : "\ue252", #xe252
"triangle-left" : "\ue251", #xe251
"triangle-right" : "\ue250", #xe250
"triangle-top" : "\ue253", #xe253
"unchecked" : "\ue157", #xe157
"upload" : "\ue027", #xe027
"usd" : "\ue148", #xe148
"user" : "\ue008", #xe008
"volume-down" : "\ue037", #xe037
"volume-off" : "\ue036", #xe036
"volume-up" : "\ue038", #xe038
"warning-sign" : "\ue107", #xe107
"wrench" : "\ue136", #xe136
"yen" : "\u00a5", #x00a5
"zoom-in" : "\ue015", #xe015
"zoom-out" : "\ue016" } #xe016

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
        return unicode(value).replace('.', ',', 1)


def splitId(string):
    if not string:
        return '', ''
    splits = string.split(u'_')
    return splits[0] if len(splits) > 0 else '', splits[1] if len(splits) > 1 else ''


class valueCategory(object):

    def __init__(self, level, name, acronym, color, text_color):
        self.level = level
        self.name = name
        self.acronym = acronym
        self.color = color
        self.text_color = text_color

    # triple returns 4 values for a given category !
    def triple(self):
        return self.name, self.acronym, self.color, self.text_color

def exec_command(args):
    outputText = None
    try:
        outputText = subprocess.check_output(args, stderr=subprocess.STDOUT).decode(sys.getdefaultencoding())
    except subprocess.CalledProcessError as anError:
        print u"Statut=" + unicode(anError.returncode) + u" " + unicode(anError)
        return "Error="+unicode(anError.returncode)
    except:
        traceback.print_exc()
        return None
    return outputText


valueCategs = {-2: valueCategory(-2, 'minmin', '---', color_violet, color_black),
               -1: valueCategory(-1, 'min', '--', color_blue, color_white), 0: valueCategory(
        0, 'typical', '==', color_green, color_black), 1: valueCategory(1, 'max', '++', color_orange, color_black),
               2: valueCategory(2, 'maxmax', '++', color_red, color_white),
               3: valueCategory(3, 'none', '??', color_grey, color_white)}


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

        if not os.path.samefile(os.getcwd(), DIR_BASE):
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
        self.channels = {} # Directory of devices for different channels
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
        self.TimerThread = TimerThread(self)
        self.TimerThread.daemon = True
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
        self.AllBatches.load()  # must be just before loading checkpoints
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
        self.TimerThread.start()

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

    def getMessage(self, message_acronym, lang):
        mess = self.AllMessages.get(message_acronym)
        if mess:
            return mess.getName(lang)
        else:
            return message_acronym

    def getName(self, allObjects, lang):
        return self.getMessage(allObjects.get_class_acronym(), lang)

    def getHalfling(self, acronym, supp_classes=""):
        return self.AllHalflings.getHalfling(acronym, supp_classes)

    def getAllHalfling(self, allObjects, supp_classes=""):
        return self.AllHalflings.getHalfling(allObjects.get_class_acronym(), supp_classes)

    def getGlyph(self, acronym):
        return self.AllHalflings.getGlyph(acronym)

    def getAllGlyph(self, allObjects):
        return self.AllHalflings.getGlyph(allObjects.get_class_acronym())

    def get_channel_devices(self, channel):
        if not channel in self.channels:
            return []
        list_channel = self.channels[channel]
        if channel == 'wire':
            timestamp = useful.get_timestamp()
            list = self.owproxy.dir()
            for w in list:
                w = w.strip('/. ').replace('.','')[:14]
                self.set_channel_access('wire', w, 0, timestamp)
        return list_channel

    def set_channel_access(self, channel, device, rssi, timestamp):
        if not device:
            print "Device not specified."
            traceback.print_stack()
            return
        if not channel in self.channels:
            print "Channel "+channel+" unknown."
            traceback.print_stack()
            return
        list_channel = self.channels[channel]
        if not timestamp:
            timestamp = useful.get_timestamp()
        else:
            try:
                timestamp = int(timestamp)
            except:
                print "Timestamp " + unicode(timestamp) + " not a number."
                traceback.print_exc()
                return
        if not rssi:
            rssi = 0
        list_channel[device] = [rssi,timestamp]

    def breadcrumbTop(self, top):
        if top in "grbdtv":
            top = "gr"
        elif top == "gu":
            pass
        elif top in "gfu":
            top = "gf"
        elif top in "hdmtmvm" and not top in "mdtv":
            top = "h"
        elif top == u"pec":
            top = "pec"
        return top

    def breadcrumb(self, top, kowner, kelem, operation, lang):
        global buttonClasses
        #print "top=" + top + ",owner=" + kowner + ",kelem=" + kelem + ",operation=" + operation
        html = ""
        if not top:
            if kowner:
                ids = kowner.split('_')
                if len(ids) >= 2:
                    top = ids[0]
            if not top and kelem:
                ids = kelem.split('_')
                if len(ids) >= 2:
                    top = ids[0]
        top = self.breadcrumbTop(top)
        if top in "grbdtv":
            html = '<a href="/map/gr" class="btn btn-default">' + self.AllGrRecipe.statusIcon(None, False,
                                                                                              buttonClasses) + self.getMessage(
                'grecipe', lang) + '</a>'
        elif top == self.AllGrUsage.get_type():
            html = '<a href="/map/gu" class="btn btn-default">' + self.AllGrUsage.statusIcon(None, False,
                                                                                             buttonClasses) + self.getMessage(
                'guse', lang) + '</a>'
        elif top in "gfu":
            html = '<a href="/map/gf" class="btn btn-default">' + self.AllGrFunction.statusIcon(
                None, False)  + self.getMessage('gfunction', lang) + '</a>'
        elif top in "hdmtmvm" and not top in "mdtv":
            html = '<a href="/map/h" class="btn btn-default">' + self.AllCheckPoints.statusIcon(None, False,
                                                                                                buttonClasses) + self.getMessage(
                'checkpoint', lang) + '</a>'
        elif top == u"pec":
            html = '<a href="/map/pec" class="btn btn-default">' + self.getHalfling('place') + self.getHalfling(
                'equipment') + self.getHalfling('container') + self.getMessage('component', lang) + '</a>'
        elif not top in 'dtv':
            allObj = self.findAll(top)
            html = '<a href="/list/' + top + '" class="btn btn-default">' + allObj.statusIcon(None, False,
                                                                                               buttonClasses) + self.getMessage(
                allObj.get_class_acronym(), lang) + '</a>'
        owner = None
        if kowner:
            ids = kowner.split('_')
            if len(ids) >= 2:
                owner = self.get_object(ids[0], ids[1])
                if owner:
                    if ids[0] == top:
                        html += '<a href="/find/related/' + owner.getTypeId() + '" class="btn btn-default"><strong>' + owner.get_acronym() + '</strong></a>'  #:
                    else:
                        allGroup = self.findAllFromObject(owner)
                        html += '<a href="/find/related/' + owner.getTypeId() + '" class="btn btn-default">' + owner.statusIcon(
                            self, None, False) + '<strong>' + owner.get_acronym() + '</strong></a>'  # -
                    top = ids[0]
        if kelem:
            ids = kelem.split('_')
            if len(ids) >= 2:
                if ids[1] == 'new':
                    allObj = self.findAll(ids[0])
                    if allObj:
                        html += '<a href="/edit/' + ids[0] + '_new" class="btn btn-default">' + self.getHalfling(
                            'add') + self.getMessage('add', lang) + ' ' + allObj.statusIcon(None,
                                                                                            False) + self.getMessage(
                            allObj.get_class_acronym(), lang) + '</a>'  # -
                else:
                    elem = self.get_object(ids[0], ids[1])
                    if elem:
                        allObj = self.findAllFromObject(elem)
                        if not owner:
                            if ids[0] in 'dt':
                                kowner = elem.fields['object_id']
                                type = elem.fields['object_type']
                            elif ids[0] == 'v':
                                kowner = elem.fields['src']
                                type = 'b'
                            elif allObj.get_group_type():
                                kowner = elem.get_group()
                                type = allObj.get_group_type()
                            if kowner:
                                allGroup = self.findAll(type)
                                owner = allGroup.get(kowner)
                                if owner:
                                    html += '<a href="/find/related/' + owner.getTypeId() + '" class="btn btn-default">' + (
                                        '' if type == top else owner.statusIcon(self, None,
                                                                                False)) + '<strong>' + owner.get_acronym() + '</strong></a>'  # ' = ' if type==top else ' - ')+
                                    top = type
                        # if owner:
                        #    html += ' / '
                        # else:
                        #    if top == ids[0]:
                        #        html += ' = '
                        #    else:
                        #        html += ' - '
                        if ids[0] in 'dtv':
                            html += '<a href="/find/' + ids[
                                0] + '/' + owner.getTypeId() + '" class="btn btn-default">' + elem.statusIcon(self,
                                                                                                              None,
                                                                                                              False) + '</a>'
                        else:
                            html += '<a href="/find/related/' + elem.getTypeId() + '" class="btn btn-default">' + (
                                '' if top == ids[0] else elem.statusIcon(self, None,
                                                                         False)) + '<strong>' + elem.get_acronym() + '</strong></a>'
                        if operation:
                            html += '<a href="#" class="btn btn-default">' + self.getHalfling(
                                operation) + self.getMessage(operation, lang) + '</a>'
        elif operation:
            html += '<a href="#" class="btn btn-default">' + self.getHalfling(
                operation) + self.getMessage(operation, lang) + '</a>'
        return html

    def get_time(self):
        return useful.get_time()

    def is_component(self, type):
        if type in TRANSFERABLE_TYPES:
            return True
        return False

    def get_time_format(self):
        return useful.datetimeformat

    def triple(self, key):
        for k, v in valueCategs.items():
            if v.name == key or v.acronym == key:
                return v.triple()
        return None

    def linkedAcronym(self, allobj, key, icon):
        elem = allobj.get(key)
        if elem:
            style = ""
            if allobj.isModeling():
                style = " style=\"color:#28A4C9\""
            if 'acronym' in elem.fields:
                return "<a href=\"/find/related/" + allobj.get_type() + "_" + key + "\"" + style + ">" \
                       + (elem.statusIcon(self, False, False) if icon else "") + elem.fields['acronym'] + "</a>"
            else:
                return "<a href=\"/item/" + allobj.get_type() + "_" + key + "\"" + style + ">" \
                       + (elem.statusIcon(self, False, False) if icon else "") + "#" + key + "</a>"
        else:
            return ''

    def search_acronym(self, acro, result):
        acro = acro.lower()
        for type in ALL_TYPES:
            allObj = self.findAll(type)
            if 'acronym' in allObj.fieldnames:
                for key, elem in allObj.elements.items():
                    if acro in elem.fields['acronym'].lower():
                        if not elem in result:
                            result.append(elem)
        return result

    def search_names(self, word, result):
        word = word.lower()
        for type in ALL_NAMED_TYPES:
            allObj = self.findAll(type)
            for key, elem in allObj.elements.items():
                for lang, name in elem.names.items():
                    if word in name['name'].lower():
                        if not elem in result:
                            result.append(elem)
                        break
        return result

    def search_remark(self, acro, result):
        acro = acro.lower()
        for type in ALL_TYPES:
            allObj = self.findAll(type)
            if 'remark' in allObj.fieldnames:
                for key, elem in allObj.elements.items():
                    if acro in elem.fields['remark'].lower():
                        if not elem in result:
                            result.append(elem)
        return result

    def seconds_to_string(self, seconds, lang):
        if not seconds:
            return ""
        seconds = int(seconds)
        mn = seconds // 60
        hh = mn // 60
        dd = hh // 24
        seconds = seconds % 60
        mn = mn % 60
        hh = hh % 24
        result = ((" " + unicode(dd) + " " + self.getMessage("day" + ("s" if dd > 1 else ""), lang)) if dd else "") \
                 + ((" " + unicode(hh) + " " + self.getMessage("hour" + ("s" if hh > 1 else ""), lang)) if hh else "") \
                 + ((" " + unicode(mn) + " " + self.getMessage("minute" + ("s" if mn > 1 else ""), lang)) if mn else "") \
                 + ((" " + unicode(seconds) + " " + self.getMessage("second" + ("s" if seconds > 1 else ""),
                                                                    lang)) if seconds else "")
        return result[1:]

    # TRUE if no problem to create Print job
    def labelPrinter(self, type_id, someText):
        # fileName = os.path.join(self.HardConfig.rundirectory, type_id + ".prn")
        # print "Printing using " + fileName
        # with open(fileName, "w") as printFile:
        #     printFile.write(someText)
        # return exec_command(["lpr", "-o", "raw", "-r", fileName])
        #return someText
        fileName = "/dev/usb/lp0"
        print "Printing using " + fileName
        with open(fileName, "w") as printFile:
            printFile.write(someText)


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
        return self.getTypeId() + (' ' + self.fields['acronym']) if 'acronym' in self.fields else ''

    def get_select_str(self, lang):
        acr = self.fields['acronym']
        name = self.getName(lang)
        return (unicode(acr) + ' - ' + name)

    def floats(self, field):
        return useful.str_float(self.fields[field])

    def save(self, configuration, anUser=""):
        self.fields["begin"] = useful.now()
        if anUser != "":
            self.fields["user"] = anUser.fields['u_id']

        if self.creator is None:
            self.creator = self.fields['user']
            self.created = self.fields['begin']

        allObjects = configuration.findAllFromObject(self)
        with open(allObjects.file_of_objects, "a") as csvfile:
            writer = unicodecsv.DictWriter(csvfile,
                                           delimiter='\t',
                                           fieldnames=allObjects.fieldnames,
                                           encoding="utf-8")
            writer.writerow(self.fields)
            allObjects.hierarchy = None  # Sort needed...
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
            directory = os.path.join(DIR_DOC, thisType)
            if ensure:
                if not os.path.exists(directory):
                    try:
                        os.makedirs(directory)
                    except OSError as e:
                        if e.errno != errno.EEXIST:
                            traceback.print_exc()
                            return None
            return os.path.join(directory, thisType + u'_' + unicode(self.id) + u'.' + ext)
        return None

    def getImageURL(self, ext="jpg"):
        thisType = self.get_type()
        if thisType in imagedTypes:
            return URL_DOC + thisType + u'/' + thisType + u'_' + unicode(self.id) + u'.' + ext
        return ""

    def getDocumentDir(self, ensure=False):
        thisType = self.get_type()
        if thisType in imagedTypes:
            directory = os.path.join(DIR_DOC,
                                     thisType,
                                     thisType + u'_' + unicode(self.id))
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
                                     thisType + u'_' + unicode(self.id))
            if not os.path.exists(directory):
                return []
            return os.listdir(directory)
        return []

    def getDocumentURL(self, filename=u''):
        thisType = self.get_type()
        if thisType in imagedTypes:
            return URL_DOC + thisType + u'/' + thisType + u'_' + unicode(self.id) + u'/' + filename
        return ""

    def isImaged(self):
        fileName = self.getImagePath(False, u"png")
        if fileName is None:
            return None
        elif os.path.isfile(fileName):
            return u"png"
        else:
            fileName = self.getImagePath(False, u"jpg")
            if os.path.isfile(fileName):
                return u"jpg"
            else:
                return None

    def get_href(self, operation):
        if operation:
            return '/' + operation + '/' + self.getTypeId()
        else:
            return '/find/related/' + self.getTypeId()

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
            return "Record " + unicode(self.id) + ": no name"

    def getNameHTML(self, lang):
        return cgi.escape(self.getName(lang), True).replace("'", "&#39;");

    def get_real_name(self, lang):
        if lang in self.names:
            return self.names[lang]['name']
        return ''

    def getID(self):
        return self.id

    # must be overriden
    def get_type(self):
        return ""

    def getTypeId(self):
        return self.get_type() + u'_' + unicode(self.id)

    # to be overriden when parents available
    def get_all_parents(self,list=[],allObjs=None):
        return list

    def getTimestring(self):
        stamp = ""
        if 'begintime' in self.fields:
            stamp = self.fields['begintime']
        elif 'time' in self.fields:
            stamp = self.fields['time']
        elif 'begin' in self.fields:
            stamp = self.fields['begin']
        return stamp

    def getTimestamp(self):
        # time = editable time fields
        stamp = self.getTimestring()
        if not stamp:
            return 0
        else:
            return useful.date_to_timestamp(stamp)

    def get_hash_type(self):
        obj_type = self.get_type()
        hash = 10 * (ord(obj_type[0]) - ord('a'))
        if len(obj_type) > 1:
            hash += ((ord(obj_type[1]) - ord('a')) + 1) % 10
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

    def validate_form(self, data, configuration, user):
        tmp = ''
        lang = user.fields['language']
        if 'acronym' not in data:
            tmp = configuration.getMessage('acronymrequired', lang) + '\n'
        try:
            cond = data['acronym'] == re.sub('[^\w]+', '', data['acronym'])
            if not cond:
                tmp += configuration.getMessage('acronymrules', lang) + '\n'
        except:
            tmp += configuration.getMessage('acronymrules', lang) + '\n'

        allObjects = configuration.findAllFromObject(self)
        if not allObjects.unique_acronym(data['acronym'], self.id):
            tmp += configuration.getMessage('acronymunique', lang) + '\n'
        else:
            try:
                if 'code' in data and len(data['code']) > 0:
                    some_code = data['code'].strip()
                    if not configuration.AllBarcodes.validate_barcode(
                            some_code,"", self.get_type(), self.id):
                        tmp += configuration.getMessage('barcoderules', lang) + '\n'
            except:
                tmp += configuration.getMessage('barcoderules', lang) + '\n'
        if tmp == '':
            return True
        return tmp

    def set_value_from_data(self, data, c, user):
        allObjects = c.findAllFromObject(self)

        if self.fields['acronym'] != data['acronym']:
            self.fields['acronym'] = data['acronym']
            allObjects.hierarchy = None

        for key in c.AllLanguages.elements:
            if key in data:
                self.setName(key, data[key], user, c.getKeyColumn(self))

        if 'active' in data:
            self.set_active('1')
        else:
            self.set_active('0')

        if 'placeImg' in data and data['placeImg'] != {}:
            if data.placeImg.filename != '':
                filepath = data.placeImg.filename.replace('\\', '/')
                ext = ((filepath.split('/')[-1]).split('.')[-1])
                if ext and ext.lower() in [u'jpg', u'jpeg', u'png']:
                    with open(self.getImagePath(True, ext=("png" if ext.lower() == u"png" else u"jpg")), 'w') as fout:
                        fout.write(data.placeImg.file.read())
        # linkedDocs is treated by caller because "web" object is needed...

        if 'code' in data:
            self.ensure_barcode(c,user,data['code'])

        self.fields['remark'] = data['remark']

    def ensure_barcode(self,c,user,code):
        lenCode = len(code)
        if lenCode >= 12 and lenCode <= 13:
            c.AllBarcodes.add_barcode(self, code, "", user)
        elif lenCode == 0:
            # Defaut barcode: 99hhT1234567x
            code = 990000000000 + (self.get_hash_type() * 10000000) + int(self.id)
            ean = c.AllBarcodes.EAN(unicode(code))
            c.AllBarcodes.add_barcode(self, ean.get_fullcode(), "", user)

    def get_barcode(self, c, codetype=""):
        return c.AllBarcodes.get_barcode_from_object(self.get_type(),self.getID(), codetype)

    def get_events(self, c):
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
                        if self.config.AllTransfers.elements[self.transfers[count - 1]].getTimestamp() > begin:
                            tmp.append(self.transfers[count - 1])
                tmp.append(t)
            elif time <= begin and (first is True
                                    or count == len(self.transfers) - 1):
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

    def add_position(self, transfer, user):
        self.remove_position(transfer)
        if self.isActive() and transfer.isActive():
            time = transfer.getTimestring()
            insert = False
            tmp = None
            for i in range(len(self.transfers)):
                tmp = self.config.AllTransfers.elements[self.transfers[i]]
                tmptime = tmp.getTimestring()
                if time < tmptime:
                    insert = True
                    self.transfers.insert(i, transfer.getID())
                    transfer.completed = tmptime
                    break
            if insert is False:
                if tmp:
                    tmp.completed = time
                    if user and tmp.checkTimerAlarm(self.config, False):
                        tmp.save(self.config, user)
                self.transfers.append(transfer.getID())
                transfer.completed = None

    def remove_position(self, transfer):
        try:
            pos = self.transfers.index(transfer.getID())
            if pos > 0:
                prev = self.config.AllTransfers.get(self.transfers[pos - 1])
                if prev:
                    prev.completed = None
                    if pos < (len(self.transfers) - 1):
                        nxt = self.config.AllTransfers.get(self.transfers[pos + 1])
                        if nxt:
                            prev.completed = nxt.getTimestring()
            self.transfers.remove(transfer.getID())
        except:
            pass
        transfer.completed = None

    def get_last_transfer(self, configuration):
        if len(self.transfers) > 0:
            key = self.transfers[-1]
            return configuration.AllTransfers.get(key)
        return None

    def get_last_user(self, configuration):
        if len(self.transfers) > 0:
            key = self.transfers[-1]
            t = configuration.AllTransfers.get(key)
            if t:
                return t.fields['user']
        return self.fields['user']

    def get_actual_position_here(self, configuration):
        currObj = None
        tmp = self.get_last_transfer(configuration)
        if tmp is not None:
            currObj = configuration.get_object(tmp.fields['cont_type'], tmp.fields['cont_id'])
        return currObj

    def get_actual_position_hierarchy(self, configuration, result=[]):
        if not (self in result):
            result.append(self)
            currObj = self.get_actual_position_here(configuration)
            if currObj:
                return currObj.get_actual_position_hierarchy(configuration, result)
        return result

    def is_actual_position(self, type, id, configuration):
        tmp = self.get_last_transfer(configuration)
        if tmp is not None:
            if type == tmp.fields['cont_type'] \
                    and unicode(id) == tmp.fields['cont_id']:
                return True
        return False

    def get_name_listing(self):
        return self.get_class_acronym() + 's'

    def get_acronym(self):
        return self.fields['acronym']

    # overriden for groups !
    def get_acronym_hierarchy(self):
        return self.fields['acronym']

    def sort_key(self):
        return self.get_acronym_hierarchy().upper()

    def sort_level_key(self):
        return (self.fields['rank'].rjust(10) if 'rank' in self.fields else '') + self.fields['acronym'].upper()

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
                    .elements[self.transfers[count - 1]]
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
                sensor = config.AllSensors.get(a)
                if sensor and sensor.isActive():
                    infos[a] = sensor.fetch(begin, end)
        return infos

    def isActive(self):
        if not 'active' in self.fields:
            return True
        else:
            return self.fields['active'] != '0'

    def getImage(self, height=36):
        ext = self.isImaged()
        if ext:
            return "<img src=\"" + self.getImageURL(ext) + "\" alt=\"" + unicode(self) + "\" height=" + unicode(
                height) + ">"
        else:
            return ""

    def isModeling(self):
        return None

    def isExpired(self):
        return None

    def isComplete(self):
        return False

    def isPinned(self,connected):
        return False

    def isAlarmed(self, c):
        if 'al_id' in self.fields:
            if self.fields['al_id']:
                if self.get_type() != 'al':
                    allog = c.AllAlarmLogs.get(self.fields['al_id'])
                    if allog and allog.isActive() and not allog.isComplete():
                        return True
            return False
        # TODO: Check this when implementing alarms for timed transfers and for incorrect pourings...
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

    def statusIcon(self, configuration, pic=None, inButton=False, connected = None):
        allObjects = configuration.findAllFromObject(self)
        supp_classes = ""
        if not inButton:
            if self.isModeling():
                supp_classes = " text-info"
            elif self.isComplete():
                supp_classes = " text-danger"
            elif self.isExpired():
                supp_classes = " text-danger"
        result = configuration.getAllHalfling(allObjects, supp_classes)
        if 'active' in self.fields and self.fields['active'] == '0':
            result = '<span class="icon-combine">' + result + '<span class="halflings halflings-remove text-danger"></span></span>'
        # result = '<span class="icon-combine">'+result+'<span class="halflings halflings-time text-danger"></span></span>'
        if pic:
            result += self.getImage(36)
        if connected:
            if self.isPinned(connected):
                result += configuration.getHalfling("pin","")
        return result

    def getGlyph(self, configuration):
        allObjects = configuration.findAllFromObject(self)
        return allObjects.getGlyph()

    def getTypeAlarm(self, value, model=None):
        if (value == None) or (value == ''):
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
        return useful.str_float(self.get_quantity_string())

    def get_quantity_string(self):
        return "0";

    def get_measure(self, c):
        if 'm_id' in self.fields and self.fields['m_id'] and self.fields['m_id'] in c.AllMeasures.elements:
            return c.AllMeasures.elements[self.fields['m_id']]
        return None;

    def get_unit(self, c):
        aMeasure = self.get_measure(c)
        if aMeasure:
            return aMeasure.fields['unit']
        return "";

    def getQtyUnit(self, c, lang="EN"):
        result = u'?'
        measure = self.get_measure(c)
        quantity = self.get_quantity_string()
        if quantity:
            if measure and measure.fields['step']:
                quantity = round(useful.str_float(quantity), int(measure.fields['step']))
            result = unicode(quantity)
        if measure:
            result += ' ' + measure.fields['unit']
        if result == '?':
            return ''
        return result

    def get_group(self):
        return None

    def get_batches(self, c):
        return []

    def hasParent(self, c, acronym):
        acronym = acronym.lower()
        allSelf = c.findAll(self.get_type())
        allObj = c.findAll(allSelf.get_group_type())
        gr = allObj.get(self.get_group())
        if gr:
            if acronym == gr.fields['acronym'].lower():
                return gr
            for aGroup in gr.get_all_parents([], allObj):
                bGroup = allObj.elements[aGroup]
                if bGroup.fields['acronym'].lower() == acronym:
                    return bGroup
        return None

    def updateAllowed(self, user, c):
        user_group = user.get_group()
        if user_group and user_group in c.AllGrFunction.elements:
            key_upd = u"upd_" + self.get_type()
            aGroup = c.AllGrFunction.elements[user_group]
            if aGroup.fields['acronym'].lower() == KEY_ADMIN:
                return True
            if aGroup.fields['acronym'].lower() == key_upd:
                return True
            for user_group in aGroup.get_all_parents([], c.AllGrFunction):
                bGroup = c.AllGrFunction.elements[user_group]
                if bGroup.fields['acronym'].lower() == KEY_ADMIN:
                    return True
                if bGroup.fields['acronym'].lower() == key_upd:
                    return True
        return False

    def readPrintTemplate(self,c,format):
        directory = self.getDocumentDir()
        try:
            with open(os.path.join(directory, format + ".prn")) as f:
                try:
                    return f.read()
                except:
                    pass
        except:
            pass
        allObjs = c.findAll(self.get_type())
        elem_group = self.get_group()
        if elem_group:
            allGrs = c.findAll(allObjs.get_group_type())
            above = allGrs.get(elem_group)
            if above:
                result = above.readPrintTemplate(c,format)
                if result:
                    return result
        for elem_group in self.get_all_parents([], allObjs):
            above = allObjs.get(elem_group)
            if above:
                result = above.readPrintTemplate(c,format)
                if result:
                    return result
        return None


    def labelPrinter(self, c, format="label", lang=""):
        printerString = self.readPrintTemplate(c,format)
        if printerString:
            allObjs = c.findAll(self.get_type())
            labelFields = {"barcode": self.get_barcode(c,''), "code": self.fields['acronym'], "name": self.getName(lang), "type": allObjs.getName(lang)}
            value = ""
            if 'remark' in self.fields and self.fields['remark']:
                value = c.getMessage('remark', self.lang) + ": " + self.fields['remark']
            labelFields['remark'] = value
            value = ""
            if 'expirationdate' in self.fields and self.fields['expirationdate']:
                value = c.getMessage('expirationdate', lang) + ": " + self.fields['expirationdate']
            labelFields['expiration'] = value
            value = ""
            group = self.get_group()
            if group:
                allGrs = c.findAll(allObjs.get_group_type())
                above = allGrs.get(group)
                if above:
                    value = allGrs.getName(lang) + ": " + above.getName(lang)
            labelFields['group'] = value
            labelFields['quantity'] = self.getQtyUnit(c, lang)
            return c.labelPrinter(self.getTypeId(),printerString % labelFields)
        return "Format "+format+" unknown."

    def get_history(self, c):
        allObjects = c.findAllFromObject(self)
        id = self.getID()

        relations = None
        if allObjects.file_of_relations:
            with open(allObjects.file_of_relations) as csvfile:
                reader = unicodecsv.DictReader(csvfile, delimiter="\t")
                relations = []
                for row in reader:
                    if row['parent_id'] == id:
                        relations.append(row)
                    elif row['child_id'] == id:
                        relations.append(row)

        names = None
        if allObjects.file_of_names:
            with open(allObjects.file_of_names) as csvfile:
                reader = unicodecsv.DictReader(csvfile, delimiter="\t")
                names = []
                for row in reader:
                    if row[allObjects.keyColumn] == id:
                        names.append(row)

        records = None
        with open(allObjects.file_of_objects) as csvfile:
            reader = unicodecsv.DictReader(csvfile, delimiter="\t")
            records = []
            for row in reader:
                if row[allObjects.keyColumn] == id:
                    records.append(row)

        return records, names, relations


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
            timestamp = useful.get_timestamp()
            if len(self.config.AllSensors.elements) > 0:
                self.config.AllSensors.update(timestamp)
                #TODO: send values to locally connected relays
                # for relaySensor in c.AllSensors.elements:
                #     if relaySensor.relaySetting and relaySensor.fields['channel'] != 'lora' and relaySensor.fields[
                #         'sensor'] and relaySensor.fields['subsensor']:
                #         SEND VALUE TO SENSOR/RELAY !
                #         relaySensor.relaySetting = None
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
        print "Radio at " + unicode(self.config.HardConfig.ela_bauds) + " bauds on " + DIR_TTY
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
                                timestamp = useful.get_timestamp()
                                RSS = int(line[0] + line[1], 16)
                                HEX = line[2] + line[3] + line[4]
                                self.config.set_channel_access('radio',HEX,RSS,timestamp)
                                # ADDRESS = int(HEX,16)
                                VAL = int(line[5] + line[6] + line[7], 16)
                                print ("ELA="
                                       + HEX
                                       + ", RSS="
                                       + unicode(RSS)
                                       + ", val=" + unicode(VAL))
                                currSensor = None
                                value = VAL
                                for sensor in self.config.AllSensors.elements:
                                    currSensor = self.config.AllSensors.elements[sensor]
                                    if currSensor.isActive():
                                        try:
                                            if (unicode(currSensor.fields['sensor']).translate(noDots) == unicode(
                                                    HEX).translate(noDots)):
                                                if not currSensor.fields['formula'] == '':
                                                    value = unicode(
                                                        eval(currSensor.fields['formula']))
                                                print(
                                                        u"Sensor ELA-" + currSensor.fields['sensor'] + u": " +
                                                        currSensor.fields['acronym'] + u" = " + unicode(value))
                                                currSensor.update(timestamp, value, self.config)
                                        except:
                                            traceback.print_exc()
                                            print "Error in formula, " + currSensor.fields['acronym'] + ": " + \
                                                  currSensor.fields['formula']
                            line = None
                        else:
                            line.append(data)
                except:
                    traceback.print_exc()
        except:
            traceback.print_exc()


class TimerThread(threading.Thread):

    def __init__(self, config):
        threading.Thread.__init__(self)
        self.config = config

    def run(self):
        while self.config.isThreading is True:
            timer = 0
            now = useful.get_timestamp()
            for k, b in self.config.AllBatches.elements.items():
                if b.isActive() and not b.isComplete():
                    t = b.get_last_transfer(self.config)
                    if t and not t.completed:
                        if t.checkTimerAlarm(self.config, True):
                            t.save(self.config, "")
            while self.config.isThreading is True and timer < 60:
                time.sleep(1)
                timer = timer + 1


class AllObjects(object):

    def __init__(self, obj_type, obj_name, config):
        self.obj_type = obj_type
        self.obj_classname = obj_name
        self.elements = {}
        self.hierarchy = None
        self.file_of_objects = os.path.join(DIR_DATA_CSV, obj_type.upper()) + ".csv"
        self.file_of_names = os.path.join(DIR_DATA_CSV, obj_type.upper()) + "names.csv"
        self.file_of_relations = None
        self.keyColumn = obj_type + "_id"
        self.config = config
        self.count = 0
        # TODO: Strange, some classes do not list the fields they contain...
        self.fieldnames = None
        config.registry[obj_type] = self
        config.registry[obj_name] = self
        if self.get_class_acronym():
            config.registry[self.get_class_acronym()] = self

    def get_type(self):
        return self.obj_type

    def get_group_type(self):
        return None

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
                csvfile.write('\t' + self.fieldnames[tmp])
                tmp = tmp + 1
            csvfile.write('\n')
        if self.file_of_names is not None:
            with open(self.file_of_names, 'w') as csvfile:
                csvfile.write(self.fieldtranslate[0])
                tmp = 1
                while tmp < len(self.fieldtranslate):
                    csvfile.write('\t' + self.fieldtranslate[tmp])
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
                            conformantFile = open(self.file_of_objects + ".NEW", 'w')
                            print (self.file_of_objects + " will be made conformant")
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
                currObject.fields['begin'] = useful.date_to_ISO(currObject.fields['begin'])
                if key in self.elements:
                    tmp = self.elements[key]
                    currObject.created = tmp.created
                    currObject.creator = tmp.creator
                    if tmp.get_type() == 't':
                        self.config \
                            .get_object(tmp.fields['object_type'], tmp.fields['object_id']) \
                            .remove_position(tmp)
                    elif tmp.get_type() == 'd':
                        self.config \
                            .get_object(tmp.fields['object_type'], tmp.fields['object_id']) \
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
                            .add_position(currObject, None)
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
                elif currObject.get_type() == 'al':
                    if currObject.isActive():
                        oType = currObject.fields['s_type']
                        self.config.get_object((oType if oType else 's'), \
                                               currObject.fields['s_id']) \
                            .set_alarm(self.config, currObject)
        if conformantFile is not None:
            conformantFile.close()
            # TODO: Rename current file to timestamped one, rename .NEW to actual file...
            os.rename(self.file_of_objects,
                      self.file_of_objects + '.' + useful.timestamp_to_ISO(useful.get_timestamp()).translate(None,
                                                                                                             " :./-"))
            os.rename(self.file_of_objects + ".NEW", self.file_of_objects)

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

    def unique_acronym(self, acronym, myID):
        acronym = acronym.lower()
        for k, element in self.elements.items():
            if element.fields['acronym'].lower() == acronym \
                    and unicode(myID) != unicode(element.fields[self.keyColumn]):
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
                    element = self.config.AllBarcodes.barcode_to_item(
                        iditem[:len(iditem) - 1])
                    if element.get_type() == self.get_type():
                        return element
                except:
                    return None
            elif (iditem.endswith(u"!")):
                acronym = iditem[:len(iditem) - 1]
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

    def getName(self, lang):
        return self.config.getName(self, lang)

    def get_sorted(self):
        return collections.OrderedDict(sorted(self.elements.items(),
                                              key=lambda t: t[1].sort_key()))

    def sort_hierarchy_objects(self, objects):
        return sorted(objects,
                      key=lambda t: t.sort_key() if t else "")

    def sort_hierarchy(self, keyList):
        return sorted(keyList,
                      key=lambda t: self.elements[t].sort_key() if t else "")

    def get_sorted_hierarchy(self):
        if not self.hierarchy:
            self.hierarchy = self.sort_hierarchy(self.elements.keys())
        return self.hierarchy

    # find uncompleted active objects
    def in_use(self):
        result = []
        for k in self.elements.keys():
            elem = self.elements[k]
            if elem.isActive() and not elem.isComplete():
                result.append(k)
        return result

    # find probably most useful objects
    def get_top(self, size, keyList):
        timed = sorted(keyList,
                       key=lambda t: self.elements[t].getTimestring() if t else "", reverse=True)
        if size <= 0:
            return timed
        return timed[:size]

    def findAcronym(self, acronym):
        acronym = acronym.lower()
        for k, element in self.elements.items():
            if element.fields['acronym'].lower() == acronym:
                return element
        return None

    def findBarcode(self, barcode):
        try:
            elem = self.config.AllBarcodes.barcode_to_item(barcode)
        except:
            return None

    def statusIcon(self, pic=None, inButton=False, add_classes=''):
        supp_classes = "" + add_classes
        if not inButton:
            if self.isModeling():
                supp_classes += " text-info"
        return self.config.getAllHalfling(self, supp_classes)

    def getGlyph(self):
        return self.config.getAllGlyph(self)

    def get_linked(self,parent):
        a_type = parent.get_type()
        result = []
        if a_type == self.get_group_type():
            a_ids = [parent.getID()]
            a_ids.extend(parent.get_all_children([], None))
            for key in self.get_sorted_hierarchy():
                elem = self.get(key)
                if elem.get_group() in a_ids:
                    result.append(key)
        return result


class AllUsers(AllObjects):

    def __init__(self, config):
        AllObjects.__init__(self, 'u', User.__name__, config)
        self.fieldnames = ['begin', 'u_id', 'active', 'acronym',
                           'remark', 'addr1', 'addr2', 'addr3', 'vat', 'accesslevel',
                           'registration', 'phone', 'mail', 'password',
                           'language', 'gf_id', 'donotdisturb', 'user']
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

    def get_admin(self):
        return self.findAcronym(KEY_ADMIN)

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


class AllAlarmLogs(AllObjects):

    def __init__(self, config):
        AllObjects.__init__(self, 'al', AlarmLog.__name__, config)
        self.file_of_objects = os.path.join(DIR_DATA_CSV, "alarmlogs.csv")
        self.file_of_names = None
        self.fieldnames = ['begin', 'al_id', 'cont_id', 'cont_type',
                           's_id', 's_type', 'value', 'typealarm', 'a_id', 'gf_id', 'begintime',
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
                if (sid == e.fields['s_id']) and (
                        (e.fields['s_type'] == stype) or (e.fields['s_type'] == '' and stype == 's')):
                    if (not begin or (time >= begin)) and (not end or (time < end)):
                        logs.append(e)
        else:
            for kal in self.elements.keys():
                e = self.elements[kal]
                if (sid == e.fields['s_id']) and (
                        (e.fields['s_type'] == stype) or (e.fields['s_type'] == '' and stype == 's')):
                    logs.append(e)
        return sorted(logs, key=lambda t: t.fields['begin'], reverse=True)

    def get_logs_for_component(self, component, begin, end):
        logs = []
        sid = component.getID()
        stype = component.get_type()
        if begin or end:
            for kal in self.elements.keys():
                e = self.elements[kal]
                time = e.getTimestamp()
                if (sid == e.fields['cont_id']) and (e.fields['cont_type'] == stype):
                    if (not begin or (time >= begin)) and (not end or (time < end)):
                        logs.append(e)
        else:
            for kal in self.elements.keys():
                e = self.elements[kal]
                if (sid == e.fields['cont_id']) and (e.fields['cont_type'] == stype):
                    logs.append(e)
        return sorted(logs, key=lambda t: t.fields['begin'], reverse=True)

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

    def getHalfling(self, acronym, supp_classes=""):
        try:
            return self.elements[acronym].getHalfling(supp_classes)
        except:
            traceback.print_exc()
            return "<em>" + acronym + " not found</em>"

    def getGlyph(self, acronym):
        try:
            return self.elements[acronym].getGlyph()
        except:
            traceback.print_exc()
            return "<em>" + acronym + " not found</em>"


class AllAlarms(AllObjects):

    def __init__(self, config):
        AllObjects.__init__(self, 'a', Alarm.__name__, config)
        self.fieldnames = ['begin', 'a_id', 'active', 'acronym', 'o_sms1',
                           'o_sms2', 'o_email1', 'o_email2', 'o_sound1',
                           'o_sound2', 'relay1', 'relay1_id', 'relay2', 'relay2_id', 'remark', 'user']
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
                csvfile.write('\t' + self.fieldrelations[tmp])
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
            if g:
                cond = g.getID() in group.related
            else:
                cond = len(group.related) == 0
            if cond:
                myString.append(k)
                subString = []
                self.get_hierarchy_str(group, subString)
                if len(subString) > 0:
                    myString.append('>>')
                    myString.extend(subString)
                    myString.append('<<')
        return myString

    def get_fullmap_str(self):
        objMap = []
        # find groups without parents
        for k, group in self.elements.items():
            parents = group.get_parents()
            if not parents or len(parents) == 0:
                objMap.append(group)
        objMap = sorted(objMap, key=lambda t: t.sort_level_key())
        # go down the hierarchy...
        fullmap = []
        for group in objMap:
            k = group.getID()
            fullmap.append(k)
            fullmap += group.get_submap_str()
        return fullmap

    def get_class_acronym(self):
        return 'group'

    def get_linked(self,parent):
        a_type = parent.get_type()
        result = []
        if a_type == self.get_type():
            result = parent.get_all_children([], None)
        return result


class AllGrUsage(AllGroups):
    def __init__(self, config):
        AllGroups.__init__(self, 'gu', GrUsage.__name__, config)
        self.fieldnames = ["begin", "gu_id",
                           "active", "acronym", 'rank', "remark", "user"]
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
            listtm = e.get_hierarchy_tm([], None)
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

    def component_options(self, usage, selec_type, selec_id, lang):
        c = self.config
        if usage == '0':  # DON'T MOVE transfer (just check time spent)
            v = c.getObject(selec_id, selec_type)
            options = '<option value="' + selec_type + '_' + selec_id + '" selected>' + v.fields[
                'acronym'] + ' - ' + webnet.htmlquote(v.getName(lang)) + '</option>'
        else:
            usages = []
            aUsage = self.get(usage)
            if aUsage:
                usages = aUsage.get_all_children(usages, c.AllGrUsage)
                usages.append(usage)
            options = ""
            first = True
            for k in c.AllPlaces.get_sorted_hierarchy():
                v = c.AllPlaces.get(k)
                if v and v.isActive():
                    curr_group = v.fields['gu_id']
                    if not usages or (curr_group and curr_group in usages):
                        if first:
                            options += '<optgroup label="' + webnet.htmlquote(c.getMessage('place', lang)) + '">'
                            first = False
                        options += '<option value="p_' + k + '"'
                        if selec_type == 'p' and selec_id == k:
                            options += 'selected'
                        options += '>' + v.fields['acronym'] + ' - ' + webnet.htmlquote(v.getName(lang)) + '</option>'
            first = True
            for k in c.AllEquipments.get_sorted_hierarchy():
                v = c.AllEquipments.get(k)
                if v and v.isActive():
                    curr_group = v.fields['gu_id']
                    if not usages or (curr_group and curr_group in usages):
                        if first:
                            options += '<optgroup label="' + webnet.htmlquote(c.getMessage('equipment', lang)) + '">'
                            first = False
                        options += '<option value="e_' + k + '"'
                        if selec_type == 'e' and selec_id == k:
                            options += 'selected'
                        options += '>' + v.fields['acronym'] + ' - ' + webnet.htmlquote(v.getName(lang)) + '</option>'
            first = True
            for k in c.AllContainers.get_sorted_hierarchy():
                v = c.AllContainers.get(k)
                if v and v.isActive():
                    curr_group = v.fields['gu_id']
                    if not usages or (curr_group and curr_group in usages):
                        if first:
                            options += '<optgroup label="' + webnet.htmlquote(c.getMessage('container', lang)) + '">'
                            first = False
                        options += '<option value="e_' + k + '"'
                        if selec_type == 'c' and selec_id == k:
                            options += 'selected'
                        options += '>' + v.fields['acronym'] + ' - ' + webnet.htmlquote(v.getName(lang)) + '</option>'
        return options

class AllGrRecipe(AllGroups):
    def __init__(self, config):
        AllGroups.__init__(self, 'gr', GrRecipe.__name__, config)
        self.fieldnames = ["begin", "gr_id", "gu_id", "provider_gf_id", "buyer_gf_id",
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
                csvfile.write('\t' + self.fieldcontrols[tmp])
                tmp = tmp + 1
            csvfile.write('\n')

    def load_controls(self):
        with open(self.file_of_controls) as csvfile:
            reader = unicodecsv.DictReader(csvfile, delimiter="\t")
            for row in reader:
                type = row['object_type']
                id = row['object_id']
                if id:
                    currObject = self.config.get_object(type, id)
                    if currObject:
                        currObject.add_checkpoint(row['h_id'], row['time'] if 'time' in row else row['begin'])

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

    def get_admin(self):
        return self.findAcronym(KEY_ADMIN)


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
                      'lora',
                      'radio',
                      'http',
                      'json',
                      'cputemp',
                      'system']

    def __init__(self, config):
        AllObjects.__init__(self, 's', Sensor.__name__, config)
        self.fieldnames = ['begin', 's_id', 'c_id', 'p_id', 'e_id', 'm_id', \
                           'active', 'acronym', 'remark', 'channel', 'sensor', \
                           'subsensor', 'valuetype', 'formula', \
                           'lapse1', 'lapse2', 'lapse3'] \
                          + alarmFields + ['user']
        self.fieldtranslate = ['begin', 'lang', 's_id', 'name', 'user']
        self.add_query_channels_from_hardconfig()
        for k in self._queryChannels:
            config.channels[k] = {}

    def newObject(self):
        return Sensor()

    def get_class_acronym(self):
        return 'sensor'

    def get_group_type(self):
        return 'm'

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

    def update(self, timestamp):
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
            if sensor.isActive() and sensor.fields['channel'] in self._queryChannels:
                value, cache = sensor.get_value_sensor(self.config, timestamp, get_cache(sensor))
                sensor.update(timestamp, value, self.config)
                if cache is not None:
                    set_cache(sensor, cache)

    def check_rrd(self):
        for k, v in self.elements.items():
            filename = os.path.join(DIR_RRD, v.getRRDName())
            if not os.path.exists(filename):
                v.createRRD()

    def storeLoraValue(self, inputData):
        if not 'M' in inputData or not inputData['M']:
            return
        module = inputData['M']
        if 'R' in inputData and inputData['R']: #RSSI
            rssi = int(inputData['R'])
        else:
            rssi = 0
        stamp = None
        if 'H' in inputData and inputData['H']:
            try:
                stamp = inputData['H']
            except:
                stamp = None
        if not stamp:
            stamp = useful.get_timestamp()
        self.config.set_channel_access('lora',module,rssi,stamp)

        noDots = {ord(' '): None, ord('.'): None}
        for key, value in inputData.items():
            if key and value and not key in ['H','M']:
                currSensor = None
                for sensor in self.config.AllSensors.elements:
                    currSensor = self.config.AllSensors.elements[sensor]
                    if currSensor.isActive():
                        try:
                            if (unicode(currSensor.fields['sensor']).translate(noDots) == unicode(module) ) \
                                and (unicode(currSensor.fields['subsensor']).translate(noDots) \
                                        == unicode(key).translate(noDots)):
                                if not currSensor.fields['formula'] == '':
                                    value = unicode(eval(currSensor.fields['formula']))
                                print( u"Sensor LORA-" + currSensor.fields['sensor'] + u": " +
                                        currSensor.fields['acronym'] + u" = " + unicode(value))
                                if key == 'G':
                                    try:
                                        #nfc_uid = hex(long(value)).zfill(14)
                                        nfc_uid = value.upper()
                                        print ("NFC="+nfc_uid)
                                        if len(nfc_uid) == 12: # Patch for truncated nfc_uid read by 1-wire simulation
                                            for i in range(0,255):
                                                suff = (hex(i)[2:]).zfill(2).upper()
                                                elem = self.config.AllBarcodes.barcode_to_item(nfc_uid+suff, "N")
                                                if elem:
                                                    break
                                        else:
                                            elem = self.config.AllBarcodes.barcode_to_item(nfc_uid, "N")
                                        if elem:
                                            print ("Found:"+elem.getTypeId())
                                            type = elem.get_type()
                                            if type in TRANSFERABLE_TYPES:
                                                where = currSensor.get_component(self.config)
                                                print ("Move To:" + where.getTypeId())
                                                if not elem.is_actual_position (where.get_type(), where.getID(), self.config):
                                                    newTransfer = Transfer(self.config)
                                                    newTransfer.set_position(where.getTypeId())
                                                    newTransfer.set_object(elem.getTypeId(),currSensor.default_user)
                                                    newTransfer.save(self.config, currSensor.default_user)
                                                    print ("SAVED!")
                                            elif type == self.config.AllUsers.get_type():
                                                currSensor.default_user = elem

                                    except:
                                        traceback.print_exc()
                                        print "Invalid NFC UID: " + inputData['G']
                                else:
                                    currSensor.update(stamp, value, self.config)
                        except:
                            traceback.print_exc()
                            print "Error in formula, " + currSensor.fields['acronym'] + ": " + \
                                  currSensor.fields['formula']

class AllBatches(AllObjects):

    def __init__(self, config):
        AllObjects.__init__(self, 'b', Batch.__name__, config)
        self.fieldnames = ["begin", "b_id", "active", "acronym",
                           "basicqt", "m_id", "time", "cost", "fixed_cost", "remark",
                           "provider_id", "provider_ref", "buyer_id", "buyer_ref",
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
        # print recipes
        # print usages
        for k, e in self.elements.items():
            if e.fields['gr_id'] in recipes:
                batches.append(e)
        return self.sort_hierarchy_objects(batches)

    def get_batches_for_recipe_usage(self, recipes, usages):
        batches = []
        # print recipes
        # print usages
        for k, e in self.elements.items():
            if e.isActive() and (not e.fields['gr_id'] or (e.fields['gr_id'] in recipes)):
                # print "key="+k+", recipe=",e.fields['gr_id']
                tmp = e.get_last_transfer(self.config)
                if tmp is not None:
                    currObj = self.config.get_object(tmp.fields['cont_type'], tmp.fields['cont_id'])
                    # print currObj.__repr__()+"="+currObj.get_group()
                    if currObj.get_group() in usages:
                        batches.append(e)
        return self.sort_hierarchy_objects(batches)

    def findNextAcronym(self, prefix, totalLen, count=0):
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
        self.fieldnames = ["begin", 'tm_id', 'acronym', \
                           'gu_id', 'h_id', 'rank', 'remark', 'active'] \
                          + alarmFields + ['user']
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
        # QUANTITY must NOT be used, TYPICAL is the right field
        self.fieldnames = ['begin', 'vm_id', 'acronym', 'src', 'dest', \
                           'quantity', 'h_id', 'rank', 'in', 'gu_id', 'remark', 'active'] \
                          + alarmFields + ['user']
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
        self.fieldnames = ['begin', 'dm_id', 'acronym', 'm_id', 'h_id', 'rank', \
                           'remark', 'active'] + alarmFields + ['user']
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
                           'idobject', 'code', 'codetype', 'active', 'user']
        self.fieldtranslate = None
        self.EAN = barcode.get_barcode_class('ean13')

    def load(self):
        AllObjects.check_csv(self, self.file_of_objects)
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
                            conformantFile = open(self.file_of_objects + ".NEW", 'w')
                            print (self.file_of_objects + " will be made conformant")
                            conformantWriter = unicodecsv.DictWriter(conformantFile,
                                                                     delimiter='\t',
                                                                     fieldnames=self.fieldnames,
                                                                     encoding="utf-8")
                            conformantWriter.writeheader()
                if conformantWriter is not None:
                    conformantWriter.writerow(row)
                key = row[self.keyColumn]
                if row['active'] == '0':
                    del self.elements[key]
                elif len(row['code']) > 0:
                    currObject = self.newObject(
                        self.config.get_object(row['type'], row['idobject']))
                    currObject.fields = row
                    if not 'codetype' in currObject.fields: # Old file format
                        currObject.fields['codetype'] = '' # Barcode
                    currObject.id = key
                    self.elements[key] = currObject
        # self.to_pictures()
        if conformantFile is not None:
            conformantFile.close()
            os.rename(self.file_of_objects,
                      self.file_of_objects + '.' + useful.timestamp_to_ISO(useful.get_timestamp()).translate(None,
                                                                                                             " :./-"))
            os.rename(self.file_of_objects + ".NEW", self.file_of_objects)

    def newObject(self, item):
        return Barcode(item)

    def get_barcode_from_object(self, myType, myID, codetype=""):
        for k in self.elements.keys():
            currCode = self.elements[k]
            if currCode.fields['codetype'] == codetype and currCode.element:
                if currCode.element.get_type() == myType \
                        and unicode(currCode.element.getID()) == myID:
                    return k
        return ''

    def unique_barcode(self, some_code, myType, myID):
        v = self.get(some_code)
        if v and (myID != v.fields['idobject'] or myType != v.fields['type']):
            return False
        return True

    def add_barcode(self, item, some_code, codetype, user):
        if self.unique_barcode(some_code, item.get_type(), item.getID()):
            oldBarcode = self.get_barcode_from_object(item.get_type(), item.getID(),codetype)
            if oldBarcode and not oldBarcode == some_code:
                self.delete_barcode(oldBarcode, codetype, user, item)
            self.elements[some_code] = self.create_barcode(item, some_code, codetype, user)

    def delete_barcode(self, oldBarcode, codetype, user, item):
        self.write_csv(oldBarcode, codetype, 0, user, item)
        del self.elements[oldBarcode]

    def write_csv(self, some_code, codetype, active, user, item):
        with open(self.file_of_objects, "a") as csvfile:
            tmpCode = self.create_fields(some_code, codetype, active, user, item)
            writer = unicodecsv.DictWriter(csvfile,
                                           delimiter='\t',
                                           fieldnames=self.fieldnames,
                                           encoding="utf-8")
            writer.writerow(tmpCode)

    def create_barcode(self, item, some_code, codetype, user):
        tmp = self.newObject(item)
        fields = self.create_fields(some_code, codetype, 1, user, item)
        tmp.fields = fields
        self.elements[some_code] = tmp
        tmp.element = item
        self.write_csv(some_code, codetype, 1, user, item)
        return tmp

    def create_fields(self, some_code, codetype, active, user, item):
        fields = {}
        fields['begin'] = useful.now()
        if item is None:
            fields['type'] = self.elements[some_code].element.get_type()
            fields['idobject'] = self.elements[some_code].element.id
        else:
            fields['type'] = item.get_type()
            fields['idobject'] = item.id
        fields['code'] = some_code
        fields['codetype'] = codetype
        fields['active'] = active
        fields["user"] = user.fields['u_id']
        return fields

    def validate_barcode(self, some_code, codetype, aType, anID):
        if not codetype: #Barcode EAN
            if len(some_code) < 12 or len(some_code) > 13:
                return False
            try:
                ean = self.EAN(some_code)
            except:
                traceback.print_exc()
                return False
        elif codetype == 'N': #NFC
            if len(some_code) < 12:
                return False
            #if len(some_code) != 14: # 14 hex digits
            #    return False
            try:
                test = long(some_code,16)
            except:
                traceback.print_exc()
                return False
        return self.unique_barcode(some_code, aType, anID)

    ##    def to_pictures(self):
    ##        for k, v in self.elements.items():
    ##            v.barcode_picture()

    def barcode_to_item(self, some_code,codetype=""):
        elem = self.get(some_code)
        if elem and codetype == elem.fields['codetype']:
            return self.config.get_object(elem.fields['type'], elem.fields['idobject'])
        else:
            return None

    def get_class_acronym(self):
        return 'barcode'

class ConnectedUser():

    def __init__(self, user):
        self.cuser = user
        self.datetime = time.time()
        self.initial = self.datetime
        self.completeMenu = False
        self.pin = None
        self.where = None
        self.how = None
        self.nfc = None

    def update(self):
        self.datetime = time.time()

    def pinned(self,type=''):
        if not type:
            if self.pin:
                return self.pin.getTypeId()
            if self.how:
                return self.how.getTypeId()
            if self.where:
                return self.where.getTypeId()
        elif type == 'b':
            if self.pin:
                return self.pin.getTypeId()
        elif type == 'h':
            if self.how:
                return self.how.getTypeId()
        else:
            if self.where:
                return self.where.getTypeId()
        return ''

    def pinit(self,type,obj):
        if obj:
            if type == 'b':
                self.pin = obj
            elif type == 'h':
                self.how = obj
            else:
                self.where = obj
        else:
            if type == 'b':
                self.pin = None
            elif type == 'h':
                self.how = None
            else:
                self.where = None

    def test(self, c, url):
        infoCookie = self.cuser.fields['mail'] + ',' + self.cuser.fields['password'] + ',' + (
            '1' if self.completeMenu else '0')
        cookies = {'akuinoELSA': infoCookie}
        r = requests.get("http://localhost" + url, cookies=cookies)
        if r.status_code != requests.codes.ok:
            return "<p>" + url + " : status=" + unicode(r.status_code)
        output = r.text
        if "internal server error" in output:
            return "<p>" + url + " : " + output
        if len(output) < 2000:
            return "<p>" + url + " : very short=" + output
        if "Please log-in" in output:
            return "<p>" + url + " : log-in=" + output
        if "ELSA Batch Recipes Map" in output:
            return "<p>" + url + " : root=" + output
        return ""


class AllConnectedUsers():

    def __init__(self):
        self.users = {}

    def __getitem__(self, key):
        return self.users[key]

    def addUser(self, user):
        self.removeOld()
        mail = user.fields['mail'].lower()
        if mail not in self.users:
            self.users[mail] = ConnectedUser(user)
        else:
            self.users[mail].update()
        return self.users[mail]

    def removeOld(self):
        updatetime = time.time()
        for mail, connecteduser in self.users.items():
            if (updatetime - connecteduser.datetime) > CONNECTION_TIMEOUT:
                del self.users[mail]

    def isConnected(self, mail, password):
        self.removeOld()
        mail = mail.lower()
        if mail in self.users:
            user = self.users[mail].cuser
            if user.checkPassword(password):
                self.users[mail].update()
                return self.users[mail]
        return None

    def getLanguage(self, mail):
        mail = mail.lower()
        if mail in self.users:
            return self.users[mail].cuser.fields['language']
        return 'english'

    def disconnect(self, connected):
        if connected and connected.cuser:
            mail = connected.cuser.fields['mail'].lower()
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
        if not self.isActive():
            return False
        return self.fields['password'] == password

    def get_type(self):
        return 'u'

    def get_class_acronym(self):
        return 'user'

    def validate_form(self, data, configuration, user):
        tmp = super(User, self).validate_form(data, configuration, user)
        if tmp is True:
            tmp = ''
        lang = user.fields['language']

        level = user.fields['accesslevel'] if user.fields['accesslevel'] else (
            '4' if user.adminAllowed(configuration) else '3')
        if level < data['accesslevel']:
            tmp += configuration.getMessage('accesslevelrules', lang) + '\n'

        if data['password'] and len(data['password']) < 8:
            tmp += configuration.getMessage('passwordrules', lang) + '\n'

        if tmp == '':
            return True
        return tmp

    def set_value_from_data(self, data, c, user):
        super(User, self).set_value_from_data(data, c, user)
        tmp = ['phone', 'mail', 'language', 'addr1', 'addr2', 'addr3', 'vat']
        for elem in tmp:
            self.fields[elem] = data[elem]
        level = user.fields['accesslevel'] if user.fields['accesslevel'] else ('4' if user.adminAllowed(c) else '3')
        if (level >= data['accesslevel']) and (level >= self.fields['accesslevel']):
            self.fields['accesslevel'] = data['accesslevel']

        if not self.fields['registration']:
            self.fields['registration'] = useful.now()
        if data['password']:
            self.fields['password'] = useful.encrypt(
                data['password'], self.fields['registration'])
        if 'donotdisturb' in data:
            self.fields['donotdisturb'] = '1'
        else:
            self.fields['donotdisturb'] = '0'

        self.fields['gf_id'] = data['group']
        self.save(c, user)

    def get_group(self):
        return self.fields['gf_id']

    def adminAllowed(self, c):
        if self.fields['accesslevel'] > '3':
            return True
        user_group = self.get_group()
        if user_group and user_group in c.AllGrFunction.elements:
            aGroup = c.AllGrFunction.elements[user_group]
            if aGroup.fields['acronym'].lower() == KEY_ADMIN:
                return True
            for user_group in aGroup.get_all_parents([], c.AllGrFunction):
                bGroup = c.AllGrFunction.elements[user_group]
                if bGroup.fields['acronym'].lower() == KEY_ADMIN:
                    return True
        return False

    def updateAllowed(self, c, type):
        if self.fields['accesslevel']:
            if self.fields['accesslevel'] < '3':
                return False
            if self.fields['accesslevel'] > '3':
                return True
        user_group = self.get_group()
        if user_group and user_group in c.AllGrFunction.elements:
            key_upd = u"upd_" + type
            aGroup = c.AllGrFunction.elements[user_group]
            if aGroup.fields['acronym'].lower() == KEY_ADMIN:
                return True
            if aGroup.fields['acronym'].lower() == key_upd:
                return True
            for user_group in aGroup.get_all_parents([], c.AllGrFunction):
                bGroup = c.AllGrFunction.elements[user_group]
                if bGroup.fields['acronym'].lower() == KEY_ADMIN:
                    return True
                if bGroup.fields['acronym'].lower() == key_upd:
                    return True
        return False

    def allowed(self, c):
        if self.fields['accesslevel']:
            if self.fields['accesslevel'] < '3':
                return ""
            if self.fields['accesslevel'] > '3':
                return " admin" + ALL_UPDATE_GROUPS
        user_group = self.get_group()
        result = " "
        if user_group and user_group in c.AllGrFunction.elements:
            key_upd = u"upd_" + self.get_type()
            aGroup = c.AllGrFunction.elements[user_group]
            result += aGroup.fields['acronym'].lower() + " "
            for user_group in aGroup.get_all_parents([], c.AllGrFunction):
                bGroup = c.AllGrFunction.elements[user_group]
                result += bGroup.fields['acronym'].lower() + " "
        if " admin " in result:  # all is updatable then !
            result += ALL_UPDATE_GROUPS
        return result

    def connectedSince(self, c):
        if self.fields['mail']:
            if self.fields['mail'] in c.connectedUsers.users:
                connexion = c.connectedUsers.users[self.fields['mail']]
                if connexion:
                    return useful.date_to_ISO(connexion.initial)
        return ""

    def pinning(self, c):
        if self.fields['mail']:
            if self.fields['mail'] in c.connectedUsers.users:
                connexion = c.connectedUsers.users[self.fields['mail']]
                if connexion:
                    return connexion.pin
        return None

    def get_batches(self, c):
        result = []
        for k, b in c.AllBatches.elements.items():
            if b.isActive() and (self.getID() in [b.get_last_user(c), b.fields['buyer_id'], b.fields['provider_id']]):
                result.append(b)
        return c.AllBatches.sort_hierarchy_objects(result)


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

    def getAll(self):
        return self.config.AllEquipments

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

    def isAlarmed(self, c):
        for kSensor, aSensor in c.AllSensors.elements.items():
            if aSensor.isAlarmed(c) and aSensor.is_in_component('e', self.id):
                return True
        return False

    def validate_form(self, data, configuration, user):
        return super(Equipment, self).validate_form(data, configuration, user)

    def set_value_from_data(self, data, c, user):
        super(Equipment, self).set_value_from_data(data, c, user)
        self.fields['colorgraph'] = data['colorgraph']
        self.fields['gu_id'] = data['group']
        self.save(c, user)

    def get_batches(self, c):
        result = []
        for k, b in c.AllBatches.elements.items():
            if b.isActive():
                here = b.get_actual_position_here(c)
                if here and (here.getTypeId() == self.getTypeId()):
                    result.append(b)
        return c.AllBatches.sort_hierarchy_objects(result)

    def get_group(self):
        return self.fields['gu_id']

    def isPinned(self,connected):
        return self == connected.where


class Container(ConfigurationObject):

    def __init__(self, config):
        ConfigurationObject.__init__(self)
        self.config = config

    def getAll(self):
        return self.config.AllContainers

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

    def isAlarmed(self, c):
        for kSensor, aSensor in c.AllSensors.elements.items():
            if aSensor.isAlarmed(c) and aSensor.is_in_component('c', self.id):
                return True
        return False

    def validate_form(self, data, configuration, user):
        return super(Container, self).validate_form(data, configuration, user)

    def set_value_from_data(self, data, c, user):
        super(Container, self).set_value_from_data(data, c, user)
        self.fields['colorgraph'] = data['colorgraph']
        self.fields['gu_id'] = data['group']
        self.save(c, user)

    def get_batches(self, c):
        result = []
        for k, b in c.AllBatches.elements.items():
            if b.isActive():
                here = b.get_actual_position_here(c)
                if here and (here.getTypeId() == self.getTypeId()):
                    result.append(b)
        return c.AllBatches.sort_hierarchy_objects(result)

    def get_group(self):
        return self.fields['gu_id']

    def isPinned(self,connected):
        return self == connected.where


class AlarmingObject(ConfigurationObject):

    def __init__(self):
        ConfigurationObject.__init__(self)
        self.actualAlarm = 'typical'
        self.degreeAlarm = 0
        self.countAlarm = 0
        self.colorAlarm = valueCategs[0].color
        self.colorTextAlarm = valueCategs[0].text_color
        self.lastvalue = None
        self.time = ""

    def get_alarm(self, model=None):
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
            return bounds['a_none']

    def setCorrectAlarmValue(self, model=None):
        bounds = model.fields if model else self.fields
        if bounds['lapse1'] == '':
            bounds['lapse1'] = "99999999"
        if bounds['lapse2'] == '':
            bounds['lapse2'] = "99999999"
        if bounds['lapse3'] == '':
            bounds['lapse3'] = "99999999"

    def set_alarm(self, c, alarmlog):
        self.actualAlarm = alarmlog.fields['typealarm']
        try:
            self.degreeAlarm = int(alarmlog.fields['degree'])
        except:
            self.degreeAlarm = 0
        Aname, Aacronym, self.colorAlarm, self.colorTextAlarm = c.triple(alarmlog.fields['typealarm'])
        self.lastvalue = alarmlog.fields['value']
        self.time = alarmlog.fields['alarmtime']


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

    def sort_key(self):
        return self.fields['time']

    def get_quantity_string(self):
        return self.fields['value']

    def add_component(self, component):
        type, id = splitId(component)
        self.fields['object_id'] = id
        self.fields['object_type'] = type

    def add_measure(self, measure):
        if not measure == 'None':
            self.fields['m_id'] = unicode(measure)
        else:
            self.fields['m_id'] = ''

    def validate_form(self, data, configuration, user):
        tmp = ''
        lang = user.fields['language']
        try:
            value = useful.date_to_ISO(data['time'])
        except:
            traceback.print_exc()
            tmp += configuration.getMessage('timerules', lang) + '\n'

        if 'value' in data and data['measure'] == u'None':
            if not data['value'] == '':
                tmp += configuration.getMessage('datarules', lang) + '\n'
        elif 'value' in data:
            try:
                value = float(data['value'])
            except:
                tmp += configuration.getMessage('floatrules', lang) + ' ' + data['value'] + '\n'
        aType, anId = splitId(data['component'])
        if not aType or not anId:
            tmp += configuration.getMessage('componentrules', lang) + '\n'
        elif not configuration.is_component(aType):
            tmp += configuration.getMessage('componentrules', lang) + ' ' + data['component'] + '\n'
        if tmp == '':
            return True
        return tmp

    def set_value_from_data(self, data, c, user):
        # SUPER is NOT called, beware!
        if self.fields['object_type'] != '' \
                and self.fields['object_id'] != '':
            c.get_object(self.fields['object_type'], self.fields['object_id']) \
                .remove_data(self)
        tmp = ['time', 'value', 'remark']
        for elem in tmp:
            self.fields[elem] = data[elem]
        if not self.fields['time']:
            self.fields['time'] = useful.now()
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
            typeAlarm, symbAlarm, self.colorAlarm, self.colorTextAlarm = self.getTypeAlarm(data['value'], model)
            self.actualAlarm = typeAlarm
            alarmCode = self.get_alarm(model);
        if ('a_id' in data) and data['a_id']:
            # TODO: Manual Alarm, not so "typical"
            if not self.actualAlarm:
                self.actualAlarm = "typical"
            alarmCode = data['a_id']
        anAlarm = c.AllAlarms.get(alarmCode)
        if anAlarm:
            self.fields['al_id'] = anAlarm.launch_alarm(self, c)
        if self.isActive():
            c.get_object(self.fields['object_type'], self.fields['object_id']) \
                .add_data(self)
        else:
            c.get_object(self.fields['object_type'], self.fields['object_id']) \
                .remove_data(self)
        self.save(c, user)

    def get_class_acronym(self):
        return 'manualdata'

    # WHERE the observation was done
    def get_component(self, config):
        if not self.fields['object_id']:
            return None
        if self.fields['object_type']:
            allObjs = config.findAll(self.fields['object_type'])
        else:
            allObjs = config.AllBatches
        if self.fields['object_id'] in allObjs.elements:
            return allObjs.elements[self.fields['object_id']]
        else:
            return None

    def get_model(self, config):
        return config.AllManualDataModels.get(self.fields['dm_id'])


class Pouring(AlarmingObject):
    def __init__(self):
        AlarmingObject.__init__(self)

    def __str__(self):
        string = "\nPouring :"
        for field in self.fields:
            string = string + "\n" + field + " : " + self.fields[field]
        return string + "\n"

    def get_type(self):
        return 'v'

    def sort_key(self):
        return self.fields['time']

    def get_quantity_string(self):
        return self.fields['quantity']

    def add_measure(self, measure):
        tmp = measure.split('_')
        self.fields['m_id'] = tmp[-1]

    def validate_form(self, data, configuration, user):
        tmp = ''
        lang = user.fields['language']
        try:
            value = useful.date_to_ISO(data['time'])
        except:
            tmp += configuration.getMessage('timerules', lang) + '\n'
        try:
            value = float(data['quantity'])
        except:
            tmp += configuration.getMessage('floatrules', lang) + '\n'
        try:
            b_id = data['src']
            if not b_id in configuration.AllBatches.elements.keys():
                tmp += configuration.getMessage('batchrules1', lang) + '\n'
        except:
            tmp += configuration.getMessage('batchrules1', lang) + '\n'
        try:
            b_id = data['dest']
            if not b_id in configuration.AllBatches.elements.keys():
                tmp += configuration.getMessage('batchrules2', lang) + '\n'
        except:
            tmp += configuration.getMessage('batchrules2', lang) + '\n'
        if data['src'] == data['dest']:
            tmp += configuration.getMessage('batchrules3', lang) + '\n'

        if tmp == '':
            return True
        return tmp

    def get_measure_in_context(self, c, currObject):
        if self.fields['src']:
            if self.fields['src'] in c.AllBatches.elements:
                aBatch = c.AllBatches.elements[self.fields['src']]
                return aBatch.get_measure(c)
        elif currObject:
            return currObject.get_measure(c)
        return ""

    def get_unit_in_context(self, c, currObject):
        if self.fields['src']:
            if self.fields['src'] in c.AllBatches.elements:
                aBatch = c.AllBatches.elements[self.fields['src']]
                return aBatch.get_unit(c)
        elif currObject:
            return currObject.get_unit(c)
        return ""

    def set_value_from_data(self, data, c, user):
        # SUPER is NOT called, beware!
        if self.fields['src'] != '' and self.fields['dest'] != '':
            c.AllBatches.elements[self.fields['src']].remove_source(self)
            c.AllBatches.elements[self.fields['dest']].remove_destination(self)
        tmp = ['time', 'remark', 'src', 'dest', 'quantity']
        for elem in tmp:
            self.fields[elem] = data[elem]
        if not self.fields['time']:
            self.fields['time'] = useful.now()
        self.fields['m_id'] = c.AllBatches.elements[data['src']].fields['m_id']
        if 'h_id' in data:
            self.fields['h_id'] = data['h_id']
        else:
            self.fields['h_id'] = ''
        alarmCode = ""
        if ('origin' in data) and data['origin']:
            self.fields['vm_id'] = data['origin']
            model = c.AllPouringModels.get(data['origin'])
            if model:
                typeAlarm, symbAlarm, self.colorAlarm, self.colorTextAlarm = self.getTypeAlarm(data['quantity'], model)
                self.actualAlarm = typeAlarm
                alarmCode = self.get_alarm(model);
        if ('a_id' in data) and data['a_id']:
            # TODO: Manual Alarm, not so "typical"
            self.actualAlarm = "typical"
            alarmCode = data['a_id']
        anAlarm = c.AllAlarms.get(alarmCode)
        if anAlarm:
            alid = anAlarm.launch_alarm(self, c)
            if alid:
                self.fields['al_id'] = alid

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
    def get_source(self, config):
        if not self.fields['src']:
            return None
        allObjs = config.AllBatches
        if self.fields['src'] in allObjs.elements:
            return allObjs.elements[self.fields['src']]
        else:
            return None

    # WHERE it is moved
    def get_component(self, config):
        if not self.fields['dest']:
            return None
        allObjs = config.AllBatches
        if self.fields['dest'] in allObjs.elements:
            return allObjs.elements[self.fields['dest']]
        return None

    def get_model(self, config):
        return config.AllPouringModels.get(self.fields['vm_id'])


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

    def inherited(self, fname):
        done = set()
        for p in self.parents:
            if not p in done:
                done.add(p)
                parent = self.getAll().get(p)
                if parent:
                    value = parent.fields[fname]
                    if value:
                        return value
                    else:
                        value = parent.inherited(fname)
                        if value:
                            return value
        return ""

    def field(self, fname):
        if self.fields[fname]:
            return self.fields[fname]
        else:
            return self.inherited(fname)

    def validate_form(self, data, configuration, user):
        tmp = super(Group, self).validate_form(data, configuration, user)
        if tmp is True:
            tmp = ''
        lang = user.fields['language']
        for k, v in configuration.findAllFromObject(self).elements.items():
            if k in data:
                if self.getID() in v.parents or self.getID() in v.siblings:
                    tmp += configuration.getMessage('grouprules', lang) + '\n'
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
                                           fieldnames=configuration.findAllFromObject(self).fieldrelations,
                                           encoding="utf-8")
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
                    .get_object(self.get_type(), i) \
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

    def get_all_parents(self, parents=[], allObj=None):
        if not allObj:
            allObj = self.config.findAll(self.get_type())
        for e in self.parents:
            if e and e not in parents:
                parents.append(e)
                rec = allObj.get(e)
                if rec:
                    parents = rec.get_all_parents(parents, allObj)
        return parents

    def get_all_children(self, children=[], allObj=None):
        if not allObj:
            allObj = self.config.findAll(self.get_type())
        for e in self.children:
            if e and e not in children:
                children.append(e)
                rec = allObj.get(e)
                if rec:
                    children = rec.get_all_children(children, allObj)
        return children

    def get_acronym_hierarchy(self):
        allObj = self.config.findAll(self.get_type())
        parents = self.get_all_parents([], allObj)
        result = ""
        for key in reversed(parents):
            e = allObj.elements[key]
            result += e.get_acronym() + " "
        return result + self.get_acronym()

    # Looking DOWN
    def get_submap_str(self):
        children = self.get_children()
        # print self.fields['acronym']+", children="+unicode(children)
        submap = []
        if children and len(children) > 0:
            submap.append('>>')
            allObj = self.config.findAll(self.get_type())
            childObj = []
            for k in children:
                if k and k in allObj.elements:
                    childObj.append(allObj.elements[k])
            if len(childObj):
                childObj = sorted(childObj, key=lambda t: t.sort_level_key())
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
        if children and len(children) > 0:
            submap.append('>>')
            allObj = self.config.findAll(self.get_type())
            childObj = []
            for k in children:
                if k and k in allObj.elements:
                    childObj.append(allObj.elements[k])
            if len(childObj):
                childObj = sorted(childObj, key=lambda t: t.sort_level_key())
                for elem in childObj:
                    k = elem.getID()
                    submap.append(k)
                    submap += elem.get_supermap_str()
            submap.append('<<')
        return submap

    def proposedMemberAcronym(self, configuration):
        prefix = self.fields['acronym'] + u"_"


class GrUsage(Group):
    def __init__(self, config):
        Group.__init__(self, config)
        self.keyColumn = 'gu_id'

    def get_type(self):
        return 'gu'

    def getAll(self):
        return self.config.AllGrUsage

    def get_class_acronym(self):
        return 'guse'

    def validate_form(self, data, configuration, user):
        tmp = Group.validate_form(self, data, configuration, user)
        if tmp == '':
            return True
        return tmp

    def set_value_from_data(self, data, c, user):
        super(GrUsage, self).set_value_from_data(data, c, user)
        self.fields['rank'] = data['rank']
        self.save(c, user)

    def get_batches(self, c):
        result = []
        for k, b in c.AllBatches.elements.items():
            if b.isActive():
                here = b.get_actual_position_here(c)
                if here and here.isActive() and here.get_group() == self.getID():
                    result.append(b)
        return c.AllBatches.sort_hierarchy_objects(result)

    def get_members(self):
        result = []
        for k, b in self.config.AllPlaces.elements.items():
            if b.get_group() == self.getID() and b.isActive():
                result.append(b)
        for k, b in self.config.AllEquipments.elements.items():
            if b.get_group() == self.getID() and b.isActive():
                result.append(b)
        for k, b in self.config.AllContainers.elements.items():
            if b.get_group() == self.getID() and b.isActive():
                result.append(b)
        return result


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

    def isPinned(self,connected):
        return self == connected.how

    def get_class_acronym(self):
        return 'checkpoint'

    def validate_form(self, data, configuration, user):
        tmp = Group.validate_form(self, data, configuration, user)
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
                self.tm.append(self.tm.getID())

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
        listdm = self.get_hierarchy_dm([], self)
        listvm = self.get_hierarchy_vm([], self)
        listtm = self.get_hierarchy_tm([], self)
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
            tmp += self.config.getMessage('timerules', lang) + '\n'
        for m in model:
            type = m.get_type()
            if type == 'dm':
                try:
                    value = float(data['dm_value_' + unicode(countdm)])
                except:
                    tmp += self.config.getMessage('floatrules', lang) \
                           + ' ' + data['dm_value_' + unicode(countdm)] + '\n'
                countdm += 1
            elif type == 'vm':
                try:
                    value = float(data['vm_quantity_' + unicode(countvm)])
                except:
                    tmp += self.config.getMessage('floatrules', lang) \
                           + ' ' + data['vm_quantity_' + unicode(countvm)] + '\n'
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
                tmp = self.create_data(data, type, countdm, user)
                countdm += 1
            elif type == 'tm':
                tmp = self.create_data(data, type, counttm, user)
                counttm += 1
            elif type == 'vm':
                tmp = self.create_data(data, type, countvm, user)
                countvm += 1
            if tmp:
                currObject.set_value_from_data(tmp, self.config, user)
        type, id = splitId(data['batch'])
        self.write_control(type, id, user)
        self.config.get_object(type, id).add_checkpoint(self.getID(), data['time'])

    def create_data(self, data, type, count, user):
        batch = data['batch']
        time = data['time']
        tmp = {}
        tmp['time'] = time
        tmp['active'] = '1'
        tmp['h_id'] = self.getID()
        count = unicode(count)
        if type == 'dm':
            tmp['component'] = batch
            tmp['origin'] = data['dm_id_' + count]
            tmp['remark'] = data['dm_remark_' + count]
            tmp['measure'] = data['dm_measure_' + count]
            tmp['value'] = data['dm_value_' + count]
        elif type == 'tm':
            tmp['object'] = batch
            tmp['origin'] = data['tm_id_' + count]
            tmp['position'] = data['tm_position_' + count]
            tmp['remark'] = data['tm_remark_' + count]
        elif type == 'vm':
            tmp['quantity'] = data['vm_quantity_' + count]
            tmp['origin'] = data['vm_id_' + count]
            if 'vm_src_' + count in data:  # input
                tmp['src'] = data['vm_src_' + count]
                tmp['dest'] = batch.split('_')[1]
            elif 'vm_dest_' + count in data:
                tmp['dest'] = data['vm_dest_' + count]
                tmp['src'] = batch.split('_')[1]
                if tmp['dest'].startswith('b_'):  # existing batch
                    tmp['dest'] = tmp['dest'].split('_')[1]
                else:  # sub-batch
                    currBatch = self.config.AllBatches.get(tmp['src'])
                    if currBatch:
                        subbatch = currBatch.subbatch(user, 1, self.getID(),
                                                      tmp['dest'])  # After SUB, key of the component to start with...
                        if not subbatch:
                            return None
                        tmp['dest'] = subbatch.getID()
                    else:
                        return None
            else:
                return None
            tmp['remark'] = data['vm_remark_' + count]
        else:
            return None
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

    def owns(self, type, id):
        elems = []
        if type == "dm":
            elems = self.get_hierarchy_dm([], self)
        elif type == "vm":
            elems = self.get_hierarchy_vm([], self)
        elif type == "tm":
            elems = self.get_hierarchy_tm([], self)
        return id in elems;

    def get_batches(self, c):
        result = []
        for k in self.batches:
            b = c.AllBatches.get(k)
            if b and b.isActive():
                result.append(b)
        return c.AllBatches.sort_hierarchy_objects(result)

    def get_members(self):
        return self.get_model_sorted()

class GrRecipe(Group):
    def __init__(self, config):
        Group.__init__(self, config)
        self.keyColumn = 'gr_id'

    def get_type(self):
        return 'gr'

    def getAll(self):
        return self.config.AllGrRecipe

    def get_class_acronym(self):
        return 'grecipe'

    def get_measure(self, c):
        kmeasure = self.field('m_id')
        return c.AllMeasures.get(kmeasure)

    def get_quantity_string(self):
        return self.field('basicqt')

    def get_total_cost(self):
        return useful.str_float(self.field('fixed_cost')) + (
                    useful.str_float(self.field('cost')) * useful.str_float(self.field('basicqt')))

    def validate_form(self, data, configuration, user):
        tmp = super(GrRecipe, self).validate_form(data, configuration, user)
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
        self.fields['buyer_gf_id'] = data['buyer_gf_id']
        self.fields['provider_gf_id'] = data['provider_gf_id']

        self.save(c, user)

    def proposedMemberAcronym(self, configuration):
        prefix = self.fields['acronym'] + u"_" + useful.shortNow() + u"_"
        acro = configuration.AllBatches.findNextAcronym(prefix, len(prefix) + 2, 1)
        if acro:
            return acro
        else:
            return prefix

    def lifespan(self):
        days = self.field("lifespan")
        if days:
            return int(days)
        else:
            return 0

    def get_batches(self, c):
        result = []
        for k, b in c.AllBatches.elements.items():
            if b.get_group() == self.getID() and b.isActive():
                result.append(b)
        return c.AllBatches.sort_hierarchy_objects(result)

    def get_members(self):
        return self.get_batches(self.config)

class GrFunction(Group):
    def __init__(self, config):
        Group.__init__(self, config)
        self.keyColumn = 'gf_id'

    def get_type(self):
        return 'gf'

    def getAll(self):
        return self.config.AllGrFunction

    def get_user_group(self):
        listusers = []
        for k, user in self.config.AllUsers.elements.items():
            if user.fields['gf_id'] in self.children \
                    or user.fields['gf_id'] == self.fields['gf_id']:
                listusers.append(k)
        return listusers

    def get_class_acronym(self):
        return 'gfunction'

    def validate_form(self, data, configuration, user):
        tmp = super(GrFunction, self).validate_form(data, configuration, user)
        if tmp == '':
            return True
        return tmp

    def set_value_from_data(self, data, c, user):
        super(GrFunction, self).set_value_from_data(data, c, user)
        self.save(c, user)

    def get_members(self):
        result = []
        for k, b in self.config.AllUsers.elements.items():
            if b.get_group() == self.getID() and b.isActive():
                result.append(b)
        return self.config.AllUsers.sort_hierarchy_objects(result)

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

    def getAll(self):
        return self.config.AllPlaces

    def get_class_acronym(self):
        return 'place'

    def get_sensors_in_component(self, config):
        listSensor = []
        checklist = []
        checklist.append(['p', self.id])
        for k, v in config.AllEquipments.elements.items():
            transfer = v.get_last_transfer(config)
            if transfer is not None:
                if transfer.fields['cont_type'] == 'e' \
                        and transfer.fields['cont_id'] == self.id:
                    checklist.append(['e', k])
        for k, sensor in config.AllSensors.elements.items():
            for comp, id in checklist:
                if sensor.is_in_component(comp, id):
                    listSensor.append(k)
        return listSensor

    def sort_key(self):
        pref = ""
        usage = self.config.AllGrUsage.get(self.fields['gu_id'])
        if usage:
            pref = usage.fields['rank'].rjust(10)
        return pref + self.fields['acronym'].upper()

    def isAlarmed(self, c):
        for kSensor, aSensor in c.AllSensors.elements.items():
            if aSensor.isAlarmed(c) and aSensor.is_in_component('p', self.id):
                return True
        return False

    def validate_form(self, data, configuration, user):
        return super(Place, self).validate_form(data, configuration, user)

    def set_value_from_data(self, data, c, user):
        super(Place, self).set_value_from_data(data, c, user)
        self.fields['colorgraph'] = data['colorgraph']
        self.fields['gu_id'] = data['group']
        self.save(c, user)

    def get_batches(self, c):
        result = []
        for k, b in c.AllBatches.elements.items():
            if b.isActive():
                here = b.get_actual_position_here(c)
                if here and (here.getTypeId() == self.getTypeId()):
                    result.append(b)
        return c.AllBatches.sort_hierarchy_objects(result)

    def get_group(self):
        return self.fields['gu_id']

    def isPinned(self,connected):
        return self == connected.where


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

    def sort_key(self):
        return self.fields['begin']

    # WHAT is moved
    def get_source(self, config):
        if not self.fields['s_id']:
            return None
        if self.fields['s_type']:
            allObjs = config.findAll(self.fields['s_type'])
        else:
            allObjs = config.AllSensors
        return allObjs.get(self.fields['s_id'])

    def get_quantity_string(self):
        return self.fields['value']

    def get_unit(self, config):
        s = self.get_source(config)
        if s:
            return s.get_unit(config)
        return ""

    def getQtyUnit(self, c, lang="EN"):
        result = self.get_quantity_string()
        unit = self.get_unit(c)
        if unit:
            result += ' ' + unit
        return result

    # WHERE it is moved
    def get_component(self, config):
        if not self.fields['cont_id']:
            return None
        if self.fields['cont_type']:
            allObjs = config.findAll(self.fields['cont_type'])
            return allObjs.get(self.fields['cont_id'])
        return None

    def validate_form(self, data, configuration, user):
        tmp = ''
        lang = user.fields['language']
        try:
            value = useful.date_to_ISO(data['begintime'])
        except:
            traceback.print_exc()
            tmp += configuration.getMessage('timerules', lang) + '\n'
        if tmp == '':
            return True
        return tmp

    ## READ ONLY:
    ##        'begin', 'al_id', 'cont_id', 'cont_type',
    ##        's_id', 's_type', 'value', 'typealarm', 'a_id',
    ##        'alarmtime', 'degree'
    ## May be edited:
    ##    'begintime','completedtime', 'remark', 'active' and 'user' is set automatcally

    def set_value_from_data(self, data, c, user):
        if 'active' in data:
            self.set_active('1')
        else:
            self.set_active('0')

        if 'placeImg' in data and data['placeImg'] != {}:
            if data.placeImg.filename != '':
                filepath = data.placeImg.filename.replace('\\', '/')
                ext = ((filepath.split('/')[-1]).split('.')[-1])
                if ext and ext.lower() in [u'jpg', u'jpeg', u'png']:
                    with open(self.getImagePath(True, ext=("png" if ext.lower() == u"png" else u"jpg")), 'w') as fout:
                        fout.write(data.placeImg.file.read())
        # linkedDocs is treated by caller because "web" object is needed...

        tmp = ['begintime', 'remark']
        for elem in tmp:
            self.fields[elem] = data[elem]
        if not self.fields['begintime']:
            self.fields['begintime'] = useful.now()

        completed = None
        if 'completedtime' in data and data['completedtime']:
            try:
                completed = useful.date_to_ISO(data['completedtime'])
            except:
                completed = useful.now()
        if 'iscompleted' in data and data['iscompleted']:
            if completed:
                self.fields['completedtime'] = completed
            else:
                self.fields['completedtime'] = useful.now()
        else:
            self.fields['completedtime'] = ""

        self.save(c, user)


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
                end = tmp[count + 1].getTimestamp()
            else:
                end = tmpEND
            tmpComponent = tmp[count].get_component(self.config)
            self.transfers.append(tmp[count])
            count += 1
            self.load_transfers(tmpComponent, begin, end)
        self.transfers.sort(key=lambda x: int(x.getTimestamp()), reverse=False)
        while self.transfers and self.transfers[0].fields['object_type'] != 'b':
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
                    if self.countt > (len(self.transfers) - 1):
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
                csvfile.write('\t' + self.fieldnames[tmp])
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
                        for log in reversed(logs):
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
            sensor = self.config.AllSensors.get(a)
            if sensor:
                infos[a] = sensor.fetch(begin, end)
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

        if elem.get_type() in OBSERVABLE_TYPES + ['m']:
            if elem.get_type() == 'b':
                tmp['timestamp'] = useful.date_to_ISO(elem.fields['time'])
                tmp['duration'] = self.get_duration(elem.getTimestamp(), useful.get_timestamp())
                tmp['unit'] = elem.get_unit(self.config)
                tmp['value'] = export_float(elem.get_quantity())

            if self.cond['acronym'] is True:
                tmp[elem.get_type() + '_id'] = elem.fields['acronym']
                if elem.get_type() == 'b':
                    tmp['m_id'] = elem.get_measure(self.config).fields['acronym']
            else:
                tmp[elem.get_type() + '_id'] = elem.getID()
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
                tmp[elem.fields['cont_type'] + '_id'] = \
                self.config.get_object(elem.fields['cont_type'], elem.fields['cont_id']).fields['acronym']
                tmp['sensor'] = (self.config
                    .AllSensors
                    .elements[elem.fields['s_id']]
                    .fields['acronym'])
                tmp['m_id'] = self.config.AllSensors.elements[elem.fields['s_id']].get_measure(self.config).fields[
                    'acronym']
            else:
                tmp[elem.fields['cont_type'] + '_id'] = elem.fields['cont_id']
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
                tmp[elem.fields['object_type'] + '_id'] = \
                self.config.get_object(elem.fields['object_type'], elem.fields['object_id']).fields['acronym']
            else:
                tmp['m_id'] = elem.fields['m_id']
                tmp[elem.fields['object_type'] + '_id'] = elem.fields['object_id']
            tmp['remark'] = elem.fields['remark']
            if self.cond['acronym'] is True:
                tmp['user'] = (self.config
                    .AllUsers
                    .elements[elem.fields['user']]
                    .fields['acronym'])
                tmp[elem.fields['object_type'] + '_id'] = \
                self.config.get_object(elem.fields['object_type'], elem.fields['object_id']).fields['acronym']
            else:
                tmp['user'] = elem.fields['user']
                tmp[elem.fields['object_type'] + '_id'] = elem.fields['object_id']

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
                tmp[elem.fields['cont_type'] + '_id'] = \
                self.config.get_object(elem.fields['cont_type'], elem.fields['cont_id']).fields['acronym']
                if elem.fields['object_type'] != 'b':
                    tmp[elem.fields['object_type'] + '_id'] = \
                    self.config.get_object(elem.fields['object_type'], elem.fields['object_id']).fields['acronym']
                elemtmp = elem.get_component(self.config).get_position_on_time(
                    self.config, elem.fields['time'])
                while elemtmp is not None:
                    tmp[elemtmp.fields['cont_type'] + '_id'] = \
                    self.config.get_object(elemtmp.fields['cont_type'], elemtmp.fields['cont_id']).fields['acronym']
                    elemtmp = elemtmp.get_component(self.config).get_position_on_time(
                        self.config, elemtmp.fields['time'])
            else:
                tmp[elem.fields['cont_type'] + '_id'] = elem.fields['cont_id']
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
        # timestamp = int(end) - int(begin)
        # return useful.timestamp_to_time(timestamp)
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
        glyph = self.fields['glyphname']
        if not glyph:
            return ""
        elif glyph[0] == "*" and len(glyph) > 1:
            return '<span class="halflings' + supp_classes + '">' + glyph[1:] + '</span>'
        else:
            return '<span class="halflings halflings-' + glyph + supp_classes + '"></span>'

    def getGlyph(self):
        glyph = self.fields['glyphname']
        if not glyph:
            return ""
        elif glyph[0] == "*" and len(glyph) > 1:
            return glyph[1:].encode('ascii', 'xmlcharrefreplace')
        else:
            return  HALFLING_UNICODE[glyph].encode('ascii', 'xmlcharrefreplace')

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

    def validate_form(self, data, configuration, user):
        tmp = super(Alarm, self).validate_form(data, configuration, user)
        return tmp

    def set_value_from_data(self, data, c, user):
        super(Alarm, self).set_value_from_data(data, c, user)
        tmp = alarm_fields_for_groups + ['relay1', 'relay2', 'relay1_id', 'relay2_id']
        for elem in tmp:
            self.fields[elem] = data[elem]
        self.save(c, user)

    def get_alarm_message(self, alarmedObject, config, group, lang, alid):
        newFields = {}
        newFields['s_id'] = alarmedObject.getID()
        newFields['s_type'] = alarmedObject.get_type()
        newFields['a_id'] = self.getID()
        newFields['gf_id'] = group
        newFields['alarmtime'] = useful.now()
        newFields['user'] = alarmedObject.fields['user']
        newFields['remark'] = ''
        newFields['active'] = '1'
        specmess = self.getName(lang)
        if alarmedObject.get_type() == 's':
            mess = config.getMessage('alarmmessage', lang)
            cpe = ''
            elem = config.AllContainers.get(alarmedObject.fields['c_id'])
            if elem:
                cpe = config.getMessage('container', lang)
            else:
                elem = config.AllEquipments.get(alarmedObject.fields['e_id'])
                if elem:
                    cpe = config.getMessage('equipment', lang)
                else:
                    elem = config.AllPlaces.get(alarmedObject.fields['p_id'])
                    if elem:
                        cpe = config.getMessage('place', lang)
            if elem:
                newFields['cont_type'] = elem.get_type()
                newFields['cont_id'] = elem.getID()
            newFields['value'] = unicode(alarmedObject.lastvalue)
            newFields['begintime'] = alarmedObject.time
            newFields['typealarm'] = unicode(alarmedObject.actualAlarm)
            newFields['degree'] = unicode(alarmedObject.degreeAlarm)
            newFields['remark'] = unicode.format(mess,
                                                 config.HardConfig.hostname,
                                                 specmess,
                                                 cpe,
                                                 elem.getName(lang) if elem else "",
                                                 elem.fields['acronym'] if elem else "",
                                                 alarmedObject.getName(lang),
                                                 alarmedObject.fields['acronym'],
                                                 alarmedObject.getQtyUnit(config, lang),
                                                 alarmedObject.actualAlarm,
                                                 alarmedObject.time,
                                                 unicode(alarmedObject.degreeAlarm))
        elif alarmedObject.get_type() == 'd':
            mess = config.getMessage('alarmmanual', lang)
            elem = alarmedObject.get_component(config)
            name = config.getMessage(elem.get_class_acronym(), lang)
            newFields['begintime'] = alarmedObject.fields['time']
            if elem:
                newFields['cont_type'] = elem.get_type()
                newFields['cont_id'] = elem.getID()
            newFields['value'] = unicode(alarmedObject.fields['value'])
            newFields['typealarm'] = unicode(alarmedObject.actualAlarm)
            newFields['degree'] = '2'
            newFields['remark'] = unicode.format(mess,
                                                 config.HardConfig.hostname,
                                                 specmess,
                                                 name,
                                                 elem.getName(lang) if elem else "",
                                                 elem.fields['acronym'] if elem else "",
                                                 alarmedObject.getQtyUnit(config, lang),
                                                 alarmedObject.fields['remark'],
                                                 alarmedObject.fields['time'])
        elif alarmedObject.get_type() == 't':
            mess = config.getMessage('alarmmanual', lang)
            elem = alarmedObject.get_source(config)
            compo = alarmedObject.get_component(config)
            name = config.getMessage(elem.get_class_acronym(), lang)
            newFields['begintime'] = alarmedObject.fields['time']
            if compo:
                newFields['cont_type'] = compo.get_type()
                newFields['cont_id'] = compo.getID()
            newFields['value'] = alarmedObject.get_quantity_string()
            newFields['typealarm'] = unicode(alarmedObject.actualAlarm)
            newFields['degree'] = '2'
            newFields['remark'] = unicode.format(mess,
                                                 config.HardConfig.hostname,
                                                 specmess,
                                                 name,
                                                 elem.getName(lang) if elem else "",
                                                 elem.fields['acronym'] if elem else "",
                                                 alarmedObject.getQtyUnit(config, lang),
                                                 alarmedObject.fields['remark'],
                                                 alarmedObject.fields['time'])
        elif alarmedObject.get_type() == 'v':
            mess = config.getMessage('alarmpouring', lang)
            elemid = ''
            elemin = None
            if alarmedObject.fields['src']:
                elemid = alarmedObject.fields['src']
                elemin = config.AllBatches.get(elemid)
            elemout = None
            if alarmedObject.fields['dest']:
                elemid = alarmedObject.fields['dest']
                elemout = config.AllBatches.get(elemid)
            newFields['begintime'] = alarmedObject.fields['time']
            newFields['cont_type'] = 'b'
            newFields['cont_id'] = elemid
            newFields['value'] = alarmedObject.get_quantity_string()
            # TODO: check quantities and automate alarm launch...
            newFields['typealarm'] = 'typical'
            newFields['degree'] = '2'
            newFields['remark'] = unicode.format(mess,
                                                 config.HardConfig.hostname,
                                                 specmess,
                                                 elemout.getName(lang) if elemout else "",
                                                 elemout.fields['acronym'] if elemout else "",
                                                 elemin.getName(lang) if elemin else "",
                                                 elemin.fields['acronym'] if elemin else "",
                                                 alarmedObject.getQtyUnit(config, lang),
                                                 alarmedObject.fields['remark'],
                                                 alarmedObject.fields['time'])
        if not alid:
            currObject = config.AllAlarmLogs.createObject()
            currObject.fields.update(newFields)
            currObject.save(config)
            return currObject.fields
        else:
            return newFields

    def get_alarm_title(self, alarmedObject, config, lang):
        if alarmedObject.get_type() == 's':
            title = config.getMessage('alarmtitle', lang)
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
            title = config.getMessage('alarmmanualtitle', lang)
            elem = config.get_object(
                alarmedObject.fields['object_type'], alarmedObject.fields['object_id'])
            return unicode.format(title,
                                  alarmedObject.getQtyUnit(config, lang),
                                  elem.getName(lang))
        elif alarmedObject.get_type() == 't':
            title = config.getMessage('alarmmanualtitle', lang)
            elem = config.get_object(
                alarmedObject.fields['object_type'], alarmedObject.fields['object_id'])
            return unicode.format(title,
                                  alarmedObject.getQtyUnit(config, lang),
                                  elem.getName(lang))
        elif alarmedObject.get_type() == 'v':
            title = config.getMessage('alarmpouringtitle', lang)
            elemin = config.AllBatches.elements[alarmedObject.fields['src']]
            elemout = config.AllBatches.elements[alarmedObject.fields['dest']]
            return unicode.format(title, elemout.fields['acronym'], elemout.getName(lang), elemin.fields['acronym'],
                                  elemin.getName(lang))

    def alarm_by_sms(self, alarmedObject, alid, phone_group, config):
        group = config.AllGrFunction.get(phone_group)
        if group:
            userlist = group.get_user_group()
            for user in userlist:
                anUser = config.AllUsers.elements[user]
                if anUser.isActive():
                    lang = anUser.fields['language']
                    allog = self.get_alarm_message(alarmedObject, config, phone_group, lang, alid)
                    if not alid and allog and 'al_id' in allog:
                        alid = allog['al_id']
                    title = self.get_alarm_title(alarmedObject, config, lang)
                    if anUser.fields['donotdisturb'] != '1':
                        if not useful.send_sms(config.HardConfig, anUser.fields['phone'],
                                               title, allog['remark']):  # Fall back to email...
                            useful.send_email(config.HardConfig, anUser.fields['mail'],
                                              title, allog['remark'])
        return alid

    def alarm_by_email(self, alarmedObject, alid, e_mail, config):
        group = config.AllGrFunction.get(e_mail)
        if group:
            userlist = group.get_user_group()
            for user in userlist:
                anUser = config.AllUsers.elements[user]
                if anUser.isActive():
                    lang = anUser.fields['language']
                    allog = self.get_alarm_message(alarmedObject, config, e_mail, lang,  alid)
                    if not alid and allog and 'al_id' in allog:
                        alid = allog['al_id']
                    title = self.get_alarm_title(alarmedObject, config, lang)
                    if anUser.fields['donotdisturb'] != '1':
                        useful.send_email(config.HardConfig, anUser.fields['mail'],
                                          title,
                                          allog['remark'])
        return alid

    def alarm_by_sound(self, alarmedObject, alid, dest, config):
        group = config.AllGrFunction.get(dest)
        if group:
            userlist = group.get_user_group()
            for user in userlist:
                anUser = config.AllUsers.elements[user]
                if anUser.isActive():
                    lang = anUser.fields['language']
                    allog = self.get_alarm_message(alarmedObject, config, dest, lang,  alid)
                    if not alid and allog and 'al_id' in allog:
                        alid = allog['al_id']
        return alid


    def alarm_by_relay(self, alarmedObject, relay_id, relay_value, config):
        relaySensor = config.AllSensors.get(relay_id)
        if relaySensor and relay_value:
            relaySensor.update(useful.date_to_timestamp(alarmedObject.time),relay_value,config)
            relaySensor.relaySetting = relay_value

    def alarm_by_all(self, alarmedObject, sms, mail, sound, relay_id, relay_value, config):
        alid = None
        alid = self.alarm_by_sms(alarmedObject, alid, self.fields[sms], config)
        alid = self.alarm_by_email(alarmedObject, alid, self.fields[mail], config)
        alid = self.alarm_by_sound(alarmedObject, alid, self.fields[sound], config)
        self.alarm_by_relay(alarmedObject, self.fields[relay_id], self.fields[relay_value], config)
        return alid

    def launch_alarm(self, alarmedObject, config):
        alid = None
        if alarmedObject.get_type() == 's':
            level = alarmedObject.degreeAlarm
            if level == 1:
                alid = self.alarm_by_all(alarmedObject, u'o_sms1', u'o_email1', u'o_sound1', u'relay1_id' , u'relay1', config)
            elif level == 2:
                alid = self.alarm_by_all(alarmedObject, u'o_sms2', u'o_email2', u'o_sound2', u'relay2_id' , u'relay2', config)
        elif alarmedObject.get_type() in TRANSACTION_TYPES:
            alid = self.alarm_by_all(alarmedObject, u'o_sms2', u'o_email2', u'o_sound2', u'relay2_id' , u'relay2', config)
        return alid

    def get_user_groups(self, model=None):
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
            step_dec = {'-3': '1000', '-2': '100', '-1': '10', '0': '1', '1': '0.1',
                        '2': '0.01', '3': '0.001', '4': '0.0001', '5': '0.00001',
                        '6': '0.000001'}[step]
        except:
            step_dec = 'any'
        return step_dec

    def integers_count(self):
        step = self.fields['step']
        if not self.fields['min']:
            return 0
        if not self.fields['max']:
            return 0
        if not step or step == '0':  # one by one
            return int(self.fields['max']) - int(self.fields['min']) + 1
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
                    i += step

    def get_select_str(self, lang):
        acr = self.fields['acronym']
        name = self.getName(lang)
        min = self.fields['min']
        max = self.fields['max']
        unit = self.fields['unit']

        return (unicode(acr) + ' - '
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

    def validate_form(self, data, configuration, user):
        tmp = super(Measure, self).validate_form(data, configuration, user)
        if tmp is True:
            tmp = ''
        lang = user.fields['language']
        try:
            if 'formula' in data and len(data['formula']) > 0:
                value = 1
                owData = unicode(eval(data['formula']))
                value = 0
                owData = unicode(eval(data['formula']))
        except:
            tmp += configuration.getMessage('formularules', lang) + '\n'

        try:
            if not len(data['unit']) > 0:
                tmp += configuration.getMessage('unitrules', lang) + '\n'
        except:
            tmp += configuration.getMessage('unitrules', lang) + '\n'

        valueMin = 0.0
        try:
            if not len(data['min']) > 0:
                tmp += configuration.getMessage('minrules', lang) + '\n'
            else:
                valueMin = float(data['min'])
        except:
            tmp += configuration.getMessage('minrules', lang) + '\n'

        try:
            if not len(data['max']) > 0:
                tmp += configuration.getMessage('maxrules', lang) + '\n'
            else:
                valueMax = float(data['max'])
                if valueMax < valueMin:
                    tmp += configuration.getMessage('maxrules', lang) + '\n'
        except:
            tmp += configuration.getMessage('maxrules', lang) + '\n'

        try:
            if not len(data['step']) > 0:
                tmp += configuration.getMessage('steprules', lang) + '\n'
            else:
                value = int(data['step'])
        except ValueError:
            tmp += configuration.getMessage('steprules', lang) + '\n'

        if tmp == '':
            return True
        return tmp

    def set_value_from_data(self, data, c, user):
        super(Measure, self).set_value_from_data(data, c, user)
        tmp = ['unit', 'min', 'max', 'step']
        for elem in tmp:
            self.fields[elem] = data[elem]
        self.save(c, user)

    def get_measure(self, c):
        return self;

    def get_unit(self, c):
        return self.fields['unit']


class Sensor(AlarmingObject):
    def __init__(self):
        self.default_user = None
        self.relaySetting = None
        AlarmingObject.__init__(self)

    def __str__(self):
        string = "\nSensor :"
        for field in self.fields:
            string = string + "\n" + field + \
                     " : " + unicode(self.fields[field])
        string = string + ' Actual Alarm : ' + self.actualAlarm
        string = string + ' Degree Alarm : ' + unicode(self.degreeAlarm)
        return string + "\n"

    def get_type(self):
        return 's'

    def get_class_acronym(self):
        return 'sensor'

    def get_group(self):
        return self.fields['m_id']

    def get_quantity_string(self):
        if self.lastvalue is None:
            return ""
        return unicode(self.lastvalue)

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

    def nextAlarm(self, config, timestamp, no_change):
        alid = None
        if not no_change:  # Alarm just changed !
            self.degreeAlarm = 0
        if self.degreeAlarm == 0:
            self.degreeAlarm = 1
            self.countAlarm = 0
            self.time = useful.timestamp_to_date(timestamp)
            alarmCode = self.get_alarm()
            if int(self.floats('lapse1')) == 0:
                if alarmCode and alarmCode in config.AllAlarms.elements:
                    alid = config.AllAlarms.elements[alarmCode].launch_alarm(self, config)
                self.degreeAlarm = 2
        else:
            self.countAlarm = self.countAlarm + 1
            alarmCode = self.get_alarm()
            if self.degreeAlarm == 1 \
                    and self.fields['lapse1'] and self.countAlarm >= int(self.fields['lapse1']):
                if alarmCode and alarmCode in config.AllAlarms.elements:
                    alid = config.AllAlarms.elements[alarmCode].launch_alarm(self, config)
                self.degreeAlarm = 2
                self.countAlarm = 0
            elif self.degreeAlarm == 2 \
                    and self.fields['lapse2'] and self.countAlarm >= int(self.fields['lapse2']):
                if alarmCode and alarmCode in config.AllAlarms.elements:
                    alid = config.AllAlarms \
                        .elements[alarmCode].launch_alarm(self, config)
                self.degreeAlarm = 3
                self.countAlarm = 0
            elif self.degreeAlarm == 3 \
                    and self.countAlarm >= int(self.fields['lapse3']):
                if alarmCode and alarmCode in config.AllAlarms.elements:
                    alid = config.AllAlarms.elements[alarmCode].launch_alarm(self, config)
                self.degreeAlarm = 4  # Do nothing after this!
        if alid:
            print 'Alarm #' + alid + ' [' + self.actualAlarm + '] level ' + unicode(
                    self.degreeAlarm) + ' for ' + self.__repr__()

    def update(self, timestamp, value, config):
        self.lastvalue = value
        if value is not None:
            self.updateRRD(timestamp, value)

        if config.screen is not None:
            minutes = int(timestamp / 60)
            # GMT + DST
            hours = (int(minutes / 60) % 24) + 100 + 2
            minutes = (minutes % 60) + 100
            strnow = unicode(hours)[1:3] + ":" + unicode(minutes)[1:3]
            pos = config.screen.show(config.screen.begScreen, strnow)
            pos = config.screen.showBW(pos + 2, self.get_acronym())
            pos = (config.screen
                   .show(pos + 2,
                         unicode(round(float(value), 1))))
            unit_measure = self.get_unit(config)
            if unit_measure:
                pos = config.screen.show(pos, unit_measure)

        prvAlarm = self.actualAlarm
        typeAlarm, symbAlarm, self.colorAlarm, self.colorTextAlarm = self.getTypeAlarm(value, self)
        self.actualAlarm = typeAlarm
        self.nextAlarm(config, timestamp, prvAlarm == self.actualAlarm)

    def updateRRD(self, now, value):
        value = float(value)
        rrdtool.update(str(DIR_RRD + self.getRRDName()), '%d:%f' % (now, value))
        print self.getRRDName() + " " + useful.timestamp_to_ISO(now) + " " + '%d:%f' % (now, value)

    def fetchRRD(self, period=None):
        filename = str(DIR_RRD + self.getRRDName())

        start = "end-1month"
        if period:
            if period == "300":
                start = "end-360sdays"
            elif period == "1800":
                start = "end-5years"
            result = rrdtool.fetch(filename, 'AVERAGE', "-s", start, "-r", str(period))
        else:
            result = rrdtool.fetch(filename, 'LAST', "-s", start)
        start, end, step = result[0]
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
        now = str(int(time.time()) - 60)
        if self.fields['channel'] != 'radio':
            data_sources = str('DS:' + name + ':GAUGE:120:U:U')
            rrdtool.create(str(DIR_RRD + self.getRRDName()),
                           "--step", "60",
                           '--start', now,
                           data_sources,
                           'RRA:LAST:0.5:1:43200',
                           'RRA:AVERAGE:0.5:5:103680',
                           'RRA:AVERAGE:0.5:30:86400')
        elif self.fields['channel'] == 'radio':
            data_sources = str('DS:' + name + ':GAUGE:360:U:U')
            rrdtool.create(str(DIR_RRD + self.getRRDName()),
                           "--step", "180",
                           '--start', now,
                           data_sources,
                           'RRA:LAST:0.5:1:14400',
                           'RRA:AVERAGE:0.5:5:34560',
                           'RRA:AVERAGE:0.5:30:28800')

    def get_mesure_humidity_campbell(self, config):
        input = config.HardConfig.inputs[self.fields['channel']]
        input_device = config.HardConfig.devices[input['device']]
        output = config.HardConfig.outputs[input['poweroutput']]
        output_device = config.HardConfig.devices[output['device']]
        try:
            output_gpio = abe_iopi.IOPi(int(output_device['i2c'], 16))
            output_gpio.set_pin_direction(int(output['channel']), 0)
        except IOError:
            print('Unable to control output_device!' + ' channel : '
                  + self.fields['channel']
                  + ', i2c address : '
                  + output_device['i2c'])
            return None
        try:
            adc = abe_adcpi.ADCPi(int(input_device['i2c'], 16),
                                  int(input_device['i2c'], 16) + 1,
                                  int(input['resolution']))
        except IOError:
            print('Unable to read sensor !' + ' channel : '
                  + self.fields['channel']
                  + ', i2c address : '
                  + input_device['i2c'])
            return None
        # TODO: manage invertion for output
        # Stimulate
        output_gpio.write_pin(int(output['channel']), 1)
        time.sleep(int(input['delayms']) * 0.001)

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

    def get_value_sensor(self, config, timestamp, cache=None):
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
            if config.owproxy:
                try:
                    sensorAdress = u'/' + \
                                   unicode(self.fields['sensor']) + u'/' + \
                                   unicode(self.fields['subsensor'])
                    output_val = float(config.owproxy.read(sensorAdress))
                    config.set_channel_access('wire', self.fields['sensor'][:14], 0, timestamp)
                except:
                    debugging = (u"Device=" + sensorAdress
                                 + u", Message="
                                 + traceback.format_exc())
        elif self.fields['channel'] == 'radio':
            # Look at RadioThread
            pass
        elif self.fields['channel'] == 'lora':
            # Look at WebApiKeyValue
            pass
        elif self.fields['channel'] == 'cputemp':
            try:
                with open('/sys/class/thermal/thermal_zone0/temp', 'r') \
                        as sensorfile:
                    info = sensorfile.read()
                    output_val = float(info) / 1000.0
            except:
                 debugging = (u"File=/sys/class/thermal/thermal_zone0/temp"
                                 + u", Message="
                                 + traceback.format_exc())
                 traceback.print_exc()
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
                try:  # urlopen not usable with "with"
                    sensorfile = urllib2.urlopen(self.fields['sensor'], None, 20)
                    info = sensorfile.read(80000)
                    cache = info
                    output_val = eval(self.fields['subsensor'])
                    config.set_channel_access('http', self.fields['sensor'], 0, timestamp)
                except:
                    debugging = u"URL=" + (url if url else "") + u", code=" + \
                                (unicode(code) if code else "") + u", Response=" + (info if info else "") + \
                                u", Message=" + traceback.format_exc()
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
                try:  # urlopen not compatible with "with"
                    sensorfile = urllib2.urlopen(self.fields['sensor'], None, 20)
                    # print sensorfile.getcode()
                    info = sensorfile.read()
                    info = json.loads(info)
                    cache = info
                    output_val = eval(self.fields['subsensor'])
                    config.set_channel_access('json', self.fields['sensor'], 0, timestamp)
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
                info = ""
                sensorAdress = self.fields['sensor']
                with open(sensorAdress, 'r') as sensorfile:
                    info = sensorfile.read()
                    output_val = eval(self.fields['subsensor'])
            except:
                debugging = u"Device=" + sensorAdress + u", field=" + \
                            self.fields['subsensor'] + u", data=" + \
                            unicode(info) + u", Message=" + traceback.format_exc()
        elif self.fields['channel'] == 'battery':
            if 'battery' in config.HardConfig.inputs:
                input = config.HardConfig.inputs['battery']
                device = config.HardConfig.devices[input['device']]
                if device['install'] == "mcp3423":
                    try:
                        adc = abe_mcp3423.ADCPi(int(device['i2c'], 16),
                                                int(input['resolution']))
                        output_val = adc.read_voltage(int(input['channel']))
                    except IOError:
                        debugging = ('Unable to read sensor !' + ' channel : '
                                      + self.fields['channel']
                                      + ', i2c address : '
                                      + device['i2c'])
                elif device['install'] == "abe_expanderpi":
                    adc = abe_expanderpi.ADC()
                    output_val = adc.read_adc_voltage(int(input['channel']), 0)
                    adc.close()
                else:
                    debugging = ("Error : device.install : "
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
                debugging = ('Unable to read sensor !' + ' channel : '
                              + self.fields['channel']
                              + ', i2c address : '
                              + device['i2c'])
        elif self.fields['channel'].startswith('humiditysensor'):
            output_val = self.get_mesure_humidity_campbell(config)
        elif self.fields['channel'] == 'atmos41':
            input = config.HardConfig.inputs[self.fields['channel']]
            if cache is [] or cache is None:
                try:
                    ser = serial.Serial(input['serialport'],
                                        baudrate=9600,
                                        timeout=10)
                    time.sleep(2.5)  # Leave some time to initialize
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
            if self.fields['channel'] not in  ['radio','lora']:
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
                print(u"Device=" + self.fields['sensor'] + u" / " + self.fields['subsensor'] + \
                      u", Formula=" + self.fields['formula'] + \
                      u", Message=" + traceback.format_exc())
            return self.sanitize_reading(config, output_val), cache
        return None, None

    def count_logs(self, c):
        count = 0
        sID = self.getID()
        for kal, e in c.AllAlarmLogs.elements.items():
            if (sID == e.fields['s_id']) and ((e.fields['s_type'] == 's') or (e.fields['s_type'] == '')):
                count += 1
        return count

    def isAlarmed(self, c):
        return self.actualAlarm != 'typical'

    def is_in_component(self, type, id):
        if type in COMPONENT_TYPES + ['m']:
            return id == self.fields[type + '_id']
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

    def resolution(self):
        if self.fields['channel'] == 'radio':
            return 180
        else:
            return 60

    def fetch(self, start, end=None):
        """Fetch data from the RRD.

        start -- integer start time in seconds since the epoch, or negative for
                 relative to end
        end -- integer end time in seconds since the epoch, or None for current
               time"""
        if end is None:
            end = int(time.time())
        if start < 0:
            start += end
        if end - start > 0:
            try:
                time_span, _, values = rrdtool.fetch(str(DIR_RRD + self.getRRDName()),
                                                     'AVERAGE', '-a', '-s', str(int(start)),
                                                     '-e', str(int(end)))
                ts_start, ts_end, ts_res = time_span
                times = range(ts_start, ts_end, ts_res)
                return zip(times, values)
            except:
                print self.getRRDName()
                traceback.print_exc()
                return None
        return None

    def validate_form(self, data, configuration, user):
        tmp = super(Sensor, self).validate_form(data, configuration, user)
        if tmp is True:
            tmp = ''
        lang = user.fields['language']
        try:
            if 'formula' in data and len(data['formula']) > 0:
                value = 1
                owData = unicode(eval(data['formula']))
                value = 0
                owData = unicode(eval(data['formula']))
        except:
            tmp += configuration.getMessage('formularules', lang) + '\n'

        try:
            if not len(data['component']) > 0:
                tmp += configuration.getMessage('componentrules', lang) + '\n'
        except:
            tmp += configuration.getMessage('componentrules', lang) + '\n'
        try:
            if not len(data['measure']) > 0:
                tmp += configuration.getMessage('measurerules', lang) + '\n'
        except:
            tmp += configuration.getMessage('measurerules', lang) + '\n'
        try:
            if not len(data['channel']) > 0:
                tmp += configuration.getMessage('channelrules', lang) + '\n'
        except:
            tmp += configuration.getMessage('channelrules', lang) + '\n'
        try:
            if not len(data['sensor']) > 0:
                tmp += configuration.getMessage('sensorrules', lang) + '\n'
        except:
            tmp += configuration.getMessage('sensorrules', lang) + '\n'

        if tmp == '':
            return True
        return tmp

    def set_value_from_data(self, data, c, user):
        super(Sensor, self).set_value_from_data(data, c, user)
        tmp = ['channel', 'sensor', 'subsensor', 'formula', 'lapse1', 'lapse2', 'lapse3'] + alarmFields
        for elem in tmp:
            self.fields[elem] = data[elem]
        self.add_component(data['component'])
        self.add_measure(data['measure'])

        # self.createRRD()
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

    def getAll(self):
        return self.config.AllBatches

    def get_name_listing(self):
        return 'batches'

    def get_class_acronym(self):
        return 'batch'

    def isExpired(self):
        return self.fields['expirationdate'] and (self.fields['expirationdate'] < (useful.now()[:10]))

    def add_measure(self, data):
        tmp = data.split('_')
        self.fields['m_id'] = tmp[-1]

    def inherited(self, fname):
        kgroup = self.get_group()
        parent = self.config.AllGrRecipe.get(kgroup)
        if parent:
            value = parent.field(fname)
            return value
        return ""

    def field(self, fname):
        if self.fields[fname]:
            return self.fields[fname]
        else:
            return self.inherited(fname)

    def get_total_cost(self):
        return useful.str_float(self.field('fixed_cost')) + (
                    useful.str_float(self.field('cost')) * useful.str_float(self.field('basicqt')))

    def get_quantity_string(self):
        return self.field('basicqt')

    def get_quantity_used(self):
        qt = 0
        for e in self.source:
            qt += self.config.AllPourings.elements[e].floats('quantity')
        return qt

    def get_quantity_added(self, config):
        qt = 0
        for e in self.destination:
            aPouring = self.config.AllPourings.elements[e]
            if aPouring.get_unit(config) == self.get_unit(config):
                qt += self.config.AllPourings.elements[e].floats('quantity')
        return qt

    def get_lifetime(self):
        if useful.str_float(self.get_quantity_string('basicqt')) != 0.0:
            qt = self.get_quantity_used() - self.get_quantity_added(self.config)
            tmp = self.get_quantity() - qt
            if tmp < 0:
                return self.pourings.getTimestamp() - self.getTimestamp()
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

    def get_pourings(self, c):
        events = []
        if self.source:
            for kevent in self.source:
                if kevent in c.AllPourings.elements:
                    events.append(c.AllPourings.elements[kevent])
        if self.destination:
            for kevent in self.destination:
                if kevent in c.AllPourings.elements:
                    events.append(c.AllPourings.elements[kevent])
        return sorted(events, key=lambda t: t.fields['time'])

    def add_checkpoint(self, cp, now):
        if cp not in self.checkpoints and cp in self.config.AllCheckPoints.elements:
            self.checkpoints.append(cp)
            self.lastCheckPoint = now
            aCP = self.config.AllCheckPoints.elements[cp]
            if self.id not in aCP.batches:
                aCP.batches.append(self.id)

    def fromModel(self, c, model):
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
        val = self.get_quantity_used() - self.get_quantity_added(self.config)
        # if self.floats('basicqt') == 0.0:
        #    self.fields['basicqt'] = "0"
        return self.get_quantity() - val

    def clone(self, user, name=1):
        b = self.config.getObject('new', 'b')
        allObjects = self.config.findAllFromObject(self)
        posSuffix = self.fields['acronym'].rfind('_') + 1
        lenAcro = len(self.fields['acronym'])
        prefix = self.fields['acronym'][0:posSuffix]
        tmpname = allObjects.findNextAcronym(prefix, lenAcro, name)
        if not tmpname:
            return False
        b.fields['acronym'] = tmpname
        allObjects.hierarchy = None
        for f in ['active', 'basicqt', 'm_id', 'time', 'cost', 'fixed_cost', 'remark',
                  "provider_id", "provider_ref", "buyer_id", "buyer_ref", 'gr_id']:
            if f in self.fields:
                b.fields[f] = self.fields[f]
        for lang in self.config.AllLanguages.elements:
            b.setName(lang, self.get_real_name(lang),
                      user, self.config.getKeyColumn(b))
        b.creator = user.fields['u_id']
        b.created = b.fields['begin']
        b.save(self.config, user)
        b.ensure_barcode(self.config, user, "")
        return True

    def subbatch(self, user, name, checkpoint, component):
        b = self.config.getObject('new', 'b')
        allObjects = self.config.findAllFromObject(self)
        lenAcro = len(self.fields['acronym']) + 3
        prefix = self.fields['acronym'] + '_'
        tmpname = allObjects.findNextAcronym(prefix, lenAcro, name)
        if not tmpname:
            return None
        b.fields['acronym'] = tmpname
        allObjects.hierarchy = None
        b.fields['basicqt'] = '0'
        for f in ['active', 'm_id', 'time', 'cost', 'fixed_cost', 'remark', 'expirationdate',
                  "provider_id", "provider_ref", "buyer_id", "buyer_ref", 'gr_id']:
            if f in self.fields:
                b.fields[f] = self.fields[f]
        for lang in self.config.AllLanguages.elements:
            b.setName(lang, self.get_real_name(lang),
                      user, self.config.getKeyColumn(b))
        b.creator = user.fields['u_id']
        b.created = b.fields['begin']
        b.save(self.config, user)
        b.ensure_barcode(self.config,user,"")
        if component:
            # CREATE TRANSFER OF B TO GU !!
            tr = self.config.getObject('new', 't')
            tr.fields['time'] = b.fields['begin']
            if not tr.fields['time']:
                tr.fields['time'] = useful.now()
            tr.fields['remark'] = ''
            tr.fields['active'] = '1'
            tr.fields['h_id'] = checkpoint
            tr.set_position(component)
            tr.set_object(b.getTypeId(), user)
            tr.creator = user.fields['u_id']
            tr.created = tr.fields['time']
            tr.save(self.config, user)
        return b

    def validate_form(self, data, configuration, user):
        tmp = super(Batch, self).validate_form(data, configuration, user)
        if tmp is True:
            tmp = ''
        lang = user.fields['language']
        try:
            value = useful.date_to_ISO(data['time'])
        except:
            traceback.print_exc()
            tmp += configuration.getMessage('timerules', lang) + '\n'

        ##        if 'completedtime' in data and data['completedtime']:
        ##            try:
        ##                value = useful.date_to_ISO(data['completedtime'])
        ##            except:
        ##                traceback.print_exc()
        ##                tmp += configuration.getMessage('timerules',lang) + '\n'

        try:
            value = float(data['cost'])
            if value < 0.0:
                tmp += configuration.getMessage('costrules', lang) + '\n'
        except:
            tmp += configuration.getMessage('costrules', lang) + '\n'

        try:
            value = float(data['fixed_cost'])
            if value < 0.0:
                tmp += configuration.getMessage('costrules', lang) + '\n'
        except:
            tmp += configuration.getMessage('costrules', lang) + '\n'

        try:
            value = float(data['basicqt'])
            if value < 0.0:
                tmp += configuration.getMessage('quantityrules', lang) + '\n'
        except:
            tmp += configuration.getMessage('quantityrules', lang) + '\n'

        if data['measure'] == '':
            tmp += configuration.getMessage('measurerules', lang) + '\n'

        if tmp == '':
            return True
        return tmp

    def lifespan(self):
        krecipe = self.get_group()
        aRecipe = self.config.AllGrRecipe.get(krecipe)
        if aRecipe:
            return aRecipe.lifespan()
        return 0

    def set_value_from_data(self, data, c, user):
        super(Batch, self).set_value_from_data(data, c, user)
        tmp = ['basicqt', 'time', 'cost', 'fixed_cost', "provider_id", "provider_ref", "buyer_id", "buyer_ref"]
        for f in tmp:
            if f in data:
                self.fields[f] = data[f]
        if not self.fields['time']:
            self.fields['time'] = useful.now()

        completed = None
        if 'completedtime' in data and data['completedtime']:
            try:
                completed = useful.date_to_ISO(data['completedtime'])
            except:
                completed = useful.now()
        if 'iscompleted' in data and data['iscompleted']:
            if completed:
                self.fields['completedtime'] = completed
            else:
                self.fields['completedtime'] = useful.now()
        else:
            self.fields['completedtime'] = ""

        expdate = ""
        if 'expirationdate' in data and data['expirationdate']:
            try:
                expdate = useful.date_to_ISO(data['expirationdate'])[:10]
            except:
                if self.fields['time']:
                    expdate = (useful.string_to_date(self.fields['time']) + datetime.timedelta(
                        days=self.lifespan())).isoformat()[:10]
        self.fields['expirationdate'] = expdate

        self.add_measure(data['measure'])
        self.fields['gr_id'] = data['group']
        self.save(c, user)

    def count_logs(self, c):
        count = 0
        bID = self.getID()
        for kal, e in c.AllAlarmLogs.elements.items():
            if (bID == e.fields['cont_id']) and (e.fields['cont_type'] == 'b'):
                count += 1
        return count

    def get_group(self):
        return self.fields['gr_id']

    def isPinned(self,connected):
        return self == connected.pin

    def get_allowed_checkpoints(self, c):
        recipes = set()
        recipe_id = self.fields['gr_id']
        recipe = c.AllGrRecipe.get(recipe_id)
        if recipe:
            recipes.add(recipe_id)
            new_recipes = recipe.get_all_parents([], c.AllGrRecipe)
            recipes.update(new_recipes)
        allowedcheckpoints = None
        usages = set()
        usage = None
        components = self.get_actual_position_hierarchy(c, [])
        if len(components) > 0:
            for place in components:
                if place.get_type() in COMPONENT_TYPES:
                    gr_usage = place.get_group()
                    usage = c.AllGrUsage.get(gr_usage)
                    if usage:
                        usages.add(gr_usage)
                        new_usages = usage.get_all_parents([], c.AllGrUsage)
                        usages.update(new_usages)
            allowedcheckpoints = c.AllCheckPoints.get_checkpoints_for_recipe_usage(recipes, usages)
        return allowedcheckpoints, recipes, usages


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

    def getAll(self):
        return self.config.AllPouringModels

    def isModeling(self):
        return "v"

    def get_class_acronym(self):
        return 'pouringmodel'

    def get_group(self):
        return self.fields['h_id']

    def get_quantity_string(self):
        return self.fields['typical']

    def get_unit_in_context(self, c, currObject):
        if self.fields['src']:
            if self.fields['src'] in c.AllGrRecipe.elements:
                aRecipe = c.AllGrRecipe.elements[self.fields['src']]
                return aRecipe.get_unit(c)
        elif currObject:
            return currObject.get_unit(c)
        return ""

    def validate_form(self, data, configuration, user):
        return super(PouringModel, self).validate_form(data, configuration, user)

    def set_value_from_data(self, data, c, user):
        if self.fields['h_id'] != '':
            self.config.AllCheckPoints.elements[self.fields['h_id']].remove_vm(self)
        super(PouringModel, self).set_value_from_data(data, c, user)
        tmp = ['in', 'rank', 'gu_id'] + alarmFields
        for elem in tmp:
            self.fields[elem] = data[elem]

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

    def getAll(self):
        return self.config.AllManualDataModels

    def isModeling(self):
        return "d"

    def get_class_acronym(self):
        return 'manualdatamodel'

    def get_group(self):
        return self.fields['h_id']

    def get_quantity_string(self):
        return self.fields['typical']

    def validate_form(self, data, configuration, user):
        return super(ManualDataModel, self).validate_form(data, configuration, user)

    def set_value_from_data(self, data, c, user):
        if self.fields['h_id'] != '':
            self.config.AllCheckPoints.elements[self.fields['h_id']].remove_dm(
                self)
        super(ManualDataModel, self).set_value_from_data(data, c, user)
        tmp = ['rank'] + alarmFields
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

    def getAll(self):
        return self.config.AllTransferModels

    def isModeling(self):
        return "t"

    def get_class_acronym(self):
        return 'transfermodel'

    def get_quantity(self):
        result = self.get_quantity_string()
        if result:
            return float(result)
        return -1.0

    def get_quantity_string(self):
        if self.fields['typical']:
            return self.fields['typical']
        if self.fields['min']:
            return self.fields['min']
        if self.fields['max']:
            return self.fields['max']
        if self.fields['minmin']:
            return self.fields['minmin']
        if self.fields['maxmax']:
            return self.fields['maxmax']
        return ""

    def getQtyUnit(self, c, lang="EN"):
        delay = self.get_quantity()
        if delay >= 0:
            return c.seconds_to_string(delay, lang)
        return ""

    def validate_form(self, data, configuration, user):
        return super(TransferModel, self).validate_form(data, configuration, user)

    def set_value_from_data(self, data, c, user):
        if self.fields['h_id'] != '':
            self.config.AllCheckPoints.elements[self.fields['h_id']].remove_tm(
                self)
        super(TransferModel, self).set_value_from_data(data, c, user)
        for elem in alarmFields:
            self.fields[elem] = data[elem]

        self.fields['gu_id'] = data['position']
        self.fields['h_id'] = data['checkpoint']
        self.fields['rank'] = data['rank']
        if 'active' in data:
            self.config.AllCheckPoints.elements[self.fields['h_id']].add_tm(
                self)
        self.save(c, user)

    def get_group(self):
        return self.fields['h_id']


class Transfer(AlarmingObject):
    def __init__(self, config):
        AlarmingObject.__init__(self)
        self.config = config
        self.completed = None

    def __str__(self):
        string = "\nBatchTransfer :"
        for field in self.fields:
            string = string + "\n" + field + " : " + self.fields[field]
        return string + "\n"

    def get_type(self):
        return 't'

    def getAll(self):
        return self.config.AllTransfers

    def sort_key(self):
        return self.fields['time']

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

    def getQtyUnit(self, c, lang="EN"):
        delay = self.get_quantity()
        if delay >= 0:
            return c.seconds_to_string(delay, lang)
        return ""

    def get_quantity_string(self):
        if self.completed:
            return unicode(int(
                (useful.string_to_date(self.completed) - useful.string_to_date(self.getTimestring())).total_seconds()))
        return unicode(
            int((useful.string_to_date(useful.now()) - useful.string_to_date(self.getTimestring())).total_seconds()))

    def get_planned_duration(self, c):
        if self.completed:
            return int(
                (useful.string_to_date(self.completed) - useful.string_to_date(self.getTimestring())).total_seconds())
        tm = self.get_model(c)
        if tm:
            seconds = tm.get_quantity_string()
            if seconds:
                return int(seconds)
        return -1

    def get_unit(self, c):
        return "mn"

    def set_position(self, pos):
        self.fields['cont_type'], self.fields['cont_id'] = splitId(pos)

    def set_object(self, objkey, user):
        if 'object_type' in self.fields:
            obj = self.config.get_object(self.fields['object_type'], self.fields['object_id'])
            if obj:
                obj.remove_position(self)
        type, id = splitId(objkey)
        self.fields['object_type'] = type
        self.fields['object_id'] = id
        obj = self.config.get_object(type, id)
        if obj:
            obj.add_position(self, user)

    def checkTimerAlarm(self, config, MaxOnly):
        model = self.get_model(config)
        if model:
            elapsed = self.get_quantity_string()
            typeAlarm, symbAlarm, self.colorAlarm, self.colorTextAlarm = self.getTypeAlarm(elapsed, model)
            if typeAlarm and typeAlarm != self.actualAlarm:
                if MaxOnly and not 'max' in typeAlarm:
                    return False
                self.actualAlarm = typeAlarm
                alarmCode = self.get_alarm(model);
                anAlarm = config.AllAlarms.get(alarmCode)
                if anAlarm:
                    newAlarm = True
                    if self.fields['al_id']:
                        aLog = config.AllAlarmLogs.get(self.fields['al_id'])
                        if aLog:
                            if typeAlarm == aLog.fields['typealarm']:
                                newAlarm = False
                    if newAlarm:
                        alid = anAlarm.launch_alarm(self, config)
                        if alid:
                            self.fields['al_id'] = alid
                            return True
        return False

    def validate_form(self, data, configuration, user):
        tmp = ''
        lang = user.fields['language']
        if 'position' in data:
            objtype, objid = splitId(data['object'])
            postype, posid = splitId(data['position'])
            objet = configuration.get_object(objtype, objid)
            # Transfer can be in the past: validating position is very difficult...
            # And timed transfers may not change current position!
            ##            if objet.is_actual_position(postype, posid, configuration):
            ##                transfer = objet.get_last_transfer(configuration)
            ##                if transfer and (transfer.getID() != self.id):
            ##                    tmp += configuration.getMessage('transferrules',lang) + '\n'
            if (objtype == 'e' and postype != 'p') or (objtype == 'c' and postype not in ['e', 'p']):
                tmp += configuration.getMessage('transferhierarchy', lang) + '\n'
        else:
            tmp += configuration.getMessage('transferrules', lang) + '\n'
        if tmp == '':
            return True
        return tmp

    def set_value_from_data(self, data, c, user):
        if self.fields['object_type'] != '' and self.fields['object_id'] != '':
            self.get_source(c).remove_position(self)
        tmp = ['time', 'remark']
        for elem in tmp:
            self.fields[elem] = data[elem]
        if not self.fields['time']:
            self.fields['time'] = useful.now()
        if 'active' in data:
            self.fields['active'] = '1'
        else:
            self.fields['active'] = '0'
        if 'h_id' in data:
            self.fields['h_id'] = data['h_id']
        else:
            self.fields['h_id'] = ''
        if ('origin' in data) and data['origin']:
            self.fields['tm_id'] = data['origin']
        self.set_position(data['position'])
        self.set_object(data['object'], user)
        self.save(c, user)
        if 'expirationdate' in data and data['expirationdate'] and self.get_type_container() == 'b':
            kbatch = self.get_id_container;
            if kbatch and kbatch in c.AllBatches.elements:
                batch = c.AllBatches.elements[kbatch]
                if not batch.fields['expirationdate']:
                    lifedays = batch.lifespan()
                    if lifedays:
                        batch.fields['expirationdate'] = (useful.string_to_date(
                            self.fields['time']) + datetime.timedelta(days=lifedays)).isoformat()[:10]
                        batch.save(c, user)

    def isComplete(self):
        if self.completed:
            return True
        return False

    # WHAT is moved
    def get_source(self, config):
        if not self.fields['object_id']:
            return None
        if self.fields['object_type']:
            allObjs = config.findAll(self.fields['object_type'])
        else:
            allObjs = config.AllBatches
        return allObjs.get(self.fields['object_id'])

    # WHERE it is moved
    def get_component(self, config):
        return config.get_object(self.fields['cont_type'], self.fields['cont_id'])

    def get_model(self, config):
        return config.AllTransferModels.get(self.fields['tm_id'])

    def get_class_acronym(self):
        return 'transfer'


class Barcode(ConfigurationObject):
    def __init__(self, item):
        ConfigurationObject.__init__(self)
        self.element = item

    def __repr__(self):
        return self.fields['code']+((' '+self.fields['codetype']) if self.fields['codetype'] else "")

    def __str__(self):
        string = "\nCode(barre) :"
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
