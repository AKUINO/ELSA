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
#from wiringpi2 import GPIO
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
        if (self.GPIO == None):
            self.GPIO = GPIO.pi()
        # Set all columns as output low
        for j in range(len(self.COLUMN)):
            self.GPIO.set_mode(self.COLUMN[j], GPIO.OUTPUT)
            self.GPIO.write(self.COLUMN[j], 0)

        for i in range(len(self.ROW)):
            self.GPIO.set_mode(self.ROW[i], GPIO.INPUT)
            self.GPIO.set_pull_up_down(self.ROW[i], GPIO.PUD_DOWN)
        print('Init done')

    def getKey(self):
        colVal = -1
        rowVal = -1
        # Assert each column
        for j in range(len(self.COLUMN)):
            colVal = j
            self.GPIO.write(self.COLUMN[j], 1)
            sleep(0.01)
            rowVal = -1
            for i in range(len(self.ROW)):
                # Scan rows for pushed key/button
                # A valid key press should set "rowVal"  between 0 and 3.
                tmpRead = self.GPIO.read(self.ROW[i])
                if tmpRead != 0:
                    if rowVal < 0:
                        rowVal = i
                    else:
                        rowVal = 999
            self.GPIO.write(self.COLUMN[j], 0)
            if rowVal >= 0:
                break
        # if rowVal is not 0 thru 3 then not a single button was pressed and we can exit
        if rowVal < 0 or rowVal > 3:
            return

        # Return the value of the key pressed
        return self.KEYPAD[rowVal][colVal]


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
