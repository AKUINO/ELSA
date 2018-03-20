import rrdtool
import os
import ConfigurationELSA as elsa
import calendar

def get_datapoints_from_s_id(sensorID, time_from_utc, time_to_utc):
    if time_from_utc is None:
        raise ValueError("time_from_utc has to be set")
    if time_to_utc is None:
        time_to_utc = datetime.datetime.utcnow()

    path = os.path.join(elsa.DIR_RRD, 's_' + sensorID + '.rrd')
    time_from = calendar.timegm(time_from_utc)
    time_to = calendar.timegm(time_to_utc)
    
    result = rrdtool.fetch(str(path), 'AVERAGE', '--start=' + str(time_from), '--end=' + str(time_to))
    
    
    datapoints = []
    rrd_step = result[0][2]
    for i in range(0, len(result[2])):
        datapoints.append([result[2][i][0], (time_from + i*rrd_step)*1000])
    

    return datapoints
