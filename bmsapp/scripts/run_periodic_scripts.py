'''Runs periodic scripts that are set up in the Django Admin for this
instance of BMON.  Often, these scripts collect reading values and insert
them into the reading database.
This script is usually run via a cron job every five minutes.

This script is set up to run through use of the django-extensions runscript
feature, in order that the script has easy access to the Django model data
for this application.  The script is run by:

    manage.py runscript run_periodic_scripts

This script is also called from the main_cron.py script.
'''

import logging
import threading
import time
from bmsapp.readingdb import bmsdata
import bmsapp.models

CRON_PERIOD = 300

def run():
    '''This method is called by the 'runscript' command and is the entry point for
    this module.
    '''

    # make a logger object
    logger = logging.getLogger('bms.run_periodic_scripts')

    # get a BMSdata object for the sensor reading database.
    reading_db = bmsdata.BMSdata()


class RunScript(threading.Thread):
    '''
    This class will run one periodic script in a separate thread.
    '''

    def __init__(self, script, cron_time=time.time()):
        """
        :param script: the models.PeriodicScript object containing info about the
            script to run.
        :param cron_time:  the UNIX epoch timestamp of the time when this batch of
            scripts was initiated.  This time is used to determine whether it is the
            proper time to run the script.
        """
        threading.Thread.__init__(self)
        self.script = script
        self.cron_time = cron_time

    def run(self):
        """This function is run in a new thread and runs the desired script if the time is correct
        """

        if (self.cron_time % script.period) >= CRON_PERIOD:
            # Not the correct time to run script, so exit.
            return

