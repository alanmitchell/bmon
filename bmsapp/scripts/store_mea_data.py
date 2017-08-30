#!/usr/bin/env python
'''Script that is called by "mail2script" when an email from MEA containing
usage data is received.  This script stores the reading in the email into
BMON reading database.
'''

import os
import sys
import email
from cStringIO import StringIO
import django
import pandas as pd

# need to add the directory two above this to the Python path
# so the bmsapp package can be found
this_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.abspath(os.path.join(this_dir, '../../'))
sys.path.insert(0, app_dir)

# prep the Django environment because we need access to the module
# that manipulates the Reading database.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bmon.settings")
django.setup()

# get a Reading database object
from bmsapp.readingdb.bmsdata import BMSdata
db = BMSdata()

# read the email into a Message object
with open(r'C:\Users\Alan\Documents\GitHub\original_msg.txt') as f:
    msg = email.message_from_file(f)

# Find all the attachments that are Excel files and process
for part in msg.walk():
    fname = part.get_filename()
    if (fname is not None) and ('.xlsx' in fname):
        attachment = part.get_payload(decode=True)
        df = pd.read_excel(StringIO(attachment)).dropna(how='all')
        # get the timestamps, ids and values so they can be stored.
        stamps = df['Read Date/Time'].dt.tz_localize('US/Alaska').view('int64').values / int(1e9)
        ids = df['Meter Nbr'].astype('str').values
        # multiply 15 min interval kWh by 4 to get average kW
        vals = (df['Interval kWh'] * 4.0).values
        insert_msg = db.insert_reading(stamps, ids, vals)
        print insert_msg

db.close()
