"""Script to backup the BMS sensor reading database.
The database is copied, gzipped, and placed in the bak directory.
This script is run via django-extensions runscript facility:

    manage.py runscript backup_readingdb

This script is also called from the main_cron.py script.
""" 
import bmsapp.readingdb.bmsdata

DAYS_TO_RETAIN = 21   # days of old backup files to retain

def run():
    '''Method called by runscript.
    '''
    db = bmsapp.readingdb.bmsdata.BMSdata()
    db.backup_db(DAYS_TO_RETAIN)
    db.close()
