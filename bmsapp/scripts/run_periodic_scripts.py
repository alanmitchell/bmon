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


def run():
    '''This method is called by the 'runscript' command and is the entry point for
    the script.
    '''

    # make a logger object
    logger = logging.getLogger('bms.run_periodic_scripts')

    # get a BMSdata object for the sensor reading database.
    reading_db = bmsdata.BMSdata()

class RunScript(threading.Thread):
    '''
    This class will run one periodic script in a separate thread.
    '''

    def __init__(self, script_name, cron_time=time.time()):
        '''
        :param script_name: Name of the s
        :param cron_time:
        '''
        threading.Thread.__init__()
        self.script_name = script_name
        self.cron_time = cron_time