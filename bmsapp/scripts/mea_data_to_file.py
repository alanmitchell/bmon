#!/usr/bin/env python3.7
'''Script that can be called by "mail2script" when an email from Matanuska Electric
Association containing 15 minute usage data is received.  This script parses the
data from the email, which is stored in attached Excel files, and then stores
the data in CSV files to be later processed by the separate file-to-bmon application.

This script stores data files and log files into the '~/mea_data' directory.  This directory
must be created, and two subdirectories must be present in that directory: 'data' and
'email_logs'.  The created CSV files will be stored in the '~/mea_data/data' directory,
and the application log files will be stored in '~/mea_data/email_logs' directory. 
'''

from pathlib import Path
import sys
import email
from io import BytesIO
import logging
import logging.handlers
import pandas as pd
import numpy as np

# Log file for the application
LOG_FILE = str(Path('~/mea_data/email_logs/mea_email.log').expanduser())

# create base logger for the application.
_logger = logging.getLogger('meadata')

# set the log level
_logger.setLevel(logging.INFO)

# create a rotating file handler
fh = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes=200000, backupCount=5)

# create formatter and add it to the handler
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)

# add the handler to the logger
_logger.addHandler(fh)

# variable for the base data directory
data_path = Path('~/mea_data/data').expanduser()

try:

    # the email comes from stdin; read it into a Message object
    msg = email.message_from_file(sys.stdin)

    # Find all the attachments that are Excel files and process
    for part in msg.walk():
        fname = part.get_filename()
        if (fname is not None) and ('.xlsx' in fname):
            try:
                attachment = part.get_payload(decode=True)
                df = pd.read_excel(BytesIO(attachment)).dropna(how='all')

                # used to assemble final DataFrame from individual DataFrames from
                # each row.
                df_final = pd.DataFrame()
                for ix, row in df.iterrows():
                    row_data = row.dropna().values
                    if len(row_data) == 98:
                        vals = row_data[2:].astype(float) * 4.0  # x 4 to convert from 15 min kWh to average kW
                        sensor_id = f'mea_{row_data[0]}'

                        # Make timestamps, 15 minutes apart, starting at 7.5 minutes past
                        # Midnight.
                        day_start = row_data[1].tz_localize('US/Alaska', ambiguous='NaT').value // 10 ** 9
                        seconds = np.array(list(range(15 * 60 // 2, 3600 * 24, 900)))
                        ts = day_start + seconds

                        # Put into DataFrame for easy filtering
                        dfr = pd.DataFrame({'ts': ts, 'val': vals, 'id': [sensor_id] * 96})
                        df_final = pd.concat([df_final, dfr])

                # Remove outliers from data.  No zero values, and no very large values,
                # more than 2.5 times 95th percentile value.
                find_good = lambda x: (x > 0) & (x < x.quantile(.95) * 2.5)
                good_data = df_final.groupby('id')['val'].transform(find_good).astype(bool)
                df_final = df_final[good_data]

                # Write to a CSV file
                out_path = data_path / Path(fname).with_suffix('.csv')
                df_final.to_csv(out_path, index=False)  # Pandas takes Path's directly

                _logger.info(f'{len(df_final)} records processed from {fname}')

            except Exception as e:
                _logger.exception('Error processing MEA data from file %s.' % fname)

except Exception as e:
    _logger.exception('Error processing MEA data.')
