#!/usr/local/bin/python2.7

# Script to backup the BMS sensor reading database.
# The database is copied, gzipped, and placed in the bak directory.

import os
import sys
import time
import sqlite3
import shutil
import subprocess
import glob

SENSOR_DB = 'bms_data.sqlite'

# change into the directory of this script
os.chdir(os.path.dirname(sys.argv[0]))

# make backup filename with current date time
fname = 'bak/' + time.strftime('%Y-%m-%d-%H%M%S') + '.sqlite'

# Before copying the database file, need to force a lock on it so that no
# write operations occur during the copying process
conn = sqlite3.connect(SENSOR_DB)
cur = conn.cursor()

# create a dummy table to write into.
try:
    cur.execute('CREATE TABLE _junk (x integer)')
except:
    # table already existed
    pass

# write a value into the table to create a lock on the database
cur.execute('INSERT INTO _junk VALUES (1)')

# now copy database
shutil.copy(SENSOR_DB, fname)

# Rollback the Insert as we don't really need it.
conn.rollback()

# gzip the backup file
subprocess.call(['gzip', fname])

# delete any backup files more than 3 weeks old
cutoff_time = time.time() - 3 * 7 * 24 *3600.0
for fn in glob.glob('bak/*.gz'):
    if os.path.getmtime(fn) < cutoff_time:
        os.remove(fn)
