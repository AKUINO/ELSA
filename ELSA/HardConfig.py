# -*- coding: utf-8 -*-
import ConfigParser
import socket
import traceback
import os
import codecs
import sys

HARDdirectory = os.path.normpath('~/akuino/hardware')

def get_config_file_path(config_file, hostname):
    if config_file is not None:
        return os.path.normpath(config_file)
    else:
        # Test if hostname is correctly initialized
        if not hostname.startswith(u'akuino'):
            print(hostname+": hostname should begin with akuino")
        return os.path.expanduser(os.path.join(HARDdirectory,
                                               hostname+'.ini'))

class HardConfig():
    config = None
    idDefinitions = {}
    hostname = "UNKNOWN"
    RUNdirectory = "/run/akuino"
    model = '3'
    i2c_bus = 1
    spi_channel = 0
    pcb = None
    ela = None
    ela_bauds = 9600
    ela_reset = '[9C5E01]'
    bluetooth = None
    wifi = None
    owfs = None
    oled = None
    oled_address = 0x3C
    oled_channel = 1
    oled_reset = None
    battery = None
    battery_breakout_volt = 10.0
    battery_address = 0x69
    battery_channel = 0
    battery_port = 1
    battery_RV = 45000
    battery_RG = 5000
    battery_divider = 10.0
    battery_shutdown = 'sudo shutdown now "Batterie faible !"'
    shutdown = None
    running = None
    keypad = None
    keypad_r = [0, 0, 0, 0]
    keypad_c = [0, 0, 0, 0]
    devices = {}
    inputs = {}
    outputs = {}

    def parse_section_system(self):
        if self.config.has_section('system'):
            if u'system' in self.config.sections():
                for anItem in self.config.items(u'system'):
                    if anItem[0].lower() == u'rundirectory':
                        self.rundirectory = unicode(anItem[1]).strip()
                        try:
                            if not os.path.exists(self.rundirectory):
                                os.makedirs(self.rundirectory)
                        except OSError:
                            print('Impossible de creer le dossier ' + self.rundirectory + '.')
                            sys.exit()
                    elif anItem[0].lower() == u'model':
                        self.model = anItem[1]

    def parse_section_I2C(self):
        if u'I2C' in self.config.sections():
            for anItem in self.config.items(u'I2C'):
                if anItem[0].lower() == u'bus':
                    self.i2c_bus = int(anItem[1])

    def __init__(self, config_file):
        self.hostname = socket.gethostname()
        config_file = get_config_file_path(config_file, self.hostname)
        self.config = ConfigParser.RawConfigParser()
        try:
            self.config.readfp(codecs.open(config_file, 'r', 'utf8'))
        except IOError:
            new_path = os.path.join(HARDdirectory, 'DEFAULT.ini')
            print(config_file+' not found. Using ' + new_path)
            try:
                self.config.readfp(codecs.open(os.path.expanduser(new_path), 'r', 'utf8'))
            except IOError:
                print("No valid configuration hardware configuration file found. Exiting")
                sys.exit()
    
        self.parse_section_system()
        self.parse_section_I2C()
# TODO:Finish copying sections to functions
       
        if True: 
            if u'SPI' in self.config.sections():
                for anItem in self.config.items(u'SPI'):
                    if anItem[0].lower() == u'channel':
                        self.spi_channel = int(anItem[1])

            if u'PCB' in self.config.sections():
                for anItem in self.config.items(u'PCB'):
                    if anItem[0].lower() == u'installed':
                        self.pcb = anItem[1]
                        if not self.pcb:
                            self.pcb = None
                        elif self.pcb.lower().startswith(u'no'):
                            self.pcb = None
                        elif self.pcb.startswith(u'0'):
                            self.oled_reset = 5
                            self.pcb = '0'
                        elif self.pcb.startswith(u'1'):
                            self.oled_reset = 25
                            self.pcb = '1'
                        else:
                            self.oled_reset = None

            if u'ELA' in self.config.sections():
                for anItem in self.config.items(u'ELA'):
                    if anItem[0].lower() == u'installed':
                        self.ela = anItem[1]
                        if not self.ela:
                            self.ela = None
                        elif self.ela.lower().startswith(u'no'):
                            self.ela = None

                    elif anItem[0].lower() == u'bauds':
                        self.ela_bauds = int(anItem[1])

                    elif anItem[0].lower() == u'reset':
                        self.ela_reset = anItem[1]

            if u'bluetooth' in self.config.sections():
                for anItem in self.config.items(u'bluetooth'):
                    if anItem[0].lower() == u'installed':
                        self.bluetooth = anItem[1]
                        if not self.bluetooth:
                            self.bluetooth = None
                        elif self.bluetooth.lower().startswith(u'no'):
                            self.bluetooth = None

            if u'wifi' in self.config.sections():
                for anItem in self.config.items(u'wifi'):
                    if anItem[0].lower() == u'installed':
                        self.wifi = anItem[1]
                        if not self.wifi:
                            self.wifi = None
                        elif self.wifi.lower().startswith(u'no'):
                            self.wifi = None

            if u'owfs' in self.config.sections():
                for anItem in self.config.items(u'owfs'):
                    if anItem[0].lower() == u'installed':
                        self.owfs = anItem[1]
                        if not self.owfs:
                            self.owfs = None
                        elif self.owfs.lower().startswith(u'no'):
                            self.owfs = None

            if u'OLED' in self.config.sections():
                for anItem in self.config.items(u'OLED'):
                    if anItem[0].lower() == u'installed':
                        self.oled = anItem[1]
                        if not self.oled:
                            self.oled = None
                        elif self.oled.lower().startswith(u'no'):
                            self.oled = None

                    elif anItem[0].lower() == u'i2c':
                        try:
                            self.oled_address = int(anItem[1], 16)
                        except:
                            print(anItem[0]+'='+anItem[1] +
                                  ' is not in hexadecimal')

                    elif anItem[0].lower() == u'spi':
                        self.oled_channel = int(anItem[1])

                    elif anItem[0].lower() == u'reset':
                        self.oled_reset = int(anItem[1])

            if u'battery' in self.config.sections():
                for anItem in self.config.items(u'battery'):
                    if anItem[0].lower() == u'installed':
                        self.battery = anItem[1]
                        if not self.battery:
                            self.battery = None
                        elif self.battery.lower().startswith(u'no'):
                            self.battery = None
                        elif self.battery.lower().startswith(u'spi'):
                            self.battery = 'SPI'
                        else:  # Anything else than SPI is I2C !
                            self.battery = 'I2C'

                    elif anItem[0].lower() == u'shutdown':
                        a_command = anItem[1]
                        if a_command and (a_command.lower() != u'no'):
                            self.battery_shutdown = a_command

                    elif anItem[0].lower() == u'breakout_volt':
                        self.battery_breakout_volt = float(anItem[1])

                    elif anItem[0].lower() == u'i2c':
                        try:
                            self.battery_address = int(anItem[1], 16)
                        except:
                            print(anItem[0]+'='+anItem[1] +
                                  ' is not in hexadecimal')
                    elif anItem[0].lower() == u'spi':
                        self.battery_channel = int(anItem[1])

                    elif anItem[0].lower() == u'port':
                        self.battery_port = int(anItem[1])

                    elif anItem[0].lower() == u'rv':
                        self.battery_rv = int(anItem[1])

                    elif anItem[0].lower() == u'rg':
                        self.battery_rg = int(anItem[1])
            if self.battery:
                self.battery_divider = (
                    float(self.battery_rv)+float(self.battery_rg))/float(self.battery_rg)
                print("Battery voltage divider="+str(self.battery_divider))

            if u'shutdown' in self.config.sections():
                for anItem in self.config.items(u'shutdown'):
                    if anItem[0].lower() == u'installed':
                        self.shutdown = anItem[1]
                        if not self.shutdown:
                            self.shutdown = None
                        elif self.shutdown.lower().startswith(u'no'):
                            self.shutdown = None
                        else:
                            self.shutdown = int(self.shutdown)

            if u'running' in self.config.sections():
                for anItem in self.config.items(u'running'):
                    if anItem[0].lower() == u'installed':
                        self.running = anItem[1]
                        if not self.running:
                            self.running = None
                        elif self.running.lower().startswith(u'no'):
                            self.running = None
                        else:
                            self.running = int(self.running)

            if u'keypad' in self.config.sections():
                for anItem in self.config.items(u'keypad'):
                    if anItem[0].lower() == u'installed':
                        self.keypad = anItem[1]
                        if not self.keypad:
                            self.keypad = None
                        elif self.keypad.lower().startswith(u'no'):
                            self.keypad = None
                        elif self.pcb == '0':
                            self.keypad_r = [18, 23, 24, 25]
                            self.keypad_c = [4, 17, 22, 0]
                        elif self.pcb == '1':
                            self.keypad_r = [26, 12, 20, 21]
                            self.keypad_r = [5, 6, 13, 19]
                    elif anItem[0][0].lower == 'r':
                        try:
                            x = int(anItem[0][1])
                            self.keypad_r[x] = int(anItem[1])
                        except:
                            pass
                    elif anItem[0][0].lower == 'c':
                        try:
                            x = int(anItem[0][1])
                            self.keypad_c[x] = int(anItem[1])
                        except:
                            pass
            
# TODO: Add verfication for configuration options (if an input mentions a device, it should exitst, etc.)
            for section in (j for j in self.config.sections() if '.' in j):
                name = section.split('.')[1]
                if section.startswith('device'):
                    self.devices[name] = dict(self.config.items(section))
                elif section.startswith('input'):
                    self.inputs[name] = dict(self.config.items(section))
                elif section.startswith('output'):
                    self.outputs[name] = dict(self.config.items(section))
                    

        else:
            print('Unable to load configuration. Exiting.')
            sys.exit()
