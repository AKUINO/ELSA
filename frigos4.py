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
import ow
import smbus
import evdev

from select import select
from evdev import InputDevice, categorize, ecodes

from ConfigurationELSA import *
from LectureBarcode import *
from bluetoothScanner import *
from I2CScreen import *

# ALIM_BREAKOUT_V = 10.8 # C-TEC Power supply
ALIM_BREAKOUT_V = 11.6  # Meanwelll Power supply

ELAdirectory = '/run/akuino/ELA'
## RPi2 = ttyAMA0
ELAtty = '/dev/ttyS0'
CONFdirectory = '~/akuino'

# Raspberry Pi pin configuration:
RST = 25

# Code source dans le meme repertoire
from keypadClass30 import keypad

# Ensure UTF-8 for the output terminal
UTF8Writer = codecs.getwriter('utf8')
sys.stdout = UTF8Writer(sys.stdout)

# Allow graceful stop of the processes
Alive = True

# GPIO.setmode(GPIO.BCM)
#GPIO.setup(5, GPIO.OUT)
#GPIO.output(5, GPIO.LOW)
# time.sleep(0.05)
#GPIO.output(5, GPIO.HIGH)
# time.sleep(0.05)

PIG = pigpio.pi()

telOwner = u"0032475776211"

#sm = gammu.StateMachine()
# sm.ReadConfig()
# sm.Init()

if True:  # Put False if no screen available
    # 128x64 display with hardware I2C:
    screen = I2CScreen(True, disp=SSD1306.SSD1305_132_64(rst=RST, gpio=PIG))
else:
    screen = I2CScreen(False, disp=None)


# CONFIGURATION ELSA

c = Configuration()
c.load()

bluetooth = bluetoothScanner()
bluetooth.config = c
bluetooth.screen = screen

# Pour les lots dans la liste de lots
#	Si ils sont dans la même piece que le senseur et dans le même equipement du senseur
#		Pour les mesures dans l'étape actuelle, si l'id de la mesure correspond à la mesure du senseur
#			Pour les mesure dans le lot actuel
#			Si l'id de la mesure correspond a la mesure du senseur alors on le met a jour


def StepValuesUpdate(currSensor, value):
    if(currSensor != None):
        for batch in c.AllBatches.elements:
            if (c.AllBatches.elements[batch].piece != "" and c.AllBatches.elements[batch].piece.fields['p_id'] == currSensor.fields['p_id']):
                if (c.AllBatches.elements[batch].equipment == currSensor.fields['e_id'] or c.AllBatches.elements[batch].equipment.fields['e_id'] == currSensor.fields['e_id']):
                    for stepmeasure in c.AllBatches.elements[batch].currStep.stepmeasures:
                        if (c.AllBatches.elements[batch].currStep.stepmeasures[stepmeasure].fields['m_id'] == currSensor.fields['m_id']):
                            for stepvalue in c.AllBatches.elements[batch].stepValues:
                                sv = c.AllBatches.elements[batch].stepValues[stepvalue]
                                if (sv.measure.fields['m_id'] == currSensor.fields['m_id']):
                                    data = float(value)
                                    sv.total += data
                                    sv.number += 1
                                    if data > sv.max:
                                        sv.max = data
                                    if data < sv.min:
                                        sv.min = data
                                    print(
                                        c.AllBatches.elements[batch].fields['b_id'] + " modified...")


# Lance les alertes

def alertOwner(currSensor):
    global typeNames
    global telOwner
    message = u"Capteur "+defins['name']+u"="+str(currSensor.data)
    if currSensor.alarm == None:
        message = message + u" OK"
    else:
        # +u"="+str(defins[transac['alarm']])
        message = message + u" enfreint "+currSensor.alarm
    print message
    result = subprocess.check_output(['gammu-smsd-inject', 'TEXT', telOwner, '-len', str(len(
        message)), '-unicode', '-text', message], stdin=None, stderr=None, shell=False, universal_newlines=True)
    print result


def storeSensor(currSensor, temperature):
    if currSensor:
        owtemperature = float(temperature)
        prevAlarm = None
        if hasattr(currSensor, 'alarm'):
            prevAlam = currSensor.alarm
        currSensor.data = round(owtemperature, 1)
        currSensor.alarm = None
# if owtemperature < currSensor.min:
##                currSensor.alarm = 'min'
# if owtemperature > currSensor.max:
##                currSensor.alarm = 'max'
        currSensor.timestamp = datetime.datetime.now()
        if not prevAlarm == currSensor.alarm:
            alertOwner(currSensor)


def elaRead():
    global temperature
    global Alive
    global screen
    try:
        elaSerial = serial.Serial(ELAtty, 9600, timeout=0.01)
        time.sleep(0.05)
        # reset to manufacturer settings
        elaSerial.write('[9C5E01]')
        line = None
        while Alive:
            try:
                data = elaSerial.read()
                if data == '[':
                    line = []
                elif line != None:
                    if data == ']':
                        if len(line) == 10:
                            RSS = int(line[0]+line[1], 16)
                            HEX = line[2]+line[3]+line[4]
                            ADDRESS = int(HEX, 16)
                            VAL = int(line[5]+line[6]+line[7], 16)
                            READER = int(line[8]+line[9], 16)
                            if VAL >= 2048:
                                VAL = VAL - 4096
                            temperature = VAL*60.0/960
                            with open(ELAdirectory+'/'+str(ADDRESS)+'.dat', 'w') as aFile:
                                aFile.write(str(temperature))
                            print "ELA="+HEX+", RSS="+str(RSS)+", val="+str(VAL)
                            currSensor = None
                            for sensor in c.AllSensors.elements:
                                currSensor = c.AllSensors.elements[sensor]
                                if (currSensor.fields['sensor'].translate(None, '. ') == HEX.translate(None, '. ')):
                                    print(
                                        u"Sensor ELA-" + currSensor.fields['sensor'] + u": " + currSensor.fields['acronym'] + u" = "+str(temperature))
                                    storeSensor(currSensor, str(temperature))
                                    StepValuesUpdate(
                                        currSensor, str(temperature))
                        line = None
                    else:
                        line.append(data)
            except:
                traceback.print_exc()
        elaSerial.close()
        print(ELAtty+u" libre")
    except:
        traceback.print_exc()
        Alive = False
    return


if not os.path.exists(ELAdirectory):
    os.makedirs(ELAdirectory)

threadELA = threading.Thread(target=elaRead)
threadELA.start()


def owRead():
    global Alive
    global paging
    global screen
    ow.init("/dev/i2c-1")
    owDevices = ow.Sensor("/")
    try:
        while Alive:
            time.sleep(15)
            for sensor in c.AllSensors.elements:
                currSensor = c.AllSensors.elements[sensor]
                if (currSensor.fields['channel'].translate(None, '. ') == "wire"):
                    try:
                        aDevice = ow.Sensor('/'+currSensor.fields['sensor'])
                        if aDevice:
                            owtemperature = aDevice.__getattr__(
                                currSensor.fields['subsensor'])
                            if owtemperature:
                                if currSensor.fields['formula']:
                                    value = float(owtemperature)
                                    owtemperature = str(
                                        eval(currSensor.fields['formula']))
                                print(
                                    u"Sensor 1Wire-" + currSensor.fields['sensor']+u": " + currSensor.fields['acronym'] + " = " + owtemperature)
                                storeSensor(currSensor, owtemperature)
                                StepValuesUpdate(currSensor, owtemperature)
                    except:
                        traceback.print_exc()
    except:
        traceback.print_exc()
        Alive = False
    return


threadOW = threading.Thread(target=owRead)
threadOW.start()

threadBlueTooth = bluetooth.start()

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


class InputEventThread(threading.Thread):

    def __init__(self, currScanner):
        threading.Thread.__init__(self)
        self.scanner = currScanner
        self.dev = evdev.InputDevice(
            "/dev/input/event"+str(self.scanner.numDev))

    def run(self):
        global Alive
        global screen

        self.dev.grab()
        print(self.dev.fn, u"grabbed !")
        self.Alive = True
        time.sleep(0.01)

        res = ""
        while Alive and self.Alive:
            caps = False
            try:
                for event in self.dev.read():
                    # print event
                    if not Alive:
                        break
                    if not self.Alive:
                        break
                    if event.type == evdev.ecodes.EV_KEY:
                        data = evdev.categorize(event)
                        if data.scancode == 42:
                            caps = not data.keystate == 0
                        elif data.keystate == 1:
                            if data.scancode == 28:
                                print("\n " + str(self.scanner.rank) + ":  " + res)
                                if self.scanner.rank in allReaders:
                                    contexte = allReaders[self.scanner.rank]
                                else:
                                    contexte = BarcodeReader(self.scanner, c)
                                with screen.lock:
                                    isNow = datetime.datetime.now()
                                    self.scanner.last = isNow
                                    screen.refreshDisplay = isNow + \
                                        datetime.timedelta(seconds=12)
                                    contexte.BarcodeIn(
                                        res[:13], screen, isNow, bluetooth)
                                res = ''
                            else:
                                # print(data.scancode)
                                try:
                                    if caps:
                                        res += capscodes[int(data.scancode)]
                                    else:
                                        res += scancodes[int(data.scancode)]
                                except:
                                    print("Invelid key:", data.scancode)

                    # else:
                       # print event
            except io.BlockingIOError:
                print("Blocking")
                time.sleep(0.01)
            except IOError as anError:
                if anError.errno == 11:
                    #print (self.dev.fn,anError)
                    time.sleep(0.001)
                elif anError.errno == 19:
                    self.Alive = False  # device has disappeared
                    try:
                        self.dev.ungrab()
                        print("ungrabbed 19")
                    except:
                        pass
                else:
                    traceback.print_exc()
                    try:
                        self.dev.ungrab()
                        print(u"ungrabbed IOerror")
                    except:
                        pass
                    break
            except:
                traceback.print_exc()
                try:
                    self.dev.ungrab()
                    print("ungrabbed other")
                except:
                    pass
                break
            time.sleep(0.001)
        self.Alive = False


def InputListThread():
    global screen
    global Alive
    global bluetoothScanner

# UTILISER /proc/bus/input/devices
    physical = None
    looping = 0
    while Alive:
        looping += 1
        if ((looping % 8) == 0) or screen.newConnect:
            with screen.lock:
                looping = 0
                screen.newConnect = False
                device = ""
                somethingDisplayed = False
                try:
                    fInputDevices = open("/proc/bus/input/devices", 'r')
                    activeSet = []
                    screen.devConnected = ""
                    for inputLine in fInputDevices:
                        if inputLine[:8] == 'U: Uniq=':
                            physical = inputLine[8:].strip()
                        elif inputLine[:12] == 'H: Handlers=':
                            for capab in inputLine[12:].strip().split(' '):
                                if capab[:5] == 'event':
                                    numDev = int(capab[5:])
                                    if physical:
                                        key = c.AllScanners.makeKey(physical)
                                        physical = None
                                        if key in c.AllScanners.elements:
                                            activeSet.append(key)
                                            currScanner = c.AllScanners.elements[key]
                                            currScanner.numDev = numDev
                                            currScanner.paired = True

                                            screen.devConnected += str(
                                                currScanner.rank)
                                            if currScanner.reader is None:
                                                currScanner.reader = InputEventThread(
                                                    currScanner)
                                            elif (not currScanner.reader.is_alive()) or (not currScanner.reader.Alive):
                                                currScanner.reader = InputEventThread(
                                                    currScanner)
                                            else:
                                                continue  # Thread still alive
                                            currScanner.reader.start()

                                            if not somethingDisplayed:
                                                screen.refreshDisplay = datetime.datetime.now() + datetime.timedelta(seconds=6)
                                                screen.draw.rectangle(
                                                    (screen.begScreen, 0, 131, 63), fill=0)
                                                screen.linePos = 0
                                                strnow = screen.refreshDisplay.strftime(
                                                    "%H:%M")
                                                screen.draw.text(
                                                    (screen.begScreen, screen.linePos+1), strnow, font=screen.font, fill=255)
                                                screen.linePos += screen.lineHeight
                                                somethingDisplayed = True
                                            screen.draw.text((screen.begScreen, screen.linePos+1), "Connect "+str(
                                                currScanner.rank)+"#"+str(currScanner.id), font=screen.font, fill=255)
                                            screen.linePos += screen.lineHeight
                                            screen.draw.text(
                                                (screen.begScreen, screen.linePos+1), "            "+currScanner.mac, font=screen.font, fill=255)
                                            screen.linePos += screen.lineHeight

                    for key in c.AllScanners.elements:
                        if key in activeSet:
                            pass
                        else:
                            currScanner = c.AllScanners.elements[key]
                            if currScanner.reader:
                                currScanner.reader.Alive = False
                    if somethingDisplayed:
                        screen.show(screen.devConnected)
                        time.sleep(0.01)
                except:
                    traceback.print_exc()
            if not screen.devConnected and not bluetooth.pairing:
                screen.draw.text(
                    (4, screen.linePos+1), u"Bluetooth Pairing", font=screen.font, fill=255)
                screen.linePos += screen.lineHeight
                bluetooth.pairingDevice()
                if bluetooth.startScan:
                    screen.devConnected += "*"
                screen.show(screen.devConnected)
            elif bluetooth.startScan:
                screen.devConnected += "*"
            time.sleep(2.0)


threadList = threading.Thread(target=InputListThread)
threadList.start()

ADCconf = 0x98
ADCaddr = 0x69


def tension():
    try:
        bus_pi = smbus.SMBus(1)
        global Alive
        while Alive:

                            #os.system("i2cset -y 1 0x6E 0x98")
            time.sleep(20)
            # bus_pi.write_byte(ADCaddr,0x98)# va charger la valeur du registre
            # dans le mcp
            """print 'ADC I2C:',hex(addr)"""
            # xa = bus_pi.read_word_data(ADCaddr,0)# recupère la valeur en décimal
            xa = bus_pi.read_i2c_block_data(ADCaddr, ADCconf, 3)
            if len(xa) < 2:
                continue
            x1 = xa[0]  # les 2 premier Bytes et les 2 derniers doivent
            x2 = xa[1]  # être inversé pour récupérer la bonne valeur
            #x1b = int(x1,16)*256
            #x2b = int(x2,16)
            tens = (x1*256) + x2
            if tens >= 32768:
                tens = tens - 65536
            tens = (tens*0.0625)/1000  # 0.0625 codé sur 16 bits
            # et /1000 pour avoir la valeur en volt
            tens = tens*9.4727  # 9.4727 est le coefficient du pont diviseur de
            # tension qui est placé au borne de l'ADC
            tens = round(tens, 2)  # Arrondi la valeur au centième près

            if tens < 4:
                #print ("Sous tension")
                pass
            else:
                if tens <= ALIM_BREAKOUT_V:
                    print(tens, "V lower than "+str(ALIM_BREAKOUT_V)+"...")
                    time.sleep(5)
                    bus_pi.write_byte(ADCaddr, ADCconf)
                    xa = bus_pi.read_i2c_block_data(ADCaddr, 0)
                    if len(xa) < 3:
                        continue
                    x = hex(xa)
                    x1 = x[4:6]
                    x2 = x[2:4]
                    tens = (x1*256) + x2
                    if tens >= 32768:
                        tens = tens - 65536
                    tens = (tens*0.0625)/1000
                    tens = tens*9.4727
                    tens = round(tens, 2)
                    if tens < ALIM_BREAKOUT_V:
                        print(tens, "V : Shutdown...")
                        Alive = False
                        os.system("sudo shutdown now")
                else:
                    print 'Sensor battery: '+str(tens)+' V'
                for sensor in c.AllSensors.elements:
                    currSensor = c.AllSensors.elements[sensor]
                    if (currSensor.fields['channel'].translate(None, '. ') == "batt"):
                        try:
                            storeSensor(currSensor, str(tens))
                            StepValuesUpdate(currSensor, str(tens))
                        except:
                            traceback.print_exc()
    except:
        traceback.print_exc()


threadADC = threading.Thread(target=tension)
threadADC.start()

# ow.init('/mnt/1wire')

# Initialize the keypad class
gpio = PIG
kp = keypad()

keys = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '*', '#', '#']
# symbols = [ u'\ue259',
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
gNum = 9
gMain = 10
gConf = 11
gConf2 = 12

##symbols = keys[:]
##symbols[gNext]       = u'\ue259'
##symbols[aPlace]      = u'\ue021'
##symbols[aBatch]      = u'\ue010'
##symbols[aPerson]     = u'\ue008'
##symbols[aMeasure]    = u'\ue166'
##symbols[aAlarm]      = u'\ue123'
##symbols[aAlarmTrig]  = u'\ue072'
##symbols[aAlarmResol] = u'\ue073'
##symbols[gPrev]       = u'\ue260'
##symbols[gNum]        = u'\ue136'
##symbols[gMain]       = u'\ue093'
##symbols[gConf]       = u'\ue013'
##symbols[gConf2]      = u'\ue185'

# The events for time slices:
tHour = 1
tDay = 2
tWeek = 3
tMonth = 4
tYear = 5

# fsm = Fysom({'initial':'BranchMain',
# 'events' : [ ]})


def showKey(aKey, dispSymb, showIt, x, y):
    "Shows a key on screen"
    time.sleep(0.003)
    endPos = x+5
    draw.rectangle((x, y, x+5, y+8), fill=255)
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
            result = str(timespan.days)+"j" + \
                (" " if not timespan.seconds == 0 else "")
        if timespan.seconds != 0:
            result = result + str(int(timespan.seconds/3600)) + \
                "h "+str(int((timespan.seconds % 3600)/60))+"m"
        return result


def eventDisplay(screen, strid, timestamp, value, timespan, alarm):
    "Shows an event on screen"
    time.sleep(0.003)
    strnow = timestamp.strftime("%H:%M")
    screen.draw.text((screen.begScreen, screen.linePos+1),
                     strnow, font=screen.font, fill=255)
    screen.draw.rectangle((28, screen.linePos, 30+screen.draw.textsize(strid,
                                                                       font=screen.font)[0], screen.linePos+10), fill=255)
    screen.draw.text((30, screen.linePos+1), strid, font=screen.font, fill=0)
    screen.draw.text((68, screen.linePos+1), value, font=screen.font, fill=255)
    if not timespan == None:
        draw.text((84, screen.linePos+1), strDelta(timespan),
                  font=screen.font, fill=255)
    if not alarm == None:
        screen.draw.text((123, screen.linePos),
                         symbols[aAlarm], font=screen.fontG10, fill=255)
        screen.draw.text((102, screen.linePos+1), alarm,
                         font=screen.font, fill=255)


alarmblink = False
state = 0
chapter = 10
paging = 0
print "STARTED"
try:
    while Alive:
        time.sleep(0.01)
        isNow = datetime.datetime.now()
        if isNow > screen.refreshDisplay:
            with screen.lock:
                screen.refreshDisplay = isNow + datetime.timedelta(seconds=6)
                screen.draw.rectangle((0, 0, 131, 63), fill=0)
                screen.linePos = 0

                # Check if alarm condition apply and create an error message
                # If error message, alert the owner
                # Browse the available measures and display them
                i = 0
                for nSensor in c.AllSensors.elements:
                    currSensor = c.AllSensors.elements[nSensor]
                    if hasattr(currSensor, 'data'):
                        i += 1
                        if i < paging:
                            continue
                        if screen.linePos > 58:
                            paging = i
                            break
                        eventDisplay(screen, currSensor.fields['acronym'],
                                     currSensor.timestamp if hasattr(
                                         currSensor, 'timestamp') else "",
                                     str(currSensor.data)+u" ", None,
                                     currSensor.alarm if hasattr(currSensor, 'alarm') else "")
                        screen.linePos += screen.lineHeight
                if (i > paging):  # last screen
                    paging = 0
                screen.show(screen.devConnected)
        # Loop while waiting for a keypress
        digit = None
        slept = 0
        while Alive and (digit == None) and (slept < 1):
            digit = kp.getKey()
            slept += 0.01
            if digit != None:
                print("#"+str(digit))
                if digit == 9:
                    idDef()
                if digit == 11:
                    Alive = False
            time.sleep(0.01)
            slept += 0.01
except:
    syslog.syslog(syslog.LOG_ERR, u"FRIGOS ABORTED")
    traceback.print_exc()
    Alive = False
bluetooth.alive = False
time.sleep(0.2)
threadList.join()
time.sleep(0.2)
PIG.stop()
