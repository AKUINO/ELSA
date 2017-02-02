import time
import datetime
import subprocess
import select
import re
import traceback
import threading
from ConfigurationELSA import AllScanners, Scanner

SCAN_SECONDS = 60

class bluetoothScanner():

    handle = None
    startScan = None
    pairing = False
    toBePaired = None
    config = None
    screen = None
    alive = True

    def rePairingDevice(self):
        if self.pairing:
            print("Already pairing...")
            return
        if self.handle:
            for aScanner in self.config.AllScanners.elements:
                if currScanner.paired:
                    currScanner.paired = False
                    self.handle.stdin.write("disconnect "+aScanner.mac+"\n")
                    currScanner = self.config.AllScanners.elements[aScanner]
                currScanner.paired = False
            self.handle.stdin.write("paired-devices\n")
            self.pairingDevice()

    def pairingDevice(self):
        if self.pairing:
            print("Already pairing...")
            return
        if self.handle:
            if not self.startScan:
                self.handle.stdin.write("scan on\n")
            self.startScan = datetime.datetime.now() + datetime.timedelta(seconds=SCAN_SECONDS);
            if self.config:
                self.pairing = True
                self.toBePaired = None
                self.pairingNextDevice()

    def pairingNextDevice(self):
        if self.handle and self.pairing and self.config:
            found = self.toBePaired is None
            for aScanner in self.config.AllScanners.elements:
                currScanner = self.config.AllScanners.elements[aScanner]
                if found:
                    self.toBePaired = None
                    if currScanner.there and not currScanner.reader and not currScanner.paired:
                        self.toBePaired = currScanner
                        self.handle.stdin.write("agent on\npair "+currScanner.mac+"\n")
                        print "Pairing "+str(currScanner)
                        break
                else:
                    found = self.toBePaired == currScanner
            self.pairing = not (self.toBePaired is None)

    def connect(self,scanner):
        if self.handle and scanner:
            print "connect "+scanner.mac
            self.handle.stdin.write("connect "+scanner.mac+"\n")
            scanner.last = datetime.datetime.now()

    def connectKey(self,KEY):
        if self.handle:
            if KEY in self.config.AllScanners.elements:
                currScanner = self.config.AllScanners.elements[KEY]
                self.connect(currScanner)

    def connectMac(self,MAC):
        if self.handle:
            KEY = self.config.AllScanners.makeKey(MAC)
            self.connectKey(KEY)

    def list(self):
        for aScanner in self.config.AllScanners.elements:
            currScanner = self.config.AllScanners.elements[aScanner]
            if currScanner.paired:
                self.screen.draw.text((4,self.screen.linePos+1), str(currScanner.rank)+u"#"+str(currScanner.id)+u": "+currScanner.mac, font=self.screen.font,fill=255)
                self.screen.linePos += self.screen.lineHeight

    def control(self):
        try:
            self.handle = subprocess.Popen(["bluetoothctl"],bufsize=0,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,close_fds=True,cwd=None)
        except:
            traceback.print_exc()
        remove_escape = re.compile(r'(\x98|\x1B\[)[0-?]*[ -\/]*[@-~]')

        begin = True
        while self.handle and self.alive:
            now = datetime.datetime.now()
            if begin:
                begin = False
                self.handle.stdin.write("power on\n")
            if self.startScan and (self.startScan < now):
                self.startScan = None
                self.handle.stdin.write("scan off\n")
                self.pairing = False
                self.toBePaired = None

            r,w,e = select.select ([self.handle.stdout], [], [], 0)
            if self.handle.stdout in r:
                lines = self.handle.stdout.readline()
                lines = remove_escape.sub('',lines)
                lines = lines.split('\r')
                for line in lines:
                    lineP = line.split(' ')
                    if len(lineP) >= 3:
                        print unicode(line)
                        pref = lineP[0]
                        if pref == "[agent]":
                            if self.toBePaired and (line.find("PIN") > 0):
                                self.handle.stdin.write(self.toBePaired.fields['PIN']+"\ntrust "+self.toBePaired.mac+"\n")
                                print "PIN="+self.toBePaired.fields['PIN']
                            self.pairingNextDevice()
                        elif lineP[1] == "Device":
                            key = self.config.AllScanners.makeKey(lineP[2])
                            status = u"unknown"
                            if key in self.config.AllScanners.elements:
                                currScanner = self.config.AllScanners.elements[key]
                                if pref == "[NEW]":
                                    currScanner.there = True
                                    status = u"there"
                                    self.connect(currScanner)
                                elif pref == "[DEL]":
                                    currScanner.there = False
                                    status = u"gone"
                                elif pref == "[CHG]":
                                    currScanner.there = True
                                    status = u"changing"
                                    if line.find("Connected: yes") >= 0:
                                        status = u"connected"
                                        self.screen.newConnect = True
                                        currScanner.paired = True
                                    else:
                                        self.connect(currScanner)
                                    # RSSI: value Connected: yes...
                                currScanner.last = now
                            print "Scanner "+str(key)+" is "+status
                        elif lineP[0] == "Device":
                            key = self.config.AllScanners.makeKey(lineP[1])
                            status = u"unknown"
                            if key in self.config.AllScanners.elements:
                                currScanner = self.config.AllScanners.elements[key]
                                currScanner.there = True
                                currScanner.last = now
                                status = "there"
                                if self.pairing:
                                    status = "paired"
                                    currScanner.paired = True
                                elif line.find("Connected: yes") >= 0:
                                    status = u"connected"
                                    self.screen.newConnect = True
                                    currScanner.paired = True
                            print "Scanner "+str(key)+" "+status+"..."
            else:
                for aScanner in self.config.AllScanners.elements:
                    currScanner = self.config.AllScanners.elements[aScanner]
                    if currScanner.there and currScanner.reader is None:
                        self.connect(currScanner)
                time.sleep(1.0)

        if self.handle:
            try:
                self.handle.kill()
            except:
                traceback.print_exc()
        self.handle = None

    def start(self):
        thread = threading.Thread(target=self.control)
        thread.start()
        return thread
