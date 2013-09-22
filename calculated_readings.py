"""
Code related to adding calculated fields to the sensor reading database.
"""
import numpy as np
import pandas as pd
import transforms
import urllib2, time, logging, json, urllib
from metar import Metar

# Make a logger for this module
_logger = logging.getLogger('bms.' + __name__)


class Cache:
    """
    Implements a cache for an object identified by a key.  Allows for a timeout of the
    cached object.
    """
    
    def __init__(self, timeout=600):
        self.timeout = timeout   # number of seconds before timeout of cache item
        self.cache = {}
        
    def store(self, key, obj):
        """
        Stores an object 'obj' in the cache having a key of 'key'.
        """
        self.cache[key] = (time.time(), obj)
        
    def get(self, key):
        """
        Returns an object matching 'key' from the cache if it is present and hasn't 
        timed out.  Returns None otherwise.
        """
        if key in self.cache:
            tm, obj = self.cache[key]
            if (time.time() - tm) < self.timeout:
                return obj
        
        return None

# cache for storing NWS observations
_nws_cache = Cache()   

def getWeatherObservation(stnCode):
    """
    Returns a current weather observation from an NWS weather station, using the metar 
    library to parse and hold the values.  Uses the 'metar' python library.
    """

    URL = 'http://weather.noaa.gov/pub/data/observations/metar/stations/%s.TXT'

    obs = _nws_cache.get(stnCode)   # try cache first

    if obs is None:

        # try 3 times in case of download errors.
        for i in range(3):
            try:
                read_str = urllib2.urlopen(URL % stnCode).read()
                break
            except:
                _logger.info('Retry required in getWeatherObservation.')
                # wait before retrying
                time.sleep(1)

        if 'read_str' not in locals():
            # retries must have failed if there is no 'read_str' variable.
            raise Exception('Could not access %s.' % stnCode)

        obs = Metar.Metar('\n'.join( read_str.splitlines()[1:] ))  # second line onward
        _nws_cache.store(stnCode, obs)

    return obs

# cache for storing Weather Underground observations
_wu_cache = Cache()

def getWUobservation(stnList):
    """
    Returns a current weather observation (dictionary) retrieved from weather underground.
    Google Weather Underground API for more info.  
    'stnList' is a list of Weather Underground stations.  The first one to provide a valid
    current observation is used.
    """

    for stn in stnList:
        # ignore None stations
        if stn is None:
            continue
        
        # retrieve from cache, if there.
        obs = _wu_cache.get(stn)
    
        if obs is None:
            # not in cache; download from weather underground.
            # strange characters after the api are my weather underground key
            json_str = urllib2.urlopen('http://api.wunderground.com/api/52f395599cb1a086/conditions/q/%s.json' % urllib.quote(stn)).read()
            obs = json.loads(json_str)
            _wu_cache.store(stn, obs)

        if 'current_observation' in obs:
            return obs['current_observation']
    
    # No stations were successful
    raise ValueError("No stations with data.")

class CalculateReadings:
    """
    This class is used to execute the calculated field functions and insert the 
    results into the sensor reading database.  The main method of the class is the 
    'processCalc' method.  This method processes one calculated field.  Please see the
    extensive documentation provided for that method.
    """
    
    def __init__(self, db, reach_back_mins):
        """
        'db': a BMSdata object holding the sensor reading database.
        'reach_back_mins': calculated values will not be created more than this number of minutes
            into the past.
        """
        self.db = db
        self.reach_back = reach_back_mins * 60   # store as seconds

        
    def dataForID(self, sensorID, start_ts=0):
        """
        Returns timestamp and values numpy arrays for the sensor with an
        ID of 'sensorID' and having timestamps greater than 'start_ts'.
        """
        ts = []
        vals = []
        for flds in self.db.rowsWhere('id="%s" AND ts>%d ORDER BY ts' % (sensorID, start_ts)):
            ts.append(flds['ts'])
            vals.append(flds['val'])
        return np.array(ts), np.array(vals)

    
    def getDFofSyncedValues(self, input_ids, calc_id=None, earliest_time=0):
        """
        This returns a DataFrame having columns for each of the 'input_ids', which is a list
        of sensor IDs that are inputs for the calculated ID.  The timestamps from the first
        sensor in 'input_ids' are the index of the dataframe.  The timestamps start at the 
        first reading of input_id[0] that occurs past the last reading for 'calc_id', the ID
        of the calculated field.  However, 'earliest_time' overrides this relationship, not 
        allowing input_id[0] timestamps occurring before 'earliest_time'.
        If 'calc_id' is None and 'earliest_time' is 0 (the default), then all 
        timestamps for input_id[0] will be returned.
        For input sensors other than the first, their values are 
        interpolated to match up with the input_id[0] timestamps.  For rows where interpolation
        of any of the inputs cannot occur because the input data does not span the timestamp,
        the row is dropped from the DataFrame.
        """
        
        # determine the timestamp of the last entry in the database for this calculated field.
        last_calc_rec = self.db.last_read(calc_id)
        last_ts = int(last_calc_rec['ts']) if last_calc_rec else 0   # use 0 ts if no records
        
        # constrain this value to greater or equal to 'earliest_time'
        last_ts = max(last_ts, earliest_time)
        
        # get numpy ts and value arrays for the first input for records past this timestamp.
        # these timestamp values will be the common synchronized timestamps for all of the
        # inputs.
        sync_ts, vals0 = self.dataForID(input_ids[0], last_ts)
        
        # if there is no data, we're done and return an empty DataFrame
        if len(sync_ts)==0:
            return pd.DataFrame()
        
        # For the other inputs, start 70 minutes prior to first record in first input's Series
        # in order that timestamps will span the input0 stamps so that interpolation can be 
        # performed.
        inputs_ts_start = sync_ts[0] - 70 * 60
        
        # accumulate all of the input values in a dictionary, keyed on the sensor ID
        input_series = {input_ids[0]: vals0}
        
        # Loop through the rest of the inputs, creating interpolated values for the synchrnonized
        # timestamps.
        for inp_id in input_ids[1:]:
    
            ser_ts, ser_vals = self.dataForID(inp_id, inputs_ts_start)
            
            # if this series is empty, we're toast.  Return with empty DataFrame
            if len(ser_ts)==0:
                return pd.DataFrame()
    
            # use this series as the x and y for interpolation of values
            # for the synchronized ts values.  Fill outside the interpolation
            # table with NaN's, because later data will be eventually arrive which 
            # will providea better interpolation.  These rows will get dropped below.
            sync_vals = np.interp(sync_ts, ser_ts, ser_vals, left=np.NaN, right=np.NaN)
            
            # add these input values to our dictionary of input values
            input_series[inp_id] = sync_vals
        
        # make a DataFrame from these series and drop any row with an NaN.
        df = pd.DataFrame(input_series, index=sync_ts)
        df = df.dropna()
        
        return df
    
    def processCalc(self, calc_id, calcFuncName, calcParams):
        """
        Insert records for the calculated reading using the function with the name
        'calcFuncName' and having the parameters 'calcParams'.  The inserted readings
        have a senor ID of 'calc_id'.  The method returns the number of records inserted.

        'calcFuncName' is a string giving the name of a method of this class.  The method
        is used to calculate new readings for the sensor database.  'calcParams' is one string
        that is formatted like the keyword parameters of a function call; for example:
            heat_capacity=1.08, flow=60
        
        There are two categories of functions that can be named by 'calcFuncName':
            *  Functions that expect at least one of the parameters to be the ID of an 
            sensor (or prior calculated field) that already existing in the sensor
            database.
            *  Functions that do not need to have existing sensor readings as inputs.
            An example is a function that acquires weather data from the Internet.
        In the section of this class where the calculation functions are given, the functions
        are split into these two categories.

        For functions in the first category (those that operate on existing sensor readings),
        you can pass an array of existing sensor readings to the function by prefacing a
        keyword parameter with the string 'id_'.  Using the 'fluidHeatFlow' function as an 
        example, if you want the function to operate on the flow readings recorded by sensor
        12345, you would pass the parameter:
            id_flow="12345"
            (all sensor IDs are strings and are therefore quoted, although code has been
            included to assume a string even if the quotes are forgotten)
        If instead there were no flow sensor readings but you know the flow to have the value
        of 60.5, you would pass:
            flow=60.5
        in the 'calcParams' string.

        If you are using multiple existing sensor readings as inputs to the calculation function,
        the timestamps of the calculated values are synchronized with one of the sensors. To
        designate the sensor to be used for synchronization, append '_sync' to that parameter
        name.  For example, to synchronize on the flow sensor in the 'fluidHeatFlow' function,
        pass:
            id_flow_sync="12345"
        For the other sensor inputs, sensor values are interpolated to the timestamps of the 
        synchronized sensor.

        For functions that don't operate on existing sensor values, the functions must return a
        list of timestamps and a list of calculated values, since there are no existing sensor
        timestamps to synchronize to.
        """
        
        # Save the calculated field ID as an object
        # variable in case any of the calculation functions need to use it.
        self.calc_id = calc_id

        # Get the function parameters as a dictionary
        params = transforms.makeKeywordArgs(calcParams)
        
        # Start a List to hold the sensor IDs that need to be synchronized.  Also start
        # a separate dictionary that will map the parameter names to these IDs, since the
        # the parameter names will be modified.
        ids = []
        id_dict = {}   # keys are modified parameter names, values are sensor IDs.
        
        # Walk through the parameter list finding parameters that are sensor IDs and extract
        # those out.  Put the special sensor that identifies the sensor to synchronize
        # timestamps on at the front of the 'ids' list.
        for nm, id in params.items():

            if nm.startswith('id_'):
                if nm.endswith('_sync'):
                    # the sensor to sync on needs to be the first in the ID list.
                    ids.insert(0, id)
                    id_dict[nm[3:-5]] = id  # strip 'id_' and '_sync' from the name
                else:
                    ids.append(id)
                    id_dict[nm[3:]] = id    # strip 'id_' from the name

                # delete the parameter from the main parameter dictionary, since it is now
                # stored in the id_dict.
                del params[nm]
        
        if len(ids):
            # There are some sensors in the parameter list.  Get a DataFrame of 
            # synchronized readings for those sensors.
            df = self.getDFofSyncedValues(ids, self.calc_id, time.time() - self.reach_back)
            
            # If there are no rows in the DataFrame, there are no records to add to the
            # database.
            if len(df)==0:
                return 0
            
            # Put the array of values for each sensor back into the main parameter dictionary
            for nm, id in id_dict.items():
                params[nm] = df[id].values
                
            # Save the array of timestamps from the synchronized values
            ts_sync = df.index.values
        
            # call the function with the parameters
            vals = getattr(self, calcFuncName.strip())(**params)
            
            # make the list of records to add to the database.
            recs = zip(ts_sync, len(ts_sync)*[self.calc_id], vals)

        else:
            # There were no sensor IDs in the parameter list.  This calculate function must
            # return a list of timestamps and a list of values for the records it wants to 
            # add to the database.
            stamps, vals = getattr(self, calcFuncName.strip())(**params)
            recs = zip(stamps, len(stamps)*[self.calc_id], vals)
        
        # insert the records into the database.
        for ts, id, val in recs:
            # Had trouble inserting numpy data types, so convert to regular python data
            # types.
            self.db.insert_reading(int(ts), str(id), float(val))  
            
        return len(recs)
    

    # ****************** Calculation Functions beyond Here **********************

    # ******* The following functions require that one of parameters be a sensor ID, i.e.
    # at least one of the keyword arguments passed to the 'calcParams' argument of
    # 'processCalc' must be prefaced by 'id_' and the value for that parameter is a 
    # sensor ID.
    # For all of those parameters that are passed to 'processCalc' as sensor IDs, the 
    # functions below receive a numpy array of sensor values as the input parameter.
    # These functions must return a list or numpy array of the calculated values, the
    # length of that array being the same length as the input sensor value array(s).
    # See the section below for functions that don't receive sensor values as inputs.
    
    def fluidHeatFlow(self, flow, Thot, Tcold, heat_capacity, heat_recovery=0.0):
        """
        Heat flow (power) in a fluid.  Inputs are flow rate of fluid, hot and cold
        temperatures and a heat capacity.  A heat_recovery fraction can also
        be provided, which if greater than 0 will dimish the calculated heat flow.
        Any of these parameters can be passed to 'processCalc' as sensor IDs, as 
        array math is used in the calculation below.
        """
    
        # return the records to insert
        return flow * (Thot - Tcold) * heat_capacity * (1.0 - heat_recovery)

    def linear(self, val, slope=1.0, offset=0.0):
        """
        Returns a new value, linearly related to input value, 'val'.  
        Any parameters can be passed to 'processCalc' as sensor IDs.
        """
        return val * slope + offset
    
    def AminusB(self, A, B):
        """
        Subtracts the 'B' values from the 'A' values.
        Any parameters can be passed to 'processCalc' as sensor IDs.
        """
        return A - B
    
    def AplusBplusCplusD(self, A, B, C=0.0, D=0.0):
        """
        Adds together A, B, C, and D values, with C and D being optional.
        Any parameters can be passed to 'processCalc' as sensor IDs.
        """
        return A + B + C + D
    
    # ******** The following functions don't receive arrays of sensor values as
    # inputs; none of the parameters are passed to 'processCalc' prefaced with 'id_'.
    # Since there are no sensor timestamps to synchronize the calculated values with,
    # the functions below must return two items: a list (or numpy array) of timestamps
    # (Unix seconds) and a list/array of calculated values.

    def getInternetTemp(self, stnCode):
        """
        Returns an outdoor dry-bulb temperature from an NWS weather station in degrees F.
        Returns just one record of information, timestamped with the current time.
        """
        obs = getWeatherObservation(stnCode)
        return [int(time.time())], [obs.temp.value() * 1.8 + 32.0]
    
    def getInternetWindSpeed(self, stnCode):
        """
        Returns a wind speed in mph from an NWS weather station.
        Returns just one record of information, timestamped with the current time.
        """
        obs = getWeatherObservation(stnCode)
        return [int(time.time())], [obs.wind_speed.value() * 1.1508]  # mph

    def getWUtemperature(self, stn, stn2=None):
        """
        Returns a temperature (deg F) from a Weather Underground station.
        'stn' is the primary station to use.  'stn2' is a backup station.
        """
        obs = getWUobservation( [stn, stn2] )
        return [int(time.time())], [float(obs['temp_f'])]

    def getWUwindSpeed(self, stn, stn2=None):
        """
        Returns a wind speed (mph) from a Weather Underground station.
        'stn' is the primary station to use.  'stn2' is a backup station.
        """
        obs = getWUobservation( [stn, stn2] )
        return [int(time.time())], [float(obs['wind_mph'])]
    
    def runtimeFromOnOff(self, onOffID, runtimeInterval=30):
        """
        Calculates runtime fraction data for a sensor having the id of 'onOffID' that produces
        On/Off state change values.  The state change values are either 0.0 (Turns Off) or 
        1.0 (Turns On).  The calculated runtime fractions vary from 0.0 to 1.0, indicating the 
        fraction of the time that the device was On in a particular time interval.  
        'runtimeInterval' is the width of the runtime intervals produced in minutes.  The
        timestamp returned for each interval is placed at the midpoint of the interval.  Records
        are returned for times after the last stored runtime reading, subject to the reach_back
        constraint established in the constructor of this class.
        """
        # determine the timestamp of the last entry in the database for this calculated field.
        last_calc_rec = self.db.last_read(self.calc_id)
        last_ts = int(last_calc_rec['ts']) if last_calc_rec else 0   # use 0 ts if no records
        
        # constrain this value to greater or equal to 'reach_back'
        last_ts = max(last_ts, int(time.time() - self.reach_back))
        
        # get the On/Off values starting two hours prior to this in order to capture at least
        # one state change prior to last_ts.  Put these in a Pandas series
        ts_state = []
        state = []
        for rec in self.db.rowsWhere('id="%s" AND ts>%d' % (onOffID, last_ts - 7200)):
            ts_state.append(rec['ts'])
            state.append(rec['val'])
        states = pd.Series(state, index=ts_state)
        
        # must be at least two records to produce runtime data
        if len(states) < 2:
            return [], []
        
        # turn this into one second data spanning from first entry to last
        new_index = range(states.index[0], states.index[-1] + 1)
        ser_one_sec = states.reindex(new_index).ffill()
        
        # average into bins of runtime data
        interval_seconds = runtimeInterval * 60
        ser_runtime = ser_one_sec.groupby(lambda t: int(t / interval_seconds) * interval_seconds + interval_seconds / 2).mean()
        
        # Drop the last row, since it most always includes only a partial interval of data
        ser_runtime = ser_runtime.drop( [ser_runtime.index[-1]] )
        
        # only keep runtime values for intervals greater than the last recorded calculated
        # runtime.
        ser_runtime = ser_runtime[ser_runtime.index > last_ts]
        
        # return the timestamps and runtime values
        return ser_runtime.index.values, ser_runtime.values
        
    