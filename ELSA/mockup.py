import resource
import subprocess
import threading
import traceback
import syslog
import serial
from fysom import Fysom
from . import SSD1306
from keypadClass4 import keypad

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

from select import select
from evdev import InputDevice, categorize, ecodes

# Allow graceful stop of the processes
ALIVE = True

# Raspberry Pi pin configuration:
RST = 5
# GPIO.setmode(GPIO.BCM)
#GPIO.setup(5, GPIO.OUT)
#GPIO.output(5, GPIO.LOW)
# time.sleep(0.05)
#GPIO.output(5, GPIO.HIGH)
# time.sleep(0.05)

PIG = pigpio.pi()
# 128x64 display with hardware I2C:
disp = SSD1306.SSD1305_132_64(rst=RST, gpio=PIG)

# Initialize library.
disp.begin()

# Clear display.
disp.clear()

# Create blank image for drawing.
# Make sure to create image with mode '1' for 1-bit color.
width = disp.width
height = disp.height
image = Image.new('1', (width, height))

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# Default font = better than
#font = ImageFont.load_default()

# Alternatively load a TTF font.  Make sure the .ttf font file is in the same directory as the python script!
# Some other nice fonts to try: http://www.dafont.com/bitmap.php
font = ImageFont.truetype('sans.ttf', 9)
fontG8 = ImageFont.truetype('glyphicons-halflings-regular.ttf', 8)
fontG10 = ImageFont.truetype('glyphicons-halflings-regular.ttf', 10)
degree = '\N{DEGREE SIGN}'

temperature = 0.0
owtemperature = ''

ELAdirectory = '/run/akuino/ELA'
ELAtty = '/dev/ttyAMA0'


def elaRead():
    global temperature
    global ALIVE
    try:
        elaSerial = serial.Serial(ELAtty, 9600, timeout=0.01)
        time.sleep(0.05)
        # reset to manufacturer settings
        elaSerial.write('[9C5E01]')
        line = None
        while ALIVE:
            try:
                data = elaSerial.read()
                if data == '[':
                    line = []
                elif line != None:
                    if data == ']':
                        if len(line) == 10:
                            RSS = int(line[0]+line[1], 16)
                            ADDRESS = int(line[2]+line[3]+line[4], 16)
                            VAL = int(line[5]+line[6]+line[7], 16)
                            READER = int(line[8]+line[9], 16)
                            if VAL >= 2048:
                                VAL = - (VAL - 2048)
                            temperature = VAL*60.0/960
                            aFile = open(ELAdirectory+'/' +
                                         str(ADDRESS)+'.dat', 'w')
                            aFile.write(str(temperature))
                            aFile.close()
                        line = ''.join(line)
                        print(line)
                        #syslog.syslog(syslog.LOG_ERR, line)
                        line = None
                    else:
                        line.append(data)
            except:
                pass
        elaSerial.close()
        print((ELAtty+" libre"))
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
    try:
        owList = subprocess.check_output(
            ['owdir', '/'], stdin=None, stderr=None, shell=False, universal_newlines=True)
        print(owList)
        while ALIVE:
            time.sleep(15.0)
            try:
                owtemperature = subprocess.check_output(
                    ['owget', '/21.1ABF39000000/temperature'], stdin=None, stderr=None, shell=False, universal_newlines=False).strip()
                print(owtemperature)
                #syslog.syslog(syslog.LOG_ERR, owtemperature)
            except:
                pass
    except:
        traceback.print_exc()
        ALIVE = False
    return


threadOW = threading.Thread(target=owRead)
threadOW.start()

scancodes = {
    # Scancode: ASCIICode
    0: None, 1: 'ESC', 2: '1', 3: '2', 4: '3', 5: '4', 6: '5', 7: '6', 8: '7', 9: '8',
    10: '9', 11: '0', 12: '-', 13: '=', 14: 'BKSP', 15: 'TAB', 16: 'q', 17: 'w', 18: 'e', 19: 'r',
    20: 't', 21: 'y', 22: 'u', 23: 'i', 24: 'o', 25: 'p', 26: '[', 27: ']', 28: 'CRLF', 29: 'LCTRL',
    30: 'a', 31: 's', 32: 'd', 33: 'f', 34: 'g', 35: 'h', 36: 'j', 37: 'k', 38: 'l', 39: ';',
    40: '"', 41: '`', 42: 'LSHFT', 43: '\\', 44: 'z', 45: 'x', 46: 'c', 47: 'v', 48: 'b', 49: 'n',
    50: 'm', 51: ',', 52: '.', 53: '/', 54: 'RSHFT', 56: 'LALT', 100: 'RALT'
}

capscodes = {
    0: None, 1: 'ESC', 2: '!', 3: '@', 4: '#', 5: '$', 6: '%', 7: '^', 8: '&', 9: '*',
    10: '(', 11: ')', 12: '_', 13: '+', 14: 'BKSP', 15: 'TAB', 16: 'Q', 17: 'W', 18: 'E', 19: 'R',
    20: 'T', 21: 'Y', 22: 'U', 23: 'I', 24: 'O', 25: 'P', 26: '{', 27: '}', 28: 'CRLF', 29: 'LCTRL',
    30: 'A', 31: 'S', 32: 'D', 33: 'F', 34: 'G', 35: 'H', 36: 'J', 37: 'K', 38: 'L', 39: ':',
    40: '\'', 41: '~', 42: 'LSHFT', 43: '|', 44: 'Z', 45: 'X', 46: 'C', 47: 'V', 48: 'B', 49: 'N',
    50: 'M', 51: '<', 52: '>', 53: '?', 54: 'RSHFT', 56: 'LALT', 100: 'RALT'
}


def rfidRead():
    dev = None
    caps = False
    global ALIVE
    while ALIVE:
        if (dev is None):
            try:
                dev = InputDevice(
                    "/dev/input/by-id/usb-OEM_RFID_Device__Keyboard_-event-kbd")
                print(dev)
                dev.grab()
            except:
                dev = None
                # Waiting for scanner to be available
                time.sleep(2.0)
        else:
            try:
                res = ''
                for event in dev.read_loop():
                    if not ALIVE:
                        break
                    if event.type == ecodes.EV_KEY:
                        data = categorize(event)
                        if data.scancode == 42:
                            caps = False
                        if data.keystate == 1:
                            if data.scancode == 28:
                                print(res)
                                res = ''
                            elif data.scancode == 42:
                                caps = True
                            else:
                                if caps:
                                    res += capscodes[data.scancode]
                                else:
                                    res += scancodes[data.scancode]
            except:
                try:
                    dev.ungrab()
                except:
                    pass
                dev = None
                pass
            time.sleep(0.1)


threadRFID = threading.Thread(target=rfidRead)
threadRFID.start()


def tree(sensor):
    print('%7s - %s' % (sensor._type, sensor._path))
    for next in sensor.sensors():
        if next._type in ['DS2409', ]:
            tree(next)
        else:
            print('%7s - %s' % (next._type, next._path))

# ow.init('/mnt/1wire')


# Initialize the keypad class
gpio = PIG
kp = keypad()

keys = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '*', '#', '#']
# symbols = [ u'\ue259',
#	    u'\ue021', u'\ue010', u'\ue008',
#            u'\ue166', u'\ue123', u'\ue072',
#            u'\ue073', u'\ue260', u'\ue136',
#            u'\ue093', u'\ue013', u'\ue185' ]

# The main States are:
msSteps = 20
msList = msSteps
msBranch = msSteps*2
msGraph = msSteps*3
msNum = msSteps*4

# The Sub-States are in line with their access keys (events):
aAlarm = 1
aAlarmTrig = 2
aAlarmResol = 3
aPlace = 4
aMeasure = 5
aPerson = 6
aBatch = 7

# Generic Events keys
gPrev = 8
gNext = 0
gNum = 9
gMain = 10
gConf = 11
gConf2 = 12

symbols = keys[:]
symbols[gNext] = '\ue259'
symbols[aPlace] = '\ue021'
symbols[aBatch] = '\ue010'
symbols[aPerson] = '\ue008'
symbols[aMeasure] = '\ue166'
symbols[aAlarm] = '\ue123'
symbols[aAlarmTrig] = '\ue072'
symbols[aAlarmResol] = '\ue073'
symbols[gPrev] = '\ue260'
symbols[gNum] = '\ue136'
symbols[gMain] = '\ue093'
symbols[gConf] = '\ue013'
symbols[gConf2] = '\ue185'

# The events for time slices:
tHour = 1
tDay = 2
tWeek = 3
tMonth = 4
tYear = 5

fsm = Fysom({'initial': 'BranchMain',
             'events': []})


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


alarmblink = False
state = 0
chapter = 10
begScreen = 4
col2 = begScreen + 39
col3 = 89
endScreen = 131
lineHeight = 13
line2 = 12
line3 = line2 + lineHeight
line4 = line3 + lineHeight
line5 = line4 + lineHeight

try:
    while ALIVE:
        draw.rectangle((0, 0, 131, 63), fill=0)

        draw.text((4, 0), symbols[chapter], font=fontG10, fill=255)
        now = datetime.datetime.now()
        strnow = now.strftime("%Y-%m-%d %H:%M")
        #syslog.syslog(syslog.LOG_ERR, strnow)
        draw.text((15, 0), strnow,  font=font, fill=255)
        #endtext = draw.textsize(strnow, font=font)

        if state == 0:
            draw.rectangle((col3, 0, 131, 8), fill=255)
            draw.text((90, 0), "{0:.2f}".format(
                temperature)+degree+'C',  font=font, fill=0)

            endPos = showKey(aAlarm, True, alarmblink, begScreen, line2)
            draw.text((endPos+1, line2), '13', font=font, fill=255)
            endPos = showKey(aAlarmTrig, True, True, col2, line2)
            endPos = showKey(aAlarmResol, True, alarmblink, col3, line2)
            endPos = showKey(aPlace, True, True, begScreen, line3)
            draw.text((endPos+1, line3), '15', font=font, fill=255)
            endPos = showKey(aMeasure, True, True, col2, line3)
            draw.text((endPos+1, line3), '12', font=font, fill=255)
            endPos = showKey(aPerson, True, True, col3, line3)
            draw.text((endPos+1, line3), '179', font=font, fill=255)
            endPos = showKey(aBatch, True, True, begScreen, line4)
            draw.text((endPos+1, line4), '109876543210987654321',
                      font=font, fill=255)

            print(('mem='+str(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) +
                  ', 1wire='+owtemperature))
            draw.rectangle((begScreen, line5, col2-3, line5+8), fill=255)
            draw.text((begScreen, line5), owtemperature.strip() +
                      degree+'C',  font=font, fill=0)

            endPos = showKey(gNum, True, True, col2, line5)
            endPos = showKey(gConf, True, True, col3, line5)
            alarmblink = not alarmblink

        elif state == 1:
            x = 0
        elif state == 11:
            ALIVE = False
        else:
            state = 0

        # Display image.
        disp.image(image)
        try:
            disp.display()
            # print(now)
        except:
            traceback.print_exc()
        # Loop while waiting for a keypress
        digit = None
        slept = 0
        while ALIVE and (digit == None) and (slept < 1):
            digit = kp.getKey()
            slept += 0.01
            if digit != None:
                print(digit)
                chapter = digit
                if digit == 10:
                    state = 0
                elif digit == 1:
                    state = 1
                elif digit == 2:
                    state = 2
                elif digit == 3:
                    state = 3
                elif digit == 4:
                    state = 4
                elif digit == 5:
                    state = 5
                elif digit == 6:
                    state = 6
                elif digit == 7:
                    state = 7
                elif digit == 8:
                    state = 8
                elif digit == 9:
                    state = 9
                elif digit == 0:
                    state = 10
                elif digit == 11:
                    state = 11
            time.sleep(0.01)
            slept += 0.01
except:
    syslog.syslog(syslog.LOG_ERR, "MOCKUP ABORTED")
    traceback.print_exc()
    ALIVE = False
time.sleep(0.2)
PIG.stop()
