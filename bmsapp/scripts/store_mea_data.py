#!/usr/bin/env python
'''Script that is called by "mail2script" when an email from MEA containing
usage data is received.  This script stores the reading in the email into
BMON reading database.
'''

import os
import sys
import email
from cStringIO import StringIO
import logging
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

# Make a logger for this module.  I'm doing this after the
# above import because logging is set up when the bmsapp
# package is accessed.  These logger messages will now appear
# in the standard BMON log file.
_logger = logging.getLogger('bms.' + os.path.basename(__file__))

# access the Reading database
db = BMSdata()

try:

    # the email comes from stdin; read it into a Message object
    msg = email.message_from_file(sys.stdin)

    # Find all the attachments that are Excel files and process
    for part in msg.walk():
        fname = part.get_filename()
        if (fname is not None) and ('.xlsx' in fname):
            try:
                attachment = part.get_payload(decode=True)

                df = pd.read_excel(StringIO(attachment)).dropna(how='all')
                df = df[df['Interval kWh'] > 0]    # drop the zero readings

                # get the timestamps, ids and values so they can be stored.
                # Convert date column to Unix Epoch timestamps
                stamps = df['Read Date/Time'].dt.tz_localize('US/Alaska', ambiguous='infer').view('int64').values / int(1e9)
                ids = df['Meter Nbr'].astype('str').values
                # multiply 15 min interval kWh by 4 to get average kW
                vals = (df['Interval kWh'] * 4.0).values

                insert_msg = db.insert_reading(stamps, ids, vals)
                _logger.info('MEA Data processed from %s:\n    %s' % (fname, insert_msg))

            except Exception as e:
                _logger.exception('Error processing MEA data from file %s.' % fname)

except Exception as e:
    _logger.exception('Error processing MEA data.')

finally:
    db.close()
