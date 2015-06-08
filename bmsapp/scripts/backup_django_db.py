'''Script to backup the main Django database, if it is a SQLite database
ending with extension '.sqlite'.
The database is copied, gzipped, and placed in the bak directory beneath
the main Django project directory.
This script is run via django-extensions runscript facility:

    manage.py runscript backup_django_db

This script is also called from the main_cron.py script.
'''
import os
import time
import shutil
import glob
import subprocess
import bmsapp

DAYS_TO_RETAIN = 21   # days of old backup files to retain


def run():

    # get the top level directory of the 'bmsapp' application.
    app_dir = os.path.dirname(bmsapp.__file__)

    # the project directory, where the SQLite files should be, is the parent
    # of the app directory.
    proj_dir = os.path.join(app_dir, '../')

    # the backup directory is a subdirectory of the project directory.
    backup_dir = os.path.join(proj_dir, 'bak')

    # backup all the '.sqlite' files in the project directory
    for fn in glob.glob(os.path.join(proj_dir, '*.sqlite')):
        # make a name and the full path to backup file
        bak_fn = time.strftime('%Y-%m-%d-%H%M%S') + '_' + os.path.basename(fn)
        bak_fn = os.path.join(backup_dir, bak_fn)

        shutil.copy(fn, bak_fn)

        # gzip the backup file
        subprocess.call(['gzip', bak_fn])

    # delete any backup files more than 'days_to_retain' old.
    cutoff_time = time.time() - DAYS_TO_RETAIN * 24 * 3600.0
    for fn in glob.glob(os.path.join(backup_dir, '*.gz')):
        if os.path.getmtime(fn) < cutoff_time:
            os.remove(fn)
