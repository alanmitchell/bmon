#!/usr/local/bin/python2.7

import os, sys, logging, time

# change into this directory
os.chdir(os.path.dirname( os.path.abspath(sys.argv[0]) ))

sys.path.insert(0, '../../')   # add the parent/parent directory to the Python path
sys.path.insert(0, '../')   # add the parent directory to the Python path
import global_vars          # needed to set up logging
import bmsdata

# make a logger object and set time zone so log readings are stamped with Alaska time.
# Did this because Django sets time to AK time.
os.environ['TZ'] = 'US/Alaska'
try:
    time.tzset()
except:
    # the above command is not supported in Windows.
    # Need to come up with another solution if running on Windows
    # is necessary
    pass

logger = logging.getLogger('bms.daily_status')

# get a BMSdata object for the sensor reading database.
reading_db = bmsdata.BMSdata()
logger.info( '{:,} readings inserted in last day. {:,} total readings.'.format(reading_db.readingCount(time.time() - 3600*24), reading_db.readingCount()) )
reading_db.close()
