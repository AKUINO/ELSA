from Configuration import *
from LectureBarcode import *
import threading
import time

global ALIVE
ALIVE = True

c = Configuration()
c.load()

bc = BarcodeReader(c)
bc.BarcodeIn("2000002100010")
bc.BarcodeIn("3400000000012")
bc.BarcodeIn("3500000000033")
bc.BarcodeIn("3600000000047")
bc.BarcodeIn("2201607230113")
bc.BarcodeIn("2201607220114")


def BarcodeReader():
    global ALIVE
    while ALIVE:
        time.sleep(0.1)
        scan = input("Barcode   :")
        scan = str(scan)
        if (scan == "1"):
            ALIVE = False
        else:
            bc.BarcodeIn(str(scan))


threadbarcode = threading.Thread(target=BarcodeReader)
threadbarcode.start()


def StepValuesUpdate(sensorIn, data):
    currSensor = None
    for sensor in c.AllSensors.elements:
        if (c.AllSensors.elements[sensor].fields['sensor'].translate(None, '.') == sensorIn.translate(None, '.')):
            currSensor = c.AllSensors.elements[sensor]
    if(currSensor != None):
        for batch in c.AllBatches.elements:
            if (c.AllBatches.elements[batch].piece != None and c.AllBatches.elements[batch].piece.fields['p_id'] == currSensor.fields['p_id']):
                if (c.AllBatches.elements[batch].equipment != None and c.AllBatches.elements[batch].equipment.fields['e_id'] == currSensor.fields['e_id']):
                    for stepmeasure in c.AllBatches.elements[batch].currStep.stepmeasures:
                        if (c.AllBatches.elements[batch].currStep.stepmeasures[stepmeasure].fields['m_id'] == currSensor.fields['m_id']):
                            print(
                                c.AllBatches.elements[batch].fields['b_id'] + " modified...")
                            for stepvalue in c.AllBatches.elements[batch].stepValues:
                                sv = c.AllBatches.elements[batch].stepValues[stepvalue]
                                if (sv.measure == currSensor.fields['m_id']):
                                    sv.total += data
                                    sv.number += 1
                                    if data > sv.max:
                                        sv.max = data
                                    if data < sv.min:
                                        sv.min = data
