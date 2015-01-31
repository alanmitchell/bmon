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

# change into the directory of this script
os.chdir(os.path.dirname(sys.argv[0]))

# get parent directory into path
sys.path.insert(0, '../')
import bmsdata

# path to reading database
db_path = bmsdata.DEFAULT_DB

# make backup filename with current date time in 'bak' subdirectory
fname = os.path.join(os.path.dirname(db_path), 'bak', time.strftime('%Y-%m-%d-%H%M%S') + '.sqlite')

# Before copying the database file, need to force a lock on it so that no
# write operations occur during the copying process
conn = sqlite3.connect(db_path)
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
shutil.copy(db_path, fname)

# Rollback the Insert as we don't really need it.
conn.rollback()

# gzip the backup file
subprocess.call(['gzip', fname])

# delete any backup files more than 3 weeks old
cutoff_time = time.time() - 3 * 7 * 24 *3600.0
for fn in glob.glob(os.path.join(os.path.dirname(db_path), 'bak', '*.gz')):
    if os.path.getmtime(fn) < cutoff_time:
        os.remove(fn)
