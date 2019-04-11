'''Determines and inserts the calculated sensor values into the sensor
reading database.  This script is usually run via a cron job every half 
hour.

This script is set up to run through use of the django-extensions runscript
feature, in order that the script has easy access to the Django model data
for this application.  The script is run by:

    manage.py runscript calc_readings

This script is also called from the main_cron.py script.
'''

import logging
from bmsapp.readingdb import bmsdata
from bmsapp.calcs import calcreadings, calcfuncs01
import bmsapp.models


def run():
    '''This method is called by the 'runscript' command.
    '''

    # make a logger object
    logger = logging.getLogger('bms.calc_readings')

    # get a BMSdata object for the sensor reading database and then make a Calculate
    # Readings object.  Other calculated reading classes in addition to CalcReadingFuncs_01
    # can be added to the list and they will be search for matching function names.
    # Only allow calculated readings within the last 60 days.
    reading_db = bmsdata.BMSdata()
    calc = calcreadings.CalculateReadings([calcfuncs01.CalcReadingFuncs_01, ], reading_db, 60*24*60)

    # Loop through the calculated sensor readings in the proper calculation order,
    # inserting the calculated values in the database.
    for calc_sensor in bmsapp.models.Sensor.objects.filter(is_calculated=1).order_by('calculation_order'):
        try:
            rec_count = calc.processCalc(calc_sensor.sensor_id, calc_sensor.tran_calc_function, calc_sensor.function_parameters)
            logger.debug( '%s %s readings calculated and inserted' % (rec_count, calc_sensor.sensor_id) )
        except:
            logger.exception('Error calculating %s readings' % calc_sensor.sensor_id)

    reading_db.close()
