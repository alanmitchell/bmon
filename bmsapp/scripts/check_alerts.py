'''Checks all alert conditions and notifies recipients as needed.  Should
be run with the django-extensions runscript facility:

    manage.py runscript check_alerts

This script is also called from the main_cron.py script.    
'''
import logging
import time
from bmsapp.models import AlertCondition
from bmsapp.readingdb.bmsdata import BMSdata


def run():
    '''Checks all Alert conditions and notifies Alert recipients for those
    conditions that are true.
    Returns the number alerts where the alert condition is true.
    '''

    # make a logger object
    logger = logging.getLogger('bms.check_alerts')

    # get a sensor reading database object
    reading_db = BMSdata()

    total_true_alerts = 0
    
    for condx in AlertCondition.objects.all():
        # Only send alerts if there are buildings associated with the
        # alert sensor.
        if len(condx.sensor.building_set.all()) > 0:
            total_true_alerts += condx.handle(reading_db, logger)

    return total_true_alerts
