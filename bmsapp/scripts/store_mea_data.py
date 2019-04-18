#!/usr/bin/env python
'''Script that is called by "mail2script" when an email from MEA containing
usage data is received.  This script stores the reading in the email into
BMON reading database.
'''

import os
import sys
import email
from io import StringIO
import logging
import django
import pandas as pd
import numpy as np

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

                # used to assemble final DataFrame from individual DataFrames from
                # each row.
                df_final = pd.DataFrame()
                for ix, row in df.iterrows():
                    row_data = row.dropna().values
                    if len(row_data) == 98:
                        vals = row_data[2:].astype(float) * 4.0  # x 4 to convert from 15 min kWh to average kW
                        sensor_id = row_data[0]

                        # Make timestamps, 15 minutes apart, starting at 7.5 minutes past
                        # Midnight.
                        day_start = row_data[1].tz_localize('US/Alaska', ambiguous='NaT').value // 10 ** 9
                        seconds = np.array(list(range(15 * 60 / 2, 3600 * 24, 900)))
                        ts = day_start + seconds

                        # Put into DataFrame for easy filtering
                        dfr = pd.DataFrame({'ts': ts, 'val': vals, 'id': [sensor_id] * 96})
                        df_final = pd.concat([df_final, dfr])

                # Remove outliers from data.  No zero values, and no very large values,
                # more than 2.5 times 95th percentile value.
                find_good = lambda x: (x > 0) & (x < x.quantile(.95) * 2.5)
                good_data = df_final.groupby('id')['val'].transform(find_good).astype(bool)
                df_final = df_final[good_data]

                stamps = df_final.ts.values
                ids = df_final.id.astype('str').values
                vals = df_final.val.values

                insert_msg = db.insert_reading(stamps, ids, vals)
                _logger.info('MEA Data processed from %s:\n    %s' % (fname, insert_msg))

            except Exception as e:
                _logger.exception('Error processing MEA data from file %s.' % fname)

except Exception as e:
    _logger.exception('Error processing MEA data.')

finally:
    db.close()
