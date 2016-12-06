'''
Script to collect sensor readings from an OkoFEN pellet boiler.
'''
from datetime import datetime, timedelta, date
import sys
import StringIO
import urlparse
import traceback
import re
import calendar
import requests
import pandas as pd
import pytz

# Parameters that are State-type values instead of continuous analog values.
# The name of the parameter here should be the PXXX number, or the sensor ID
# for a sensor that does not have a PXXX number.  e.g. the "Boiler 1" sensor
# would be shown as 'boiler_1'.
STATE_PARAMS = (
    'P112',
    'P241',
)

# Compiled RegEx used to find parameter number in a parameter name
P_REGEX = re.compile('^P\d{3}\s')

def run(url= '', site_id='', tz_data='US/Alaska', last_date_loaded='2016-01-01', **kwargs):
    """

    Parameters
    ----------
    url:  The base URL including port (if not port 80) for the OkoFEN boiler.
        e.g. http://64.189.233.145:8888
    site_id: A string to identify this particular boiler, e.g. 'Haines_boiler1'.  Used to
        create Sensor IDs for each of the readings.
    tz_data:  Olson Timezone string indicating what timezone the boiler data is represented
        in.  Sometimes, the timezone of the boiler is set to a value not consistent with
        where the boiler is located.  See https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
        for valid timezone string values.
    last_date_loaded: This is the date in YYYY-MM-DD format of the last CSV file loaded by
        the script.  The script will try to load CSV files timestamped after that date, but
        no further in the past than 2 weeks.
    kwargs:  No other keyword arguments are used.

    Returns
    -------
    A dictionary with the following keys are values:
        readings: A list of sensor readings in the Periodic Script format
            (ts, Sensor ID, value)
        last_date_loaded: A date string like '2016-11-22' that indicated the date
            of the last CSV file successfully loaded
        errors: A string listing any errors that occurred while fetching data.
        sensor_ids: A comma-separated string of the sensor IDs that were read for
            the last CSV file loaded.
    """

    # tracks errors that occur in the collection
    errors = ''

    # list of readings to return
    readings = []

    # list of sensor IDs found in the data.  Returned for information
    # to the System Admin
    sensor_ids = []

    # dictionary of results to return
    results = {}

    # get last day loaded into datetime format.  If it was entered
    # in the YAML Parameters box, it has already been converted to a
    # date
    if type(last_date_loaded) == type(date.today()):
        last_date = last_date_loaded
    else:
        try:
            last_date = datetime.strptime(last_date_loaded, '%Y-%m-%d').date()
        except:
            # if the date string wasn't proper, set to two weeks + 1 day ago
            last_date = date.today() - timedelta(days=15)

    try:
        # get the next CSV file date to load
        next_date = last_date + timedelta(days=1)

        # but limit this to two weeks ago
        next_date = max(next_date, date.today() - timedelta(days=14))

        # Each sensor reading type can have a "converter" function applied
        # to it prior to storing.  List the function in the dictionary below
        # if such conversion is required.
        converters = {
            'P116': lambda x: x / 10.0,
            'P117': lambda x: x / 10.0,
        }

        while next_date <= date.today():
            try:
                # make the CSV file name
                fname = next_date.strftime('csv/%Y-%m-%d_00-00.csv')

                resp = requests.get(urlparse.urljoin(url, fname), timeout=6)
                doc = resp.text
                df = pd.read_csv(StringIO.StringIO(doc),
                                 sep=';',
                                 decimal=',',
                                 index_col=False,
                                 )
                # clean up the column names
                cols = []
                for col in df.columns:
                    match_res = P_REGEX.match(col)
                    if match_res:
                        # there was a parameter number in the column name
                        col = match_res.group(0).strip()
                    else:
                        # no parameter number, so make a clean column name
                        col = col.replace('.', '').replace(' ', '_').replace('/', '_').lower()
                    cols.append(col)
                cols[0] = 'datetime'
                df.columns = cols

                # make a list of UNIX timestamps and then dispose of the datetime
                # column since it is not a sensor reading column.
                tstamps = [ts_from_datestr(dt, tz_data) for dt in df['datetime']]
                df.drop(['datetime'], axis=1, inplace=True)

                # loop through the columns, creating readings
                sensor_ids = []
                for col in df.columns:
                    sensor_id = '%s_%s' % (site_id, col)
                    sensor_ids.append(sensor_id)    # list used later to return info on sensors read

                    # apply a converter function to the values if necessary
                    if col in converters:
                        vals = converters[col](df[col].values)
                    else:
                        vals = df[col].values

                    # get a set of filtered sensor readings, filtered to show significant changes.
                    filtered_ts, filtered_vals = find_changes(tstamps, vals,
                                                              state_change=(col in STATE_PARAMS))

                    new_reads = zip(filtered_ts, (sensor_id,) * len(filtered_ts), filtered_vals)
                    readings += new_reads

                # successfully loaded this date, so update the tracking variable
                last_date = next_date

            except Exception as e:
                errors += 'Error loading %s: %s; ' % (next_date.strftime('%Y-%m-%d'), str(e))

            finally:
                # increment the day and go on
                next_date += timedelta(days=1)

    except:
        # Store information about the error that occurred
        errors += traceback.format_exc()

    finally:
        results['readings'] = readings
        results['last_date_loaded'] = last_date.strftime('%Y-%m-%d')
        results['sensor_ids'] = ', '.join(sensor_ids)
        results['script_errors'] = errors
        return results

def ts_from_datestr(datestr, tzname):
    """Converts a date/time string in the format '%Y-%m-%d %H:%M' into a Unix timestamp
    assuming the date/time is expressed in the 'tzname' timezone.
    """
    tz = pytz.timezone(tzname)
    dt = datetime.strptime(datestr, '%Y-%m-%d %H:%M')
    dt_aware = tz.localize(dt)
    return calendar.timegm(dt_aware.utctimetuple())


def find_changes(times, vals, state_change=False, min_change=0.02, max_spacing=600):
    """Finds significant analog or state changes in a set of sensor readings for one
    sensor, and returns those filtered readings.  This is primarily used to reduce
    the number of sensor readings stored.

    Parameters
    ----------
    times: Iterable of UNIX timestamps (seconds past Epoch) for the sensor readings
    vals: Iterable of sensor reading values
    state_change: If True, treats the sensor readings as State values, not continuous
        analog values.  For this type of reading, every change is considered significant
        and is returned in the filtered list.
    min_change:  This determines what is considered a significant change for an analog
        sensor reading.  This argument is expressed as the fraction of the difference
        between the minimum and maximum sensor reading in the input set.
    max_spacing: If no significant change has occurred in 'max_spacing' number of seconds
        then a sensor reading is returned anyway.

    Returns
    -------
    A two-tuple, the first element being a list of timestamps of the filtered readings,
    and the second element being a list of filtered readings.
    """
    if state_change:
        # any change at all counts as a change.  Use smallest float as trigger
        chg_trigger = sys.float_info.min
    else:
        chg_trigger = (max(vals) - min(vals)) * min_change  # 2% change trigger reading
        if chg_trigger == 0.0:
            chg_trigger = sys.float_info.min  # must be some change to record a reading

    # Always include first point
    filtered_ts = [times[0]]
    filtered_vals = [vals[0]]

    for ts, val in zip(times[1:], vals[1:]):
        if abs(val - filtered_vals[-1]) >= chg_trigger or (ts - filtered_ts[-1]) >= max_spacing:
            filtered_ts.append(ts)
            filtered_vals.append(val)

    return filtered_ts, filtered_vals
