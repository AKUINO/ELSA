#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import datetime
import time
import threading
import traceback


class I2CScreen:    
    disp = None
    draw = None
    font = None
    begScreen = 4
    endScreen = 131
    lineHeight = 10
    newConnect = False
    i2cPresent = True
    refreshDisplay = datetime.datetime.now()
    degree = u'\N{DEGREE SIGN}'
    devConnected = ""
    linePos = 0

    def __init__(self, i2cPresent = True, **kwds):
        self.__dict__.update(kwds)
        self.lock = threading.Lock() #Synchronize screen accesses

        if self.i2cPresent is True:
            # Initialize library.
            self.disp.begin()
            # Clear display.
            self.disp.clear()
            # Create blank image for drawing.
            # Make sure to create image with mode '1' for 1-bit color.
            self.width = self.disp.width
            self.height = self.disp.height
        else:
            self.width = 128
            self.height = 64
        self.image = Image.new(u'1', (self.width, self.height))

        # Get drawing object to draw on image.
        self.draw = ImageDraw.Draw(self.image)

        # Default font = better than 
        #font = ImageFont.load_default()

        # Alternatively load a TTF font.  Make sure the .ttf font file is in the same directory as the python script!
        # Some other nice fonts to try: http://www.dafont.com/bitmap.php
        self.font = ImageFont.truetype('sans.ttf', 9)
        self.fontG8 = ImageFont.truetype('glyphicons-halflings-regular.ttf', 8)
        self.fontG10 = ImageFont.truetype('glyphicons-halflings-regular.ttf', 10)

    def clear(self):
        if self.i2cPresent is True:
            self.draw.rectangle((self.begScreen,0,self.begScreen+self.width-1,self.height),fill=0)
        self.linePos = 0

    def end_line(self):
        if self.i2cPresent is True:
            # Display image.
            self.disp.image(self.image)
            try:
                    self.disp.display()
            except:
                    traceback.print_exc()
            time.sleep(0.1)
        self.linePos += self.lineHeight
        if (self.linePos + self.lineHeight) > self.height:
            self.linePos = 0
        self.draw.rectangle((self.begScreen,self.linePos,self.begScreen+self.width-1,self.linePos+self.lineHeight-1),fill=0)

    def show(self,pos,message):
        if message and (self.i2cPresent is True):
            lgText = self.draw.textsize(message,font=self.font)[0]
            if pos < 0:
                pos = self.endScreen - lgText - 1
            self.draw.text((pos,self.linePos), message, font=self.font,fill=255)
            return pos+lgText+2
        else:
            return pos

    def showBW(self,pos,message):
        if message and (self.i2cPresent is True):
            lgText = self.draw.textsize(message,font=self.font)[0]
            if pos < 0:
                pos = self.endScreen - lgText - 1
            self.draw.rectangle((pos-2,self.linePos, pos+lgText-1,self.linePos+self.lineHeight-2),fill=255)
            self.draw.text((pos,self.linePos), message, font=self.font,fill=0)
            return pos+lgText+2
        else:
            return pos

