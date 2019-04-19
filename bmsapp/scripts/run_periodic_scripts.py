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
from datetime import datetime
import random
import importlib
import traceback
import yaml
import bmsapp.storereads
import bmsapp.models

# This is how often the Periodic scripts are checked to see if it is
# time to run them.
CRON_PERIOD = 300    # seconds

def run():
    '''This method is called by the 'runscript' command and is the entry point for
    this module.
    '''

    # make a logger object
    logger = logging.getLogger('bms.run_periodic_scripts')

    # Loop through all of the scripts to run.
    # Use the same time for all of the scripts to determine if
    # they should run or not.
    cron_time = time.time()
    for script in bmsapp.models.PeriodicScript.objects.all():
        try:
            RunScript(script, cron_time).start()
        except:
            logger.exception('Error run %s Periodic Script.' % script.script_file_name)


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

        # check to see if script is disabled, and exit if so.
        if self.script.period == 0:
            return

        if (self.cron_time % self.script.period) >= CRON_PERIOD:
            # Not the correct time to run script, so exit.
            return

        # in order to minimize coincident requests on resources due to multiple scripts
        # starting at the same time, introduce a random delay, up to 10 seconds.
        time.sleep(random.random() * 10.0)

        try:
            # Start a dictionary that holds info about this script run and the
            # results of the script.
            results ={'script_start_time': datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}

            # Start a dictionary that holds results that are not shown in the Admin interface.
            hidden_results = {}

            # get a logger.  First strip off any extension from the script
            # file name and use that as part of the logger name.
            script_mod_base = self.script.script_file_name.split('.')[0]
            logger = logging.getLogger('bms.run_periodic_scripts.' + script_mod_base)

            # Assemble the parameter list to pass to the script.  It consists of the
            # combination of the configuration parameters and saved results from the
            # last run of the script.  Those sets of parameters are in YAML form.
            # There are cases where the same parameter may appear in more than one of
            # these locations.  The highest priority is the Script Parameters, next is
            # visible Script Results, and last is Hidden script results.  This affects
            # the order the parameters dictionary is built.
            param_sources = (self.script.hidden_script_results,
                             self.script.script_results,
                             self.script.script_parameters)
            params = {}

            for param_src in param_sources:
                new_params = yaml.load(param_src, Loader=yaml.FullLoader)
                if type(new_params) == dict:
                    # Update only if there was a valid dictionary of hidden script results
                    params.update(new_params)

            # import the periodic script module, but first strip off any extension that
            # the user may have appended
            script_mod = importlib.import_module('bmsapp.periodic_scripts.' + script_mod_base)

            # The script is coded in the 'run' function, so run it with the input parameters
            # and record the execution time.
            start = time.time()
            script_results = script_mod.run(**params)
            exec_time = time.time() - start
            results['script_execution_time'] = round(exec_time, 2)

            # if the script returned a dictionary, update the results dictionary with those
            # values.
            if type(script_results) == dict:
                results.update(script_results)

            # if the results contains a 'readings' key, then extract those readings for
            # storage into the reading database.
            if 'readings' in results:
                sensor_reads = results.pop('readings')
                if len(sensor_reads):
                    insert_msg = bmsapp.storereads.store_many({'readings': sensor_reads})
                    # store this message so it can be seen in the Django Admin
                    # interface
                    results['reading_insert_message'] = insert_msg
                    logger.debug('Script %s: %s' % (self.script.script_file_name, insert_msg))

            # if the results contains a 'hidden' key, then extract that dictionary and save
            # for storage in the hidden results field.
            if 'hidden' in results:
                # Note that you can put binary data into the values fields of the dictionary.
                # YAML will represent them correctly.
                hidden_results = results.pop('hidden')

            # if there is a "delete_params" key, then the script is requesting that those
            # input parameters, which are in a list, be deleted from the model object.
            # Exmaple use is to delete one-time authorization parameters
            if 'delete_params' in results:
                params = yaml.load(self.script.script_parameters, Loader=yaml.FullLoader)
                if type(params) == dict:
                    for p in results.pop('delete_params'):
                        params.pop(p, None)  # deletes param and no error if not there
                    self.script.script_parameters = yaml.dump(params, default_flow_style=False)

        except:
            # record the traceback of the error in the results variable
            results['script_error'] = traceback.format_exc()

        finally:
            # Store the results back into the model script object so they are
            # viewable in the Admin interface and are available for the next call.
            self.script.script_results = yaml.dump(results, default_flow_style=False)
            self.script.hidden_script_results = yaml.dump(hidden_results, default_flow_style=False)
            self.script.save()


