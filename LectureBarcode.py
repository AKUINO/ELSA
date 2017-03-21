#!/usr/bin/env python
# -*- coding: utf-8 -*-
from ConfigurationELSA import *
import datetime
import time
from bluetoothScanner import *

un_log = "1007"

un_equip = "1003"
un_piece = "1002"
un_measure = "1005"
un_phase = "1004"

un_bluescan = "1300"
un_bluelist = "1301"

allReaders = {}

class BarcodeReader():

    def __init__(self, currScanner, config):
        global allReaders
        
        self.user = ""
        self.c = config
        self.currBatch = ""
        self.scanner = currScanner
        allReaders[currScanner.rank] = self

    def BarcodeIn(self, i, screen, timestamp, bluetooth):
        screen.draw.rectangle((0,0,131,63),fill=0)
        screen.linePos = 0
        strnow = timestamp.strftime("%H:%M")
        screen.draw.text((4,screen.linePos+1), strnow, font=screen.font,fill=255)
        strid = str(i)
        screen.draw.rectangle((28,screen.linePos,30+screen.draw.textsize(strid,font=screen.font)[0],screen.linePos+10),fill=255)
        screen.draw.text((30,screen.linePos+1), strid, font=screen.font,fill=0)
        screen.linePos += screen.lineHeight

        if(i in self.c.barcode):
            if screen.i2cPresent:
                # Display image.
                screen.disp.image(screen.image)
                try:
                        screen.disp.display()
                except:
                        traceback.print_exc()

            barcodeClass = self.c.barcode[i].__class__
            if(barcodeClass == User):
                self.user = self.c.barcode[i]
                print "User logged : " + self.user.fields['name'] + "\n"
                strid = u"Utilisateur"
                screen.draw.text((4,screen.linePos+1), self.user.fields['name'], font=screen.font,fill=255)
                screen.linePos += screen.lineHeight
            if(barcodeClass == Measure and self.user != ""):
                self.user.context.measure = self.c.barcode[i]
                print "Measure scanned : " + self.user.context.measure.fields['name'] + "\n"
                strid = u"Mesure"
                if (self.currBatch != ""):
                    self.currBatch.measure = self.user.context.measure
                screen.draw.text((4,screen.linePos+1), self.user.context.measure.fields['name'], font=screen.font,fill=255)
                screen.linePos += screen.lineHeight
            if(barcodeClass == Equipment and self.user != ""):
                self.user.context.equipment = self.c.barcode[i]
                print "Equipment scanned : " + self.user.context.equipment.fields['name'] + "\n"
                strid = u"Equipement"
                screen.draw.text((4,screen.linePos+1), self.user.context.equipment.fields['name'], font=screen.font,fill=255)
                screen.linePos += screen.lineHeight
            if(barcodeClass == Piece and self.user != ""):
                self.user.context.piece = self.c.barcode[i]
                print "Piece scanned : " + self.user.context.piece.fields['name'] + "\n"
                strid = "Pièce"
                screen.draw.text((4,screen.linePos+1), self.user.context.piece.fields['name'], font=screen.font,fill=255)
                screen.linePos += screen.lineHeight
            if(barcodeClass == Phase and self.user != ""):
                self.user.context.phase = self.c.barcode[i]
                print "Phase scanned : " + self.user.context.phase.fields['name'] + "\n"
                strid = "Phase"
                screen.draw.text((4,screen.linePos+1), self.user.context.phase.fields['name'], font=screen.font,fill=255)
                screen.linePos += screen.lineHeight
            if(barcodeClass == Barcode and self.user != ""):
                print "Barcode special !"
                special = self.c.barcode[i].fields['k_id'] 
                if(special == un_log):
                    print "Delog\n"
                    self.user = ""
                    screen.draw.text((4,screen.linePos+1), u"SANS Utilisateur", font=screen.font,fill=255)
                    screen.linePos += screen.lineHeight
                elif(special == un_equip):
                    print "Equip out\n"
                    self.user.context.equipment = ""
                    screen.draw.text((4,screen.linePos+1), u"SANS Equipement", font=screen.font,fill=255)
                    screen.linePos += screen.lineHeight
                elif(special == un_piece):
                    print "Piece out\n"
                    self.user.context.piece = ""
                    screen.draw.text((4,screen.linePos+1), u"SANS Piece", font=screen.font,fill=255)
                    screen.linePos += screen.lineHeight
                elif(special == un_measure):
                    print "Measure out\n"
                    self.user.context.measure = ""
                    screen.draw.text((4,screen.linePos+1), u"SANS Mesure", font=screen.font,fill=255)
                    screen.linePos += screen.lineHeight
                elif(special == un_phase):
                    print "Phase out\n"
                    self.user.context.phase = ""
                    screen.draw.text((4,screen.linePos+1), u"SANS Phase", font=screen.font,fill=255)
                    screen.linePos += screen.lineHeight
                elif(special == un_bluescan):
                    print "Scan Bluetooth PicoNet\n"
                    screen.draw.text((4,screen.linePos+1), u"Bluetooth Pairing", font=screen.font,fill=255)
                    screen.linePos += screen.lineHeight
                    bluetooth.rePairingDevice()
                elif(special == un_bluelist):
                    print "List Bluetooth Configured Devices\n"
                    strid = "Bluetooth"
                    bluetooth.list()
                elif(int(special) < 1000):
                    if (self.user.context.measure and self.user.context.measure.fields['source'] == "scan"):
                        #print "Number : " + self.c.barcode[i].fields['k_id'] + "\n"
                        self.user.context.number = self.c.barcode[i].fields['k_id']
                        print "Number : " + self.user.context.number + "\n"
                        if self.currBatch:
                            for stepvalue in self.currBatch.stepValues:
                                stepVal = self.currBatch.stepValues[stepvalue]
                                print stepVal.measure.fields['m_id']+u"=?="+str(self.user.context.measure.fields['m_id'])
                                if stepVal.measure.fields['m_id'] == self.user.context.measure.fields['m_id']:
                                    stepVal.total = float(self.c.barcode[i].fields['k_id'])
                                    stepVal.number = 1.0
                                    screen.draw.text((4,screen.linePos+1), u"Mesure "+stepVal.measure.fields['name'], font=screen.font,fill=255)
                                    screen.linePos += screen.lineHeight
                                    screen.draw.text((4,screen.linePos+1), u" = "+str(stepVal.total), font=screen.font,fill=255)
                                    screen.linePos += screen.lineHeight
                        else:
                            screen.draw.text((4,screen.linePos+1), u"Scanner un Lot !", font=screen.font,fill=255)
                            screen.linePos += screen.lineHeight
                    else:
                        print "Wrong context\n"
                        screen.draw.text((4,screen.linePos+1), u"Mauvais Code", font=screen.font,fill=255)
                        screen.linePos += screen.lineHeight
            if(barcodeClass == Batch and self.user != ""):
                self.user.context.batch = self.c.barcode[i]
                self.currBatch = self.c.barcode[i]
                screen.draw.text((4,screen.linePos+1), u"Lot="+self.currBatch.fields['name'], font=screen.font,fill=255)
                screen.linePos += screen.lineHeight
                print self.currBatch.fields['name']
                self.currBatch.endStep()
                if self.user.context.piece != "":
                    piece = self.user.context.piece
                    piecei = self.user.context.piece.id
                else:
                    piece = ""
                    piecei = ""
                if self.user.context.equipment != "":
                    equipment = self.user.context.equipment
                    equipmenti = self.user.context.equipment.id
                else:
                    equipment = ""
                    equipmenti = ""
                if self.user.context.phase != "":
                    phase = self.user.context.phase
                    phasei = self.user.context.phase.id
                else:
                    phase = ""
                    phasei = ""
                if self.user.context.measure != "":
                    measure = self.user.context.measure
                else:
                    measure = ""
                if (self.currBatch.number == "" and self.user.context.number != ""):
                    number = self.user.context.number
                else:
                    number = ""
                posit = piecei+u"/"+equipmenti+u"/"+phasei
                print u"Searching ["+posit+u"]"
                if piece:
                    screen.draw.text((4,screen.linePos+1), u"Piece="+piece.fields['name'], font=screen.font,fill=255)
                    screen.linePos += screen.lineHeight
                if equipment:
                    screen.draw.text((4,screen.linePos+1), u"Equip="+equipment.fields['name'], font=screen.font,fill=255)
                    screen.linePos += screen.lineHeight
                if phase:
                    screen.draw.text((4,screen.linePos+1), u"Phase="+phase.fields['name'], font=screen.font,fill=255)
                    screen.linePos += screen.lineHeight
                recipeSteps = self.c.AllRecipes.elements[self.user.context.batch.fields['r_id']].AllSteps.elements
                for step in recipeSteps:
                    if (recipeSteps[step].fields['p_id'] == piecei) and (recipeSteps[step].fields['e_id'] == equipmenti) and (recipeSteps[step].fields['h_id'] == phasei) :
                        if(int(recipeSteps[step].fields['seq']) > self.currBatch.oldSeq):                            
                            self.currBatch.oldSeq = int(self.currBatch.currStep.fields['seq'])
                            self.currBatch.currStep = self.c.AllRecipes.elements[self.currBatch.fields['r_id']].AllSteps.elements[step]
                            self.currBatch.piece = piece
                            self.currBatch.equipment = equipment
                            self.currBatch.phase = phase
                            self.currBatch.measure = measure
                            self.currBatch.user = self.user
                            if(self.currBatch.oldSeq == 0):
                                self.currBatch.oldSeq = int(self.currBatch.currStep.fields['seq'])
                            print u"Found="+self.currBatch.currStep.fields['seq']
                        else:
                            print "On ne peut pas reculer dans les etapes..."
                            self.currBatch.oldSeq = int(self.currBatch.currStep.fields['seq'])
                            self.currBatch.currSeq = self.currBatch.oldSeq
                self.currBatch.beginStep()
            screen.draw.rectangle((28,0,130,10),fill=0)
            screen.draw.rectangle((28,0,32+screen.draw.textsize(strid,font=screen.font)[0],10),fill=255)
            screen.draw.text((30,1), strid, font=screen.font,fill=0)
                
        else:
            print "\bMauvais Barcode"
            screen.draw.text((4,screen.linePos+1), u"Mauvais Code", font=screen.font,fill=255)
            screen.linePos += screen.lineHeight
        # Display image.
        screen.show(str(self.scanner.rank))

