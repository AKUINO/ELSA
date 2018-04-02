import smbus
import time
from ABE_ADCPi import ADCPi


device_address = 0x69

adc = ADCPi(device_address, 12)

if __name__ == "__main__":
    print (adc.read_voltage(1))
