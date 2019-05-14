"""Script to collect data from Enphase Solar PV systems.  The data collection 
function is named "run" and is called by the "scripts/run_periodic_scripts.py" 
module.
"""

import time
import traceback
import requests
import dateutil
import pytz
import pandas as pd

# seconds of delay between each API call; needed to satisfy 10 calls/minute
# rate limit.
DELAY_BTWN_SYSTEMS = 6.0

# Base API URL, with System ID insertion point
BASE_URL = 'https://api.enphaseenergy.com/api/v2/systems/{}/'

def run(api_key, systems, first_date=None, first_date_tz='America/Anchorage', last_ts=None, **kwargs):
    '''The main function called by the Periodic Script.  The following parameters
    come from the "Script Parameters in YAML form" box:
        api_key:  The API key required to access the Enphase API
        systems:  A list of systems to collect data from.  Each item in the list is a 
            dictionary containing a 'user_id' key and a 'system_id' key, with associated
            values identifying the system.
        first_date: (optional) On the first run of the function, this will be the earliest
            date requested.  It can be in any format parseable by the Python dateutil.parser.parse
            function.  It will be deleted after the first successful run of the script.
        first_date_tz: (optional) This is the timezone used for 'first_date', if 'first_date'
            is provided.  It will be deleted after the first successful run of the script.
        last_ts:  Returned by the prior function call.  This is a dictionary, keyed on a string
            of {user_id}_{system_id} (tuples do not dump to YAML well), and the value of the 
            item is the Unix epoch timestamp of the last retrieved record.
    '''

    # We'll handle errors within the script so that a script return value can be
    # provided. We don't want to lose the last_ts dictionary that tracks where we
    # are with each system. 
    try:     
        
        # if there is no dictionary of last record timestamps, create an empty one.
        if last_ts is None:
            last_ts = {}
        
        # start the list that will accumulate all of the readings
        readings = []
        
        # loop through each system, getting its data
        for a_sys in systems:
            # break into components
            user_id = a_sys['user_id']
            system_id = a_sys['system_id']
            # and make a string combining user and system
            user_sys = f'{user_id}_{system_id}' 
                    
            # Get a timestamp to start at
            if user_sys in last_ts:
                # a prior run supplies the last retrieved timestamp
                start_at = last_ts[user_sys]
            elif first_date is not None:
                # no prior run but a config parameter was supplied to determine 
                # what time to start retrieving records at.
                dt_start = dateutil.parser.parse(str(first_date))
                dt_start = dt_start.astimezone(pytz.timezone(first_date_tz))
                start_at = int(dt_start.timestamp())
            else:
                # Start 1 day ago as a default.
                start_at = int(time.time() - 24 * 3600)
                
            payload = {
                'key': api_key,
                'user_id': user_id,
                'start_at': start_at
            }
            res = requests.get(BASE_URL.format(system_id) + 'stats', params=payload).json()
            
            # if there is data, there will be an 'intervals' key in the results
            if 'intervals' in res:

                # make a list of tuples having the data we need
                recs = [ (r['end_at'], r['powr']) for r in res['intervals'] ]

                if len(recs):
                    
                    # Unfortunately, API will not return records for periods where there is no power
                    # production.  Need to fill in with 0s for those 5 minute periods.  Do that
                    # through use of Pandas DataFrame
                    df = pd.DataFrame(recs, columns=['ts', 'val'])
                    df.set_index('ts', inplace=True)
                    
                    # make a new index that contains all of the 5 minute intervals starting
                    # just past start_at (API only returns records > start_at, not >= start_at).
                    # Deal with the case where 'start_at' may not be exactly on a 5 minute interval
                    # because it did not come from a prior set of readings.
                    ix_start = start_at + 300 - (start_at % 300)
                    ix_end = df.index[-1]                          # inclusive
                    new_index = pd.RangeIndex(ix_start, ix_end + 1, 300)
                    df2 = df.reindex(new_index)
                    df2.fillna(0.0, inplace=True)
                    
                    # make lists of the timestamps and the values
                    ts = list(df2.index.values)
                    val = list(df2.val.values)
                    
                    last_rec_ts = ts[-1]    # the timestamp of the last record
                    
                elif time.time() > start_at + 24*3600:
                    # sometimes there will be a 24 hour period without any reports, so advance
                    # the starting time a day.  Only do this if it will not advance
                    # beyond the current time.
                    
                    # fill in 0s for these missing records
                    ix_start = start_at + 300 - (start_at % 300)
                    ix_end = ix_start + 3600 * 24 - 300           # inclusive
                    ts = list(range(ix_start, ix_end + 1, 300))
                    val = [0.0] * len(ts)
                    last_rec_ts = ts[-1]
                    
                else:
                    ts = []
                    val = []
                    last_rec_ts = start_at
                    
                # make a sensor ID for this system
                sensor_id = f'enph_{user_sys}'
                sensor_ids = [sensor_id] * len(ts)
                
                # make a list of the new records and append to the ongoing list
                new_recs = list( zip(ts, sensor_ids, val) )
                readings += new_recs
                
                # update the timestamp of the last downloaded record
                last_ts[user_sys] = int(last_rec_ts)
                
                # sleep to keep calls under the 1 minute rate limit
                time.sleep(DELAY_BTWN_SYSTEMS)
    
    except:
        # an error occurred, return the error traceback and the
        # last_ts dictionary.  We're handling the error internal to the
        # script so that we can retain the last_ts dictionary.
        return {
            'last_ts': last_ts,
            'script_error': traceback.format_exc()
        }

    return {
        'readings': readings, 
        'last_ts': last_ts,
        'delete_params': ['first_date', 'first_date_tz']
    }
