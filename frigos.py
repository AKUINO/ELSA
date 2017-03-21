#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import io
import codecs
import sys
import resource
import subprocess
import threading
import traceback
import syslog
import serial
##from fysom import Fysom

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import datetime
import time
#import RPi.GPIO as GPIO
import pigpio
#from wiringpi2 import GPIO
import os
import functools
import pyudev
import ConfigParser
import gammu
##import ow
import smbus

from select import select
from evdev import InputDevice, categorize, ecodes

# Code source dans le meme repertoire
import SSD1306
from keypadClass4 import keypad

# Ensure UTF-8 for the output terminal
UTF8Writer = codecs.getwriter('utf8')
sys.stdout = UTF8Writer(sys.stdout)

# Allow graceful stop of the processes
ALIVE = True

# Raspberry Pi pin configuration:
RST = 5
#GPIO.setmode(GPIO.BCM)
#GPIO.setup(5, GPIO.OUT)
#GPIO.output(5, GPIO.LOW)
#time.sleep(0.05)
#GPIO.output(5, GPIO.HIGH)
#time.sleep(0.05)

PIG = pigpio.pi()
# 128x64 display with hardware I2C:
disp = SSD1306.SSD1305_132_64(rst=RST,gpio=PIG)

# Initialize library.
disp.begin()

# Clear display.
disp.clear()

# Create blank image for drawing.
# Make sure to create image with mode '1' for 1-bit color.
width = disp.width
height = disp.height
image = Image.new(u'1', (width, height))
refreshDisplay = True

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# Default font = better than 
#font = ImageFont.load_default()

# Alternatively load a TTF font.  Make sure the .ttf font file is in the same directory as the python script!
# Some other nice fonts to try: http://www.dafont.com/bitmap.php
font = ImageFont.truetype('sans.ttf', 9)
fontG8 = ImageFont.truetype('glyphicons-halflings-regular.ttf', 8)
fontG10 = ImageFont.truetype('glyphicons-halflings-regular.ttf', 10)
degree = u'\N{DEGREE SIGN}'

temperature = 0.0
owtemperature = ''

ELAdirectory = '/run/akuino/ELA'
ELAtty = '/dev/ttyAMA0'
CONFdirectory = '~/akuino'

sensors = {}
badging = {}

idDefinitions = []

# The Sub-States are in line with their access keys (events):  
aAlarm      = 1
aAlarmTrig  = 2
aAlarmResol = 3
aPlace      = 4
aMeasure    = 5
aPerson     = 6
aBatch      = 7

typeNames = [ u"?",u"Alerte",u"?",u"?",u"Lieu",u"Mesure",u"Personne",u"Lot" ]
telOwner = u"0032475776211"


#sm = gammu.StateMachine()
#sm.ReadConfig()
#sm.Init()

def alertOwner(HEX):
        global sensors
        global idDefinitions
        global typeNames
        global telOwner
        transac = sensors[HEX]
        if idDefinitions.has_key(HEX):
                defins = idDefinitions[HEX]
                message = typeNames[defins['typed']]+u" "+defins['name']+u"="+str(transac['data'])
                if transac['alarm'] == None:
                        message = message + u" OK"
                else:
                        message = message + u" enfreint "+transac['alarm']+u"="+str(defins[transac['alarm']])
                for nBadge,aBadge in badging.iteritems():
                        if aBadge['incoming']:
                                message = message + u", "
                                if idDefinitions.has_key(nBadge):
                                        defins = idDefinitions[nBadge]
                                        message = message + typeNames[defins['typed']]+u" "+defins['name']
                                else:
                                        message = message + str(nBadge)
                print message
                #gammuMessage = { 'Text':message, 'SMSC':{'Location':1}, 'Number':telOwner }
                result = subprocess.check_output(['gammu-smsd-inject','TEXT',telOwner,'-len',str(len(message)),'-unicode','-text',message], stdin=None, stderr=None, shell=False, universal_newlines=True) 
                print result
                #sm.SendSMS(gammuMessage)

def readDef(thing, attrib, defVal):
        if idDefinitions.has_key(thing):
                if idDefinitions[thing].has_key(attrib):
                        return idDefinitions[thing][attrib]
                else:
                        return defVal
        else:
                return defVal

def storeSensor(hex,temperature):
        global sensors
        HEX = hex.lower()
        owtemperature = float(temperature)
        prevAlarm = None
        if sensors.has_key(HEX):
                prevAlarm = sensors[HEX]['alarm']
        sensors[HEX] = {}
        sensors[HEX]['data'] = round(owtemperature,1)
        sensors[HEX]['alarm'] = None
        if owtemperature < readDef(HEX,'min',-999.99):
                sensors[HEX]['alarm'] = 'min'
        if owtemperature > readDef(HEX,'max',999.99):
                sensors[HEX]['alarm'] = 'max'
        sensors[HEX]['timestamp'] = datetime.datetime.now()
        #print(HEX,sensors[HEX])
        if not prevAlarm == sensors[HEX]['alarm']:
                alertOwner(HEX)
 
def elaRead():
        global temperature
        global ALIVE
        try:
                elaSerial = serial.Serial(ELAtty,9600,timeout=0.01)
                time.sleep(0.05)
                #reset to manufacturer settings
                elaSerial.write('[9C5E01]')
                line = None
                while ALIVE:
                        try:
                                data = elaSerial.read()
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
                                                        with open(ELAdirectory+'/'+str(ADDRESS)+'.dat','w') as aFile:
                                                                aFile.write(str(temperature))
                                                        storeSensor(HEX,temperature)
                                                line = ''.join(line)
                                                print(line)
                                                #syslog.syslog(syslog.LOG_ERR, line)
                                                line = None
                                        else:
                                                line.append(data)
                        except:
                                traceback.print_exc()   
                elaSerial.close()
                print(ELAtty+u" libre")
        except:
                traceback.print_exc()
                ALIVE = False
        return

if not os.path.exists(ELAdirectory):
    os.makedirs(ELAdirectory)

threadELA = threading.Thread(target=elaRead)
threadELA.start()

def owRead():
        global owtemperature
        global ALIVE
        ow.init("/dev/i2c-1") # recherche sur l'i2c tous les 1-wire connectés
        owDevices = ow.Sensor("/")
        try:
                '''owList = subprocess.check_output(['owdir','/'], stdin=None, stderr=None, shell=False, universal_newlines=True) 
                owList = owList.split('\n')
                valid = re.compile(r"^/[0-9A-F]{2}\.")
                for line in owList:
                        if valid.match(line):
                                owDevices.append(line)'''
                while ALIVE:
                        time.sleep(15)
                        for aDevice in owDevices.sensorList():
                           try:
                                #owtemperature = subprocess.check_output(['owget',aDevice+'/temperature'], stdin=None, stderr=None, shell=False, universal_newlines=False).strip()
                                owtemperature = aDevice.temperature
                                owaddress = aDevice.address
                                print(owaddress+u"="+owtemperature+u" deg.C")
                                #syslog.syslog(syslog.LOG_ERR, owtemperature)
                                HEX = str(owaddress)
                                HEX = HEX[5:8]
                                #print HEX
                                storeSensor(HEX,owtemperature)
                           except:
                                traceback.print_exc()
        except:
                traceback.print_exc()
                ALIVE = False
        return

threadOW = threading.Thread(target=owRead)
threadOW.start()

scancodes = {
    # Scancode: ASCIICode
    0: None, 1: u'ESC', 2: u'1', 3: u'2', 4: u'3', 5: u'4', 6: u'5', 7: u'6', 8: u'7', 9: u'8',
    10: u'9', 11: u'0', 12: u'-', 13: u'=', 14: u'BKSP', 15: u'TAB', 16: u'q', 17: u'w', 18: u'e', 19: u'r',
    20: u't', 21: u'y', 22: u'u', 23: u'i', 24: u'o', 25: u'p', 26: u'[', 27: u']', 28: u'CRLF', 29: u'LCTRL',
    30: u'a', 31: u's', 32: u'd', 33: u'f', 34: u'g', 35: u'h', 36: u'j', 37: u'k', 38: u'l', 39: u';',
    40: u'"', 41: u'`', 42: u'LSHFT', 43: u'\\', 44: u'z', 45: u'x', 46: u'c', 47: u'v', 48: u'b', 49: u'n',
    50: u'm', 51: u',', 52: u'.', 53: u'/', 54: u'RSHFT', 56: u'LALT', 100: u'RALT'
}

capscodes = {
    0: None, 1: u'ESC', 2: u'!', 3: u'@', 4: u'#', 5: u'$', 6: u'%', 7: u'^', 8: u'&', 9: u'*',
    10: u'(', 11: u')', 12: u'_', 13: u'+', 14: u'BKSP', 15: u'TAB', 16: u'Q', 17: u'W', 18: u'E', 19: u'R',
    20: u'T', 21: u'Y', 22: u'U', 23: u'I', 24: u'O', 25: u'P', 26: u'{', 27: u'}', 28: u'CRLF', 29: u'LCTRL',
    30: u'A', 31: u'S', 32: u'D', 33: u'F', 34: u'G', 35: u'H', 36: u'J', 37: u'K', 38: u'L', 39: u':',
    40: u'\'', 41: u'~', 42: u'LSHFT', 43: u'|', 44: u'Z', 45: u'X', 46: u'C', 47: u'V', 48: u'B', 49: u'N',
    50: u'M', 51: u'<', 52: u'>', 53: u'?', 54: u'RSHFT', 56: u'LALT', 100: u'RALT'
}

def rfidRead():
  dev = None
  caps = False
  res = ''
  global ALIVE
  global refreshDisplay
  global badging

  valid = re.compile(r"^[0-9a-f]{3}")
  while ALIVE:
        if (dev is None):
                try:
                        dev = InputDevice("/dev/input/by-id/usb-13ba_Barcode_Reader-event-kbd")
                        #usb-13ba_Barcode_Reader-event-kbd")
                        #usb-OEM_RFID_Device__Keyboard_-event-kbd
                        print(dev)
                        dev.grab()
                        print (u"grabbed!")
                except:
                        dev = None
                        # Waiting for scanner to be available
                        time.sleep(2.0)
        else:
            try:
                for event in dev.read():
                        if not ALIVE:
                                break
                        if event.type == ecodes.EV_KEY:
                                data = categorize(event)
                                if data.scancode == 42:
                                        caps = False
                                if data.keystate == 1:
                                        if data.scancode == 28:
                                                print(res)
                                                if res:
                                                   #res = res[:3].lower()
                                                   intcode = int(res)
                                                   res = "%0.8x" % intcode
                                                   lres = len(res)
                                                   res = res[lres-2]+res[lres-1]+res[lres-4]
                                                   if valid.match(res):
                                                     try:
                                                        if not res in badging.keys():
                                                                badging[res] = {'timestamp':datetime.datetime.now(),'incoming':True,'timespan':None}
                                                        else:
                                                                now = datetime.datetime.now()
                                                                badging[res]['timespan'] = now - badging[res]['timestamp']
                                                                badging[res]['timestamp'] = now
                                                                badging[res]['incoming'] = not badging[res]['incoming']
                                                                refreshDisplay = True
                                                     except:
                                                        traceback.print_exc()
                                                   res=''
                                        elif data.scancode == 42:
                                                caps = True
                                        else:
                                                if caps:
                                                        res += capscodes[data.scancode]
                                                else:
                                                        res += scancodes[data.scancode]
            except io.BlockingIOError:
                time.sleep(0.01)
            except IOError as anError:
                if anError.errno == 11:
                        time.sleep(0.01)
                else:
                        traceback.print_exc()
                        try:
                                dev.ungrab()
                                print (u"ungrabbed")
                        except:
                                pass
                        dev = None
            except:
                traceback.print_exc()
                try:
                        dev.ungrab()
                        print ("ungrabbed")
                except:
                        pass
                dev = None
            else:
                time.sleep(0.1)

threadRFID = threading.Thread(target=rfidRead)
threadRFID.start()

def tension():
        try:
                bus_pi = smbus.SMBus(1)
                ADCaddr = 0x6E
                global ALIVE
                while ALIVE:
                
                    
                    #os.system("i2cset -y 1 0x6E 0x98")
                    time.sleep(15)
                    bus_pi.write_byte(ADCaddr,0x98)# va charger la valeur du registre
                                                # dans le mcp
                    """print 'ADC I2C:',hex(addr)"""
                    xa = bus_pi.read_word_data(ADCaddr,0)# recupère la valeur en décimal
                    x = hex(xa)
                    #print x
                    x1 = x[4:6] # les 2 premier Bytes et les 2 derniers doivent                    
                    x2 = x[2:4] # être inversé pour récupérer la bonne valeur

                    x1b = int(x1,16)*256                
                    x2b = int(x2,16)
                    tens = x1b + x2b
                    tens = (tens*0.0625)/1000 # 0.0625 codé sur 16 bits
                                              # et /1000 pour avoir la valeur en volt
                    tens= tens*9.4727 # 9.4727 est le coefficient du pont diviseur de
                                      # tension qui est placé au borne de l'ADC
                    tens = round(tens, 2) # Arrondi la valeur au centième près

                    if tens < 4:
                        #print ("Sous tension")
                        pass
                    else:
                        if tens <= 10.8:
                            print (tens,"V lower than 10.8V...")
                            time.sleep(5)
                            bus_pi.write_byte(ADCaddr,0x98)
                            xa = bus_pi.read_word_data(ADCaddr,0)
                            x = hex(xa) 
                            x1 = x[4:6]                    
                            x2 = x[2:4]

                            x1b = int(x1,16)*256
                            x2b = int(x2,16)
                            tens = x1b + x2b
                            tens = (tens*0.0625)/1000
                            tens= tens*9.4727
                            tens = round(tens, 2)
                            if tens < 10.8:
                                print(tens,"V : Shutdown...")
                                ALIVE = False
                                #os.system("sudo shutdown now")
                        else:  
                            print'battery:', tens,'V'
        except:
                traceback.print_exc()
                    
threadADC = threading.Thread(target=tension)
threadADC.start()

#ow.init('/mnt/1wire')

# Initialize the keypad class
gpio=PIG
kp = keypad()

keys = [ '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '*', '#', '#' ]
#symbols = [ u'\ue259',
#           u'\ue021', u'\ue010', u'\ue008',
#            u'\ue166', u'\ue123', u'\ue072',
#            u'\ue073', u'\ue260', u'\ue136',
#            u'\ue093', u'\ue013', u'\ue185' ]

# The main States are:
msSteps = 20
msList = msSteps
msBranch = msSteps*2
msGraph = msSteps*3
msNum = msSteps*4

# Generic Events keys
gPrev = 8
gNext = 0
gNum  = 9
gMain = 10
gConf = 11
gConf2 = 12

symbols = keys[:]
symbols[gNext]       = u'\ue259'
symbols[aPlace]      = u'\ue021'
symbols[aBatch]      = u'\ue010'
symbols[aPerson]     = u'\ue008'
symbols[aMeasure]    = u'\ue166'
symbols[aAlarm]      = u'\ue123'
symbols[aAlarmTrig]  = u'\ue072'
symbols[aAlarmResol] = u'\ue073'
symbols[gPrev]       = u'\ue260'
symbols[gNum]        = u'\ue136'
symbols[gMain]       = u'\ue093'
symbols[gConf]       = u'\ue013'
symbols[gConf2]      = u'\ue185'

# The events for time slices:  
tHour = 1
tDay  = 2
tWeek = 3
tMonth= 4
tYear = 5

##fsm = Fysom({'initial':'BranchMain',
##             'events' : [ ]})

def showKey(aKey, dispSymb, showIt, x, y):
        "Shows a key on screen"
        time.sleep(0.003)
        endPos = x+5
        draw.rectangle((x,y,x+5,y+8),fill=255)
        draw.text((x+1, y), keys[aKey], font=font, fill=0)
        if (dispSymb):
                if showIt:
                        draw.text((endPos+2, y-1), symbols[aKey], font=fontG10, fill=255)
                endPos = endPos+12
        return endPos

def strDelta(timespan):
  if timespan == None:
    return ""
  else:
    result = ""
    if timespan.days != 0:
        result = str(timespan.days)+"j"+(" " if not timespan.seconds == 0 else "")
    if timespan.seconds != 0:
        result = result + str(int(timespan.seconds/3600))+"h "+str(int((timespan.seconds%3600)/60))+"m"
    return result

def eventDisplay(linepos,id,timestamp,value,timespan,alarm):
        "Shows an event on screen"
        time.sleep(0.003)
        strnow = timestamp.strftime("%H:%M")
        draw.text((4,linepos+1), strnow, font=font,fill=255)
        if idDefinitions.has_key(id):
                symbol = symbols[idDefinitions[id]['typed']]
                strid = idDefinitions[id]['lcd']
        else:
                symbol = None
                strid = id
        if not symbol == None:
                draw.text((28,linepos), symbol, font=fontG10, fill=255)
        draw.rectangle((39,linepos,40+draw.textsize(strid,font=font)[0],linepos+10),fill=255)
        draw.text((40,linepos+1), strid, font=font,fill=0)
        draw.text((68,linepos+1), value, font=font,fill=255)
        if not timespan == None:
                draw.text((84,linepos+1), strDelta(timespan), font=font,fill=255)
        if not alarm == None:
                draw.text((123,linepos), symbols[aAlarm], font=fontG10, fill=255)
                draw.text((102,linepos+1), alarm, font=font, fill=255)

def id1Def(anItem,aType):
        if not anItem[0][3:4] == '.':
                print(anItem[0]+u" : mauvaise clé de configuration")
                return
        thing = anItem[0][:3].lower()
        attrib = anItem[0][4:].lower()
        if not idDefinitions.has_key(thing):
                idDefinitions[thing] = {'identified':thing,'lcd':thing,'name':thing,'min':-999.99,'max':999.99,'typed':aType}
        if attrib == 'max' or attrib == 'min':
                idDefinitions[thing][attrib] = float(anItem[1])
        else:
                idDefinitions[thing][attrib] = anItem[1]

def idDef():
        global idDefinitions
        idDefinitions = {}
        config = ConfigParser.RawConfigParser()
        try:
                config.readfp(codecs.open(os.path.expanduser(CONFdirectory+'/frigos.ini'),'r','utf8'))
                print(config.sections())
                #print(config.items('DEFAULT'))
        except:
                traceback.print_exc()   
        else:
                try:
                        for anItem in config.items('personnes'):
                                id1Def(anItem,aPerson)
                except ConfigParser.NoSectionError:
                        traceback.print_exc()   
                try:
                        for anItem in config.items('lieux'):
                                id1Def(anItem,aPlace)
                except ConfigParser.NoSectionError:
                        traceback.print_exc()   
                try:
                        for anItem in config.items('mesures'):
                                id1Def(anItem,aMeasure)
                except ConfigParser.NoSectionError:
                        traceback.print_exc()   
                try:
                        for anItem in config.items('lots'):
                                id1Def(anItem,aBatch)
                except ConfigParser.NoSectionError:
                        traceback.print_exc()   

        for anItem in idDefinitions:
                print(anItem, idDefinitions[anItem])

idDef()

alarmblink = False
state = 0
chapter = 10
begScreen = 4
endScreen = 131
lineHeight = 13

try:
        while ALIVE:
                draw.rectangle((0,0,131,63),fill=0)
                linePos = 0
        
                # Check if alarm condition apply and create an error message
                # If error message, alert the owner
                # Browse the available measures and display them

                for nSensor,aSensor in sensors.iteritems():
                        eventDisplay (linePos, nSensor,aSensor['timestamp'],str(aSensor['data'])+u"°C", None,aSensor['alarm'])
                        linePos += lineHeight
                
                # Browse the defined people/batch and display their status
                for nBadge,aBadge in badging.iteritems():
                        eventDisplay (linePos, nBadge,aBadge['timestamp'],u"IN" if aBadge['incoming'] else u"out",aBadge['timespan'],None)
                        linePos += lineHeight

                # Display image.
                disp.image(image)
                try:
                        disp.display()
                except:
                        traceback.print_exc()
                refreshDisplay = False
                # Loop while waiting for a keypress
                digit = None
                slept = 0
                while ALIVE and (digit == None) and (slept < 1) and not refreshDisplay:
                        digit = kp.getKey()
                        slept += 0.01
                        if digit != None:
                            print ("#"+str(digit))
                            if digit == 9:
                                idDef()
                            if digit == 11:
                                ALIVE = False
                        time.sleep(0.01)
                        slept += 0.01
except:
        syslog.syslog(syslog.LOG_ERR, u"FRIGOS ABORTED")
        traceback.print_exc()
        ALIVE = False
time.sleep(0.2)
PIG.stop()

