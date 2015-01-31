'''Script to insert some summary info about database size and insertions.
This script is run through the django-extensions runscript facility.  To run:

    manage.py runscript daily_status

'''
import logging 
import time
import bmsapp.readingdb.bmsdata


def run():
    '''This method is called by the 'runscript' command.
    '''
    # get an appropriate logger to use
    logger = logging.getLogger('bms.daily_status')

    # get a BMSdata object for the sensor reading database.
    reading_db = bmsapp.readingdb.bmsdata.BMSdata()
    logger.info( '{:,} readings inserted in last day. {:,} total readings.'.format(reading_db.readingCount(time.time() - 3600*24), reading_db.readingCount()) )
    reading_db.close()
