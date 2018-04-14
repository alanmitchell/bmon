"""Parses sensor point data from a trend file created on a
Siemens DDC system.  Used initially with the Mat-Su Borough
School District Siemens system.
Main parsing function to call is 'parse_file'.
"""

import csv
import calendar
import logging
import math
import string
from StringIO import StringIO

import pytz
from dateutil import parser

# Make a logger for this module
_logger = logging.getLogger('bms.' + __name__)

def clean_string(s):
    """Function that "cleans" a string by first stripping leading and trailing
    whitespace and then substituting an underscore for all other whitepace
    and punctuation. After that substitution is made, any consecutive occurrences
    of the underscore character are reduced to one occurrence. Returns the cleaned string.
    Input Parameters:
    -----------------
    s:  The string to clean.
    """
    to_sub = string.whitespace + string.punctuation
    trans_table = string.maketrans(to_sub, len(to_sub) * '_')
    fixed = string.translate(s.strip(), trans_table)

    while True:
        new_fixed = fixed.replace('_' * 2, '_')
        if new_fixed == fixed:
            break
        fixed = new_fixed

    return fixed

def parse_file(csvfile, filename, ts_tz='US/Alaska'):
    """Parses DDC point data from a CSV trend file from a 
    Siemens control system.  Returns three lists:
    list of timestamps in Unix Epoch format, list of sensor IDs,
    and list of values.  Sensor IDs are created fromt the DDC
    point ID by substituting the underbar '_' character for
    spaces and punctuation (see 'clean_string' function above.)
    Input paramters are:
    'csvfile': a file like object containing the data
    'filename': the filename, which is only used in error messages
    'ts_tz': the name of a Olson database time zone, defaulting to US/Alaska.
    """

    # make a timezone object and a CSV reader object
    tstz = pytz.timezone(ts_tz)
    reader = csv.reader(csvfile)

    # read all lines through the header row, gathering up
    # point names along the way.
    names = []
    ln = reader.next()
    while ln[0] != '<>Date':
        if ln[0].startswith('Point_'):
            names.append(clean_string(ln[1]))
        ln = reader.next()

    # Lists to the hold the extracted values
    tstamps = []
    sensor_ids = []
    values = []

    for row in reader:

        # skip rows with less than 3 fields
        if len(row) < 3:
            continue

        try:

            # Loop through the sensor columns, which are from 
            # the 3rd column onward.
            for sensor_id, val in zip(names, row[2:]):

                # tracks whether the record is valid or not
                valid = True
                
                # make the timestamp
                dt_str = ' '.join(row[:2])
                dt = parser.parse(dt_str)
                dt = tstz.localize(dt)
                ts = calendar.timegm(dt.utctimetuple())

                # try to convert value to a float
                try:
                    val = float(val)
                    # do not include NaN values
                    if math.isnan(val):
                        valid = False
                except:
                    # Look for some other valid strings
                    lower_val = val.lower().strip()
                    if lower_val=='on':
                        val = 1.0
                    elif lower_val=='off':
                        val = 0.0
                    else:
                        # Value is not recognized
                        valid = False

                if valid:
                    tstamps.append(ts)
                    sensor_ids.append(sensor_id)
                    values.append(val)

        except Exception as e:
            _logger.exception('Error processing record from file %s: %s' % (filename, row))

    return tstamps, sensor_ids, values
