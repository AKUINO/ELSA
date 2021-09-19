#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import configparser
import socket
import traceback
import os
import codecs
import sys
from serial import Serial, PARITY_NONE, PARITY_EVEN

HARDdirectory = os.path.normpath('~/akuino/hardware')

def get_config_file_path(config_file, hostname):
    if config_file is not None:
        return os.path.normpath(config_file)
    else:
        # Test if hostname is correctly initialized
        if not hostname.startswith('akuino'):
            print((hostname+": hostname should begin with akuino"))
        return os.path.expanduser(os.path.join(HARDdirectory,
                                               hostname+'.ini'))

ModbusCurrent = -1;

class ModbusConfig():

    def __init__(self, bus = 0, bauds = 9600, device = '/dev/ttyUSB0'):
        self.bus = bus
        self.bauds = bauds
        self.device = device
        self.port = None
        
    def get_serial_port(self):
        if self.port:
            return self.port
        """ Return serial.Serial instance, ready to use for RS485."""
        self.port = Serial(port=self.device, baudrate=self.bauds, parity=PARITY_NONE,
                      stopbits=2, bytesize=8, timeout=1)
        if not self.port:
            print ("Modbus device not accessible: "+self.device)
            return None

        fh = self.port.fileno()

        # A struct with configuration for serial port: works only on some Linux...
        try:
            serial_rs485 = struct.pack('hhhhhhhh', 1, 0, 0, 0, 0, 0, 0, 0)
            fcntl.ioctl(fh, 0x542F, serial_rs485)
        except:
            print ("RS485 IOCtl not supported on this operating system.")

        return self.port

    def close_port(self):
        if self.port:
            try:
                self.port.close()
            except:
                traceback.print_exc()
            self.port = None

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
    modbus_config = {}
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
    mail_user = ''
    mail_password = ''
    mail_server = 'UNKNOWN_SMTP'
    mail_port = 587
    sms_user = ''
    sms_password = ''
    sms_server = 'UNKNOWN_SMTP'
    sms_port = 587
    sensor_polling = 60   # 60 seconds between sensors polling...

    def parse_section_system(self):
        if self.config.has_section('system'):
            if 'system' in self.config.sections():
                for anItem in self.config.items('system'):
                    if anItem[0].lower() == 'rundirectory':
                        self.rundirectory = str(anItem[1]).strip()
                        try:
                            if not os.path.exists(self.rundirectory):
                                os.makedirs(self.rundirectory)
                        except OSError:
                            print(('Impossible de creer le dossier '
                                  + self.rundirectory + '.'))
                            sys.exit()
                    elif anItem[0].lower() == 'model':
                        self.model = anItem[1]

    def parse_section_I2C(self):
        if 'I2C' in self.config.sections():
            for anItem in self.config.items('I2C'):
                if anItem[0].lower() == 'bus':
                    try:
                        self.i2c_bus = int(anItem[1])
                    except:
                        print((anItem[0] + ': ' + anItem[1] + ' is not decimal.'))

    def storeModbus(self, bus=0):
        self.modbus_config[bus]= None
        for anItem in self.config.items('modbus'+ ( str(bus) if bus else '')):
            if anItem[0].lower() == 'installed':
                self.modbus_config[bus] = anItem[1]
                if not self.modbus_config[bus]:
                    self.modbus_config[bus]= None
                elif self.modbus_config[bus].lower().startswith('no'):
                    self.modbus_config[bus] = None
                if self.modbus_config[bus]:
                    self.modbus_config[bus] = ModbusConfig(bus)

            elif anItem[0].lower() == 'bauds':
                try:
                    if self.modbus_config[bus]:
                        self.modbus_config[bus].bauds = int(anItem[1])
                except:
                    print((anItem[0] + ': ' + anItem[1] + ' is not decimal.'))

            elif anItem[0].lower() == 'device':
                if self.modbus_config[bus]:
                    self.modbus_config[bus].device = anItem[1]

    def get_serial_port(self,bus=0):
        if not bus in self.modbus_config:
            print ("Modbus #"+str(bus)+" unknown in hardware configuration.")
            return None
        if not self.modbus_config[bus]:
            print ("Modbus #"+str(bus)+" not enabled in hardware configuration.")
            return None
            
        global ModbusCurrent
        
        if ModbusCurrent != bus:
            if ModbusCurrent in self.modbus_config:
                self.modbus_config[ModbusCurrent].close_port()
            ModbusCurrent = bus
        return self.modbus_config[bus].get_serial_port()

    def close_ports(self):
        for bus in self.modbus_config:
            self.modbus_config[bus].close_port()
        global ModbusCurrent
        ModbusCurrent = -1

    def __init__(self, config_file):
        self.hostname = socket.gethostname()
        config_file = get_config_file_path(config_file, self.hostname)
        self.config = configparser.RawConfigParser()
        try:
            self.config.readfp(codecs.open(config_file, 'r', 'utf8'))
        except IOError:
            new_path = os.path.join(HARDdirectory, 'DEFAULT.ini')
            print((config_file+' not found. Using ' + new_path))
            try:
                self.config.readfp(codecs.open(os.path.expanduser(new_path),
                                               'r',
                                               'utf8'))
            except IOError:
                print("No valid hardware configuration file found. \
                       Using defaults...")
                return
    
        self.parse_section_system()
        self.parse_section_I2C()
# TODO:Finish copying sections to functions
       
        if 'SPI' in self.config.sections():
            for anItem in self.config.items('SPI'):
                if anItem[0].lower() == 'channel':
                    try:
                        self.spi_channel = int(anItem[1])
                    except:
                        print((anItem[0] + ': ' + anItem[1] + ' is not decimal.'))

        if 'PCB' in self.config.sections():
            for anItem in self.config.items('PCB'):
                if anItem[0].lower() == 'installed':
                    self.pcb = anItem[1]
                    if not self.pcb:
                        self.pcb = None
                    elif self.pcb.lower().startswith('no'):
                        self.pcb = None
                    elif self.pcb.startswith('0'):
                        self.oled_reset = 5
                        self.pcb = '0'
                    elif self.pcb.startswith('1'):
                        self.oled_reset = 25
                        self.pcb = '1'
                    else:
                        self.oled_reset = None

        if 'ELA' in self.config.sections():
            for anItem in self.config.items('ELA'):
                if anItem[0].lower() == 'installed':
                    self.ela = anItem[1]
                    if not self.ela:
                        self.ela = None
                    elif self.ela.lower().startswith('no'):
                        self.ela = None

                elif anItem[0].lower() == 'bauds':
                    try:
                        self.ela_bauds = int(anItem[1])
                    except:
                        print((anItem[0] + ': ' + anItem[1] + ' is not decimal.'))

                elif anItem[0].lower() == 'reset':
                    self.ela_reset = anItem[1]

        if 'modbus' in self.config.sections():
            self.storeModbus(0)
        for i in range(1,9):
            if 'modbus'+str(i) in self.config.sections():
                self.storeModbus(i)

        if 'bluetooth' in self.config.sections():
            for anItem in self.config.items('bluetooth'):
                if anItem[0].lower() == 'installed':
                    self.bluetooth = anItem[1]
                    if not self.bluetooth:
                        self.bluetooth = None
                    elif self.bluetooth.lower().startswith('no'):
                        self.bluetooth = None

        if 'wifi' in self.config.sections():
            for anItem in self.config.items('wifi'):
                if anItem[0].lower() == 'installed':
                    self.wifi = anItem[1]
                    if not self.wifi:
                        self.wifi = None
                    elif self.wifi.lower().startswith('no'):
                        self.wifi = None

        if 'owfs' in self.config.sections():
            for anItem in self.config.items('owfs'):
                if anItem[0].lower() == 'installed':
                    self.owfs = anItem[1]
                    if not self.owfs:
                        self.owfs = None
                    elif self.owfs.lower().startswith('no'):
                        self.owfs = None

        if 'sensors' in self.config.sections():
            for anItem in self.config.items('sensors'):
                if anItem[0].lower() == 'polling':
                    try:
                        self.sensor_polling = int(anItem[1])
                    except:
                        print((anItem[0] + ': ' + anItem[1] + ' is not decimal.'))

        if 'OLED' in self.config.sections():
            for anItem in self.config.items('OLED'):
                if anItem[0].lower() == 'installed':
                    self.oled = anItem[1]
                    if not self.oled:
                        self.oled = None
                    elif self.oled.lower().startswith('no'):
                        self.oled = None

                elif anItem[0].lower() == 'i2c':
                    try:
                        self.oled_address = int(anItem[1], 16)
                    except:
                        print((anItem[0] + '='
                                        + anItem[1]
                                        + ' is not in hexadecimal'))

                elif anItem[0].lower() == 'spi':
                    try:
                        self.oled_channel = int(anItem[1])
                    except:
                        print((anItem[0] + ': ' + anItem[1] + ' is not decimal.'))

                elif anItem[0].lower() == 'reset':
                    try:
                        self.oled_reset = int(anItem[1])
                    except:
                        print((anItem[0] + ': ' + anItem[1] + ' is not decimal.'))

        if 'battery' in self.config.sections():
            for anItem in self.config.items('battery'):
                if anItem[0].lower() == 'installed':
                    self.battery = anItem[1]
                    if not self.battery \
                            or self.battery.lower().startswith('no'):
                        self.battery = None
                    elif self.battery.lower().startswith('spi'):
                        self.battery = 'SPI'
                    else:  # Anything else than SPI is I2C !
                        self.battery = 'I2C'

                elif anItem[0].lower() == 'shutdown':
                    a_command = anItem[1]
                    if a_command and (a_command.lower() != 'no'):
                        self.battery_shutdown = a_command

                elif anItem[0].lower() == 'breakout_volt':
                    try:
                        self.battery_breakout_volt = float(anItem[1])
                    except:
                        print((anItem[0]+': '+anItem[1]+' is not decimal.'))

                elif anItem[0].lower() == 'i2c':
                    try:
                        self.battery_address = int(anItem[1], 16)
                    except ValueError:
                        print((anItem[0] + '='
                                        + anItem[1]
                                        + ' is not in hexadecimal'))
                        raise
                elif anItem[0].lower() == 'spi':
                    try:
                        self.battery_channel = int(anItem[1])
                    except:
                        print((anItem[0]+': '+anItem[1]+' is not decimal.'))

                elif anItem[0].lower() == 'port':
                    try:
                        self.battery_port = int(anItem[1])
                    except:
                        print((anItem[0]+': '+anItem[1]+' is not decimal.'))

                elif anItem[0].lower() == 'rv':
                    try:
                        self.battery_rv = int(anItem[1])
                    except:
                        print((anItem[0]+': '+anItem[1]+' is not decimal.'))

                elif anItem[0].lower() == 'rg':
                    try:
                        self.battery_rg = int(anItem[1])
                    except:
                        print((anItem[0]+': '+anItem[1]+' is not decimal.'))

        if self.battery:
            self.battery_divider = (float(self.battery_rv)
                                    + float(self.battery_rg))/float(self.battery_rg)
            print(("Battery voltage divider="+str(self.battery_divider)))

        if 'shutdown' in self.config.sections():
            for anItem in self.config.items('shutdown'):
                if anItem[0].lower() == 'installed':
                    self.shutdown = anItem[1]
                    if not self.shutdown:
                        self.shutdown = None
                    elif self.shutdown.lower().startswith('no'):
                        self.shutdown = None
                    else:
                        try:
                            self.shutdown = int(self.shutdown)
                        except:
                            print((anItem[0] + ': ' + anItem[1] + ' is not decimal.'))

        if 'running' in self.config.sections():
            for anItem in self.config.items('running'):
                if anItem[0].lower() == 'installed':
                    self.running = anItem[1]
                    if not self.running:
                        self.running = None
                    elif self.running.lower().startswith('no'):
                        self.running = None
                    else:
                        try:
                            self.running = int(self.running)
                        except:
                            print((anItem[0] + ': ' + anItem[1] + ' is not decimal.'))

        if 'mail' in self.config.sections():
            for anItem in self.config.items('mail'):
                if anItem[0].lower() == 'user':
                    self.mail_user = anItem[1]
                elif anItem[0].lower() == 'password':
                    self.mail_password = anItem[1]
                elif anItem[0].lower() == 'server':
                    self.mail_server = anItem[1]
                elif anItem[0].lower() == 'port':
                    self.mail_port = anItem[1]
                    if not self.mail_port:
                        self.mail_port = 587
                    else:
                        try:
                            self.mail_port = int(self.mail_port)
                        except:
                            print((anItem[0] + ': ' + anItem[1] + ' is not decimal.'))

        if 'sms' in self.config.sections():
            for anItem in self.config.items('sms'):
                if anItem[0].lower() == 'user':
                    self.sms_user = anItem[1]
                elif anItem[0].lower() == 'password':
                    self.sms_password = anItem[1]
                elif anItem[0].lower() == 'server':
                    self.sms_server = anItem[1]
                elif anItem[0].lower() == 'port':
                    self.sms_port = anItem[1]

        if 'keypad' in self.config.sections():
            for anItem in self.config.items('keypad'):
                if anItem[0].lower() == 'installed':
                    self.keypad = anItem[1]
                    if not self.keypad:
                        self.keypad = None
                    elif self.keypad.lower().startswith('no'):
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
                        try:
                            self.keypad_r[x] = int(anItem[1])
                        except:
                            print((anItem[0] + ': ' + anItem[1] + ' is not decimal.'))
                    except:
                        pass
                elif anItem[0][0].lower == 'c':
                    try:
                        x = int(anItem[0][1])
                        try:
                            self.keypad_c[x] = int(anItem[1])
                        except:
                            print((anItem[0] + ': ' + anItem[1] + ' is not decimal.'))
                    except:
                        pass
        
        for section_string in (j for j in self.config.sections() if '.' in j):
            name = section_string.split('.')[1]
            section = self.config.items(section_string)
            if section_string.startswith('device'):
                self.devices[name] = self.parse_one_subsection(section,
                                                               name,
                                                               'device')
            elif section_string.startswith('input'):
                self.inputs[name] = self.parse_one_subsection(section,
                                                              name,
                                                              'input')
            elif section_string.startswith('output'):
                self.outputs[name] = self.parse_one_subsection(section,
                                                               name,
                                                               'output')

    def parse_one_subsection(self, section, name, type):
        output = {}
        REQUIRED_ITEMS = {}
        REQUIRED_ITEMS['device'] = ['install']
        REQUIRED_ITEMS['input'] = []
        REQUIRED_ITEMS['output'] = ['device']
        VALID_ITEMS = {}
        VALID_ITEMS['device'] = REQUIRED_ITEMS['device'] + ['amplification',
                                                            'i2c']
        VALID_ITEMS['input'] = REQUIRED_ITEMS['input'] + ['device',
                                                          'channel',
                                                          'resolution',
                                                          'poweroutput',
                                                          'delayms',
                                                          'serialport',
                                                          'sdiaddress']
        VALID_ITEMS['output'] = REQUIRED_ITEMS['output'] + ['channel', 'invert']
        
        for i in section:
            if i[0] in VALID_ITEMS[type]:
                output[i[0]] = i[1]
            else:
                raise ValueError('Unknown configuration item "' + i[0]
                                                                + '" for '
                                                                + type
                                                                + ' "'
                                                                + name
                                                                + '"')
        for i in REQUIRED_ITEMS[type]:
            if i not in output:
                raise KeyError('Missing configuration item "' + i
                                                              + '" for '
                                                              + type
                                                              + ' "'
                                                              + name
                                                              + '"')
        return output
