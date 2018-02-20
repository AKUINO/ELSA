# #####################################################
# Python Library for 3x4 matrix keypad using
# 7 of the avialable GPIO pins on the Raspberry Pi.
#
# This could easily be expanded to handle a 4x4 but I
# don't have one for testing. The KEYPAD constant
# would need to be updated. Also the setting/checking
# of the colVal part would need to be expanded to
# handle the extra column.
#
# Written by Chris Crumpacker
# May 2013
#
# main structure is adapted from Bandono's
# matrixQPI which is wiringPi based.
# https://github.com/bandono/matrixQPi?source=cc
# #####################################################

#import RPi.GPIO as GPIO
import pigpio as GPIO
from time import sleep


class keypad():
    # CONSTANTS
    KEYPAD = [
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 9],
        [10, 0, 11]
    ]

    ROW = [18, 23, 24, 25]
    COLUMN = [4, 17, 22]

    def __init__(self, gpio=None):
        self.GPIO = gpio
        if self.GPIO == None:
            self.GPIO = GPIO.pi()
        # GPIO.setmode(GPIO.BCM)
        # pigpio is always BCM numbering...

    def getKey(self):

        # Set all columns as output low
        for j in range(len(self.COLUMN)):
            #GPIO.setup(self.COLUMN[j], GPIO.OUT)
            self.GPIO.set_mode(self.COLUMN[j], GPIO.OUTPUT)
            #GPIO.output(self.COLUMN[j], GPIO.LOW)
            self.GPIO.write(self.COLUMN[j], 0)

        # Set all rows as input
        for i in range(len(self.ROW)):
            #GPIO.setup(self.ROW[i], GPIO.IN, pull_up_down=GPIO.PUD_UP)
            self.GPIO.set_mode(self.ROW[i], GPIO.INPUT)
            self.GPIO.set_pull_up_down(self.ROW[i], GPIO.PUD_UP)
        sleep(0.01)
        # Scan rows for pushed key/button
        # A valid key press should set "rowVal"  between 0 and 3.
        rowVal = -1
        for i in range(len(self.ROW)):
            #tmpRead = GPIO.input(self.ROW[i])
            tmpRead = self.GPIO.read(self.ROW[i])
            if tmpRead == 0:
                if rowVal < 0:
                    rowVal = i
                else:
                    rowVal = 999

        # if rowVal is not 0 thru 3 then not a single button was pressed and we can exit
        if rowVal < 0 or rowVal > 3:
            self.exit()
            return
        sleep(0.01)
        # Convert columns to input
        for j in range(len(self.COLUMN)):
                #GPIO.setup(self.COLUMN[j], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            self.GPIO.set_mode(self.COLUMN[j], GPIO.INPUT)
            self.GPIO.set_pull_up_down(self.COLUMN[j], GPIO.PUD_DOWN)

        # Switch the i-th row found from scan to output
        #GPIO.setup(self.ROW[rowVal], GPIO.OUT)
        self.GPIO.set_mode(self.ROW[rowVal], GPIO.OUTPUT)
        #GPIO.output(self.ROW[rowVal], GPIO.HIGH)
        self.GPIO.write(self.ROW[rowVal], 1)
        sleep(0.01)

        # Scan columns for still-pushed key/button
        # A valid key press should set "colVal"  between 0 and 2.
        colVal = -1
        for j in range(len(self.COLUMN)):
            #tmpRead = GPIO.input(self.COLUMN[j])
            tmpRead = self.GPIO.read(self.COLUMN[j])
            if tmpRead == 1:
                if colVal < 0:
                    colVal = j
                else:
                    colVal = 999

        # if colVal is not 0 thru 2 then not a single button was pressed and we can exit
        if colVal < 0 or colVal > 2:
            self.exit()
            return

        # Return the value of the key pressed
        self.exit()
        return self.KEYPAD[rowVal][colVal]

    def exit(self):
        # Reinitialize all rows and columns as input at exit
        for i in range(len(self.ROW)):
                #GPIO.setup(self.ROW[i], GPIO.IN, pull_up_down=GPIO.PUD_UP)
            self.GPIO.set_mode(self.ROW[i], GPIO.INPUT)
            self.GPIO.set_pull_up_down(self.ROW[i], GPIO.PUD_UP)
        for j in range(len(self.COLUMN)):
            #GPIO.setup(self.COLUMN[j], GPIO.IN, pull_up_down=GPIO.PUD_UP)
            self.GPIO.set_mode(self.COLUMN[j], GPIO.INPUT)
            self.GPIO.set_pull_up_down(self.COLUMN[j], GPIO.PUD_UP)


if __name__ == '__main__':
    # Initialize the keypad class
    kp = keypad()

    # Loop while waiting for a keypress
    digit = None
    while True:
        digit = kp.getKey()
        if digit != None:
            print digit
            sleep(0.25)
        sleep(0.05)
