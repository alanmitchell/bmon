#!/usr/local/bin/python2.7

import os, sys, sqlite3, logging, time

# change into this directory
os.chdir(os.path.dirname(sys.argv[0]))

sys.path.insert(0, '../')   # add the parent directory to the Python path

import global_vars, bmsdata, calculated_readings

# make a logger object and set time zone so log readings are stamped with Alaska time.
# Did this because Django sets time to AK time.
os.environ['TZ'] = 'US/Alaska'
time.tzset()
logger = logging.getLogger('bms.calc_readings')

# get a BMSdata object for the sensor reading database and then make a Calculate
# Readings object.  Only allow calculated readings within the last eight hours (480 minutes).
reading_db = bmsdata.BMSdata(global_vars.DATA_DB_FILENAME)
calc = calculated_readings.CalculateReadings(reading_db, 480)

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