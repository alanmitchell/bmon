#!/bin/bash

# Script to backup the data in the 'reading' table of the BMS database.
# Backup files are gzipped comma-delimited and placed in the bak directory.

cd ~/webapps/django/rm/bmsapp/data
fname=bak/`date +%Y-%m-%d-%H%M%S`.csv
/usr/bin/sqlite3 bms_data.sqlite <<!
.mode csv
.output $fname
select * from reading;
!
gzip $fname
