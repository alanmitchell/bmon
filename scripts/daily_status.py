#!/usr/local/bin/python2.7

import os, sys, logging, time

# change into this directory
os.chdir(os.path.dirname(sys.argv[0]))

sys.path.insert(0, '../')   # add the parent directory to the Python path

import global_vars, bmsdata

# make a logger object and set time zone so log readings are stamped with Alaska time.
# Did this because Django sets time to AK time.
os.environ['TZ'] = 'US/Alaska'
time.tzset()
logger = logging.getLogger('bms.daily_status')

# get a BMSdata object for the sensor reading database.
reading_db = bmsdata.BMSdata(global_vars.DATA_DB_FILENAME)
logger.info( '{:,} readings inserted in last day. {:,} total readings.'.format(reading_db.readingCount(time.time() - 3600*24), reading_db.readingCount()) )
reading_db.close()
