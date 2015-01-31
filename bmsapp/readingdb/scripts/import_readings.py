"""Script to import a file(s) of sensor readings into the reading database.
The script must be called with one command line argument that gives the file
to import or a glob wildcard spec for a set of files.  So, examples of running
the script are:

    ./import_readings.py readings.txt
    ./import_readings.py *.txt

The script uses the bmsapp.readingdb.bmsdata.BMSdata.import_text_file() method,
so the text file must comply with the format required by that method, which is:

The file must be tab-delimited and the values in the first column must be date/time 
strings interpretable by the Python dateutil parser module.  Subsequent columns 
must contain sensor reading values; the each item can be blank or contain a value parseable 
by the Python float function. The first non-blank row of the file must contain sensor IDs 
(the first column of that row can contain anything, as it is the timestamp column). An
exmaple of the format is (white space separation between columns need to be the Tab
character):

    ts                 id_2341   test_alarm_code
    4/12/2014 13:23    2.2       44.3
    4/12/2014 13:33    3.2       41.1

"""

import sys, glob

# Add the parent directory to the Python import path
sys.path.insert(0, '../')

import bmsapp.readingdb.bmsdata

# Open reading database object
db = bmsapp.readingdb.bmsdata.BMSdata()

for filename in glob.glob(sys.argv[1]):
    success_count, errors = db.import_text_file(filename)
    print '\n%s readings successfully stored and %s errors.' % (success_count, len(errors))
    if len(errors):
        for err_desc in errors:
            print err_desc
db.close()