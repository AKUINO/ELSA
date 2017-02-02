#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import datetime
import time
import SSD1306
import threading


class I2CScreen:    
    disp = None
    draw = None
    font = None
    begScreen = 4
    endScreen = 131
    lineHeight = 13
    newConnect = False
    i2cPresent = True
    refreshDisplay = datetime.datetime.now()
    degree = u'\N{DEGREE SIGN}'
    devConnected = ""
    linePos = 0

    def __init__(self, i2cPresent = True, **kwds):
        self.__dict__.update(kwds)
        self.lock = threading.Lock() #Synchronize screen accesses

        if self.i2cPresent:
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

    def show(self,message):
        if message:
            lgText = self.draw.textsize(message,font=self.font)[0]
            self.draw.rectangle((130-lgText,0,132,10),fill=255)
            self.draw.text((132-lgText,0), message, font=self.font,fill=0)

        if self.i2cPresent:
            # Display image.
            self.disp.image(self.image)
            try:
                    self.disp.display()
            except:
                    traceback.print_exc()
