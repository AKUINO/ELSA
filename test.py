import SSD1306
import time
import sys
import socket
import fcntl
import struct
from time import sleep
 
# This function allows us to grab any of our IP addresses
def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])
 
# Sets our variables to be used later
RESET_PIN = 15
DC_PIN    = 16
TEXT = ''
 
led = SSD1306.SSD1306_128_64(rst=RESET_PIN)
led.begin()
led.clear_display()
 
# This sets TEXT equal to whatever your IP address is, or isn't
try:
    TEXT = get_ip_address('wlan0') # WiFi address of WiFi adapter. NOT ETHERNET
except IOError:
    try:
        TEXT = get_ip_address('eth0') # WiFi address of Ethernet cable. NOT ADAPTER
    except IOError:
        TEXT = ('NO INTERNET!')
 
# The actual printing of TEXT
led.clear_display()
intro = 'Hello!'
ip = 'Your IP Address is:'
led.draw_text2(0,25,TEXT,1)
led.draw_text2(0,0,intro,2)
led.draw_text2(0,16, ip, 1)
led.display()