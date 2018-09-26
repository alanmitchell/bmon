# -*- coding: UTF-8 -*-
'''
Script to collect sensor readings from an OkoFEN pellet boiler with a Touch
interface.  This is the type of boiler used by Tlingit Haida at the Juneau
Warehouse and the Angoon multi-family building.  The 'okofen.py' script works
with the older boiler interface, the interface used with the boiler at the
Haines Senior Center.
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

# A function to clean up the native field names found in the CSV file into simpler
# field names.
def clean_col_name(c):
    nm = c.strip().replace(' ', '_').replace('PE1_', '').replace('[', '_')
    nm = nm.replace(']', '').replace('°', '').replace('__', '_').replace('%', 'pct')
    return nm

# A dictionary that maps the cleaned up native field names (in German) from the CSV file
# into English names.  Also, only these fields will be kept
col_map = {
    'KT_C': 'boiler_temp',
    'KT_SOLL_C': 'boiler_temp_setpt',
    'Modulation_pct': 'burner_modulation_pct',
    'FRT_Ist_C': 'combustion_chamber_temp',
    'FRT_Soll_C': 'combustion_chamber_temp_setpt',
    'Einschublaufzeit_zs': 'auger_run_time',
    'Luefterdrehzahl_pct': 'burner_fan_speed',
    'Saugzugdrehzahl_pct': 'flue_gas_fan_speed',
    'Unterdruck_Ist_EH': 'negative_draft',
    'Status': 'boiler_status',
}

# Each sensor reading type can have a "converter" function applied
# to it prior to storing.  List the function in the dictionary below
# if such conversion is required.
c_to_f = lambda x: x * 1.8 + 32.0     # deg C to deg F
converters = {
    'boiler_temp': c_to_f,
    'boiler_temp_setpt': c_to_f,
    'combustion_chamber_temp': c_to_f,
    'combustion_chamber_temp_setpt': c_to_f,
}

# Fields that are State-type values instead of continuous analog values.
# The name of the parameter here should be the PXXX number, or the sensor ID
# for a sensor that does not have a PXXX number.  e.g. the "Boiler 1" sensor
# would be shown as 'boiler_1'.
state_fields = (
    'boiler_status',
)

def run(url= '', site_id='', 
        tz_data='US/Alaska', 
        last_date_loaded='2016-01-01', 
        last_ts_loaded=0, 
        **kwargs
        ):
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
        the script.  The script will try to load CSV files timestamped on or after that date, but
        no further in the past than 2 weeks.  The script reloads last_date_loaded because it 
        may have been a partial day.
    last_ts_loaded: Unix timestamp of the last record loaded.  This is used to avoid duplicate
        loading duplicate records from the last_date_loaded. The boiler drops partial-day CSV
        files.
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

    # Get a timezone object for the timezone that the data is presented in
    tz = pytz.timezone(tz_data)

    # tracks errors that occur in the collection
    errors = ''

    # list of readings to return
    readings = []

    # list of sensor IDs found in the data.  Returned for information
    # to the System Admin
    sensor_ids = []

    # dictionary of results to return
    results = {}

    # Today's date as a naive date object
    today = datetime.now(tz).date()

    # get last day loaded into datetime format.  If it was entered
    # in the YAML Parameters box, it has already been converted to a
    # date
    if type(last_date_loaded) == type(today):
        last_date = last_date_loaded
    else:
        try:
            last_date = datetime.strptime(last_date_loaded, '%Y-%m-%d').date()
        except:
            # if the date string wasn't proper, set to two weeks + 1 day ago
            last_date = today - timedelta(days=15)

    try:
        # reload the last successful day, because the day may have been partial.
        next_date = last_date

        # but limit this to two weeks ago
        next_date = max(next_date, today - timedelta(days=14))

        while next_date <= today:
            try:
                # make the CSV file name
                fname = next_date.strftime('logfiles/pelletronic/touch_%Y%m%d.csv')

                resp = requests.get(urlparse.urljoin(url, fname), timeout=15)
                doc = resp.text
                df = pd.read_csv(StringIO.StringIO(doc),
                                 sep=';',
                                 decimal=',',
                                 parse_dates=[['Datum ', 'Zeit ']],
                                 index_col=False,
                                 )
                # clean up the column names
                cols = [clean_col_name(col) for col in df.columns]
                cols[0] = 'datetime'
                df.columns = cols

                # make a list of UNIX timestamps and then dispose of the datetime
                # column since it is not a sensor reading column.
                tstamps = [ts_from_datetime(dt, tz) for dt in df['datetime']]
                df.drop(['datetime'], axis=1, inplace=True)

                # Narrow down the columns to just the ones in the column map from above
                df = df[list(col_map.keys())]
                # Now rename those columns according to the column map
                df.columns = [col_map[c] for c in df.columns]

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
                                                              state_change=(col in state_fields))

                    new_reads = zip(filtered_ts, (sensor_id,) * len(filtered_ts), filtered_vals)
                    
                    # Only keep the readings after last_ts_loaded
                    new_reads_after = [rd for rd in new_reads if rd[0] > last_ts_loaded]
                    
                    readings += new_reads_after

                # successfully loaded this date, so update the tracking variable
                last_date = next_date
                last_ts_loaded = tstamps[-1]  # last timestamp

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
        results['last_ts_loaded'] =  last_ts_loaded
        results['sensor_ids'] = ', '.join(sensor_ids)
        results['script_errors'] = errors
        return results

def ts_from_datetime(datetm, tz_obj):
    """Converts a date/time string in the format '%Y-%m-%d %H:%M' into a Unix timestamp
    assuming the date/time is in the timezone identified by the timezone object tz_obj.
    """
    dt_aware = tz_obj.localize(datetm)
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
