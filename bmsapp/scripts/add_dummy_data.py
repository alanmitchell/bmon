'''Adds dummy data to the reading database
'''

import bmsapp.readingdb.bmsdata
import random
import time

BLDG_COUNT = 8
SENSOR_COUNT = 20
YRS_OF_READINGS = 1.5
READING_SPACING = 10.0    # minutes

# create the timestamp array and the value array (random)
tstart = int(time.time() - YRS_OF_READINGS * 8766 * 3600)
tstamps = range(tstart, int(time.time()), int(READING_SPACING * 60))
vals = [random.random() for i in range(len(tstamps))]

def run():

    db = bmsapp.readingdb.bmsdata()

    for b in range(BLDG_COUNT):
        for s in range(SENSOR_COUNT):

            sensor_id = '%03d_%03d' % (b, s)
            ids = [sensor_id] * len(tstamps)
            db.insert_reading(tstamps, ids, vals)

    db.close()
