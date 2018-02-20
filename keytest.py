import time
from keypadClass3 import keypad

# Initialize the keypad class
kp = keypad()

digit = None
while digit != 11:
    # Loop while waiting for a keypress
    slept = 0
    digit = None
    while (digit != 11) and (digit == None) and (slept < 1):
        digit = kp.getKey()
        if digit != None:
            print(digit)
        time.sleep(0.01)
        slept += 0.01
