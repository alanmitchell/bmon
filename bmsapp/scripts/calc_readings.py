#!/usr/local/bin/python2.7

import os, sys, sqlite3, logging, time

# change into this directory
os.chdir(os.path.dirname( os.path.abspath(sys.argv[0]) ))

sys.path.insert(0, '../')   # add the parent directory to the Python path

import global_vars
from readingdb import bmsdata
from calcs import calcreadings, calcfuncs01

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

logger = logging.getLogger('bms.calc_readings')

# get a BMSdata object for the sensor reading database and then make a Calculate
# Readings object.  Other calculated reading classes in addition to CalcReadingFuncs_01
# can be added to the list and they will be search for matching function names.
# Only allow calculated readings within the last eight hours (480 minutes).
reading_db = bmsdata.BMSdata(global_vars.DATA_DB_FILENAME)
calc = calcreadings.CalculateReadings([calcfuncs01.CalcReadingFuncs_01, ], reading_db, 480)

# get a database connection and cursor to the Django project database that has the sensor
# list.
conn = sqlite3.connect(global_vars.PROJ_DB_FILENAME)
cursor = conn.cursor()

# get all the calculated readings in calculation order
cursor.execute('SELECT sensor_id, tran_calc_function, function_parameters FROM bmsapp_sensor WHERE is_calculated = 1 ORDER BY calculation_order')

for row in cursor.fetchall():
    try:
        rec_count = calc.processCalc(row[0], row[1], row[2])
        logger.debug( '%s %s readings calculated and inserted' % (rec_count, row[0]) )
    except:
        logger.exception('Error calculating %s readings' % row[0])

reading_db.close()