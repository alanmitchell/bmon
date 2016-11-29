'''
Script to collect sensor readings from an OkoFEN pellet boiler.
'''
from datetime import datetime, timedelta, date
import StringIO
import urlparse
import traceback
import re
import calendar
import requests
import pandas as pd
import pytz

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
                    col = re.sub('^P\d{3}\s', '', col)  # remove PXXX identifier
                    col = col.replace('.', '').replace(' ', '_').replace('/', '_').lower()
                    cols.append(col)
                cols[0] = 'datetime'
                df.columns = cols

                # *** TESTING ONLY ***
                # Take every third record
                # Drop this eventually and replace with data aggregation and selection
                every_third = [x % 3 == 0 for x in range(len(df))]
                df = df[every_third]

                # make a list of UNIX timestamps and then dispose of the datetime
                # column since it is not a sensor reading column.
                tstamps = [ts_from_datestr(dt, tz_data) for dt in df['datetime']]
                df.drop(['datetime'], axis=1, inplace=True)

                # loop through the columns, creating readings
                sensor_ids = []
                for col in df.columns:
                    sensor_id = '%s_%s' % (site_id, col)
                    sensor_ids.append(sensor_id)    # list used later to return info on sensors read
                    new_reads = zip(tstamps, (sensor_id,) * len(df), df[col].values)
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
