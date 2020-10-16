#!/usr/bin/env python3
#Local
import ConfigurationELSA as elsa

#Libraries
import calendar
import os
import rrdtool
from numpy import nan
import datetime

def get_datapoints_from_s_id(sensorID, time_from_utc, time_to_utc):
    if time_from_utc is None:
        raise ValueError("time_from_utc has to be set")
    if time_to_utc is None:
        time_to_utc = datetime.datetime.utcnow()

    path = os.path.join(elsa.DIR_RRD, 's_' + sensorID + '.rrd')
    time_from = calendar.timegm(time_from_utc)
    time_to = calendar.timegm(time_to_utc)
    
    result = rrdtool.fetch(str(path), 'AVERAGE', '--start=' + str(time_from), '--end=' + str(time_to))
    values = result[2]
    
    datapoints = []
    rrd_step = result[0][2]
    for i in range(0, len(values)):
        val = values[i][0]
        if val is not None and val != nan:
            datapoints.append([val, (time_from + i*rrd_step)*1000])

    return datapoints
