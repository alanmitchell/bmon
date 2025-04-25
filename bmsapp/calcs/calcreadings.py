"""
Code related to adding calculated fields to the sensor reading database.
"""
import time, logging
import numpy as np
import pandas as pd
import yaml

# Make a logger for this module
_logger = logging.getLogger('bms.' + __name__)


class CalculateReadings:
    """
    This class is used to execute the calculated field functions and insert the 
    results into the sensor reading database.  The main method of the class is the 
    'processCalc' method.  This method processes one calculated field.  Please see the
    extensive documentation provided for that method.
    """
    
    def __init__(self, calc_class_list, db, reach_back_mins):
        """Args:
            'calc_class_list': A list of classes (the actual class, not a string) 
                that contain the functions to use to produce the calculated values.  
                The list will be searched sequentially to find a matching function 
                name.
            'db': A bmsdata.BMSdata object holding the sensor reading database.
            'reach_back_mins' (number): Calculated values will not be created more 
                than this number of minutes into the past.
        """
        self.db = db
        self.reach_back = reach_back_mins * 60   # store as seconds

        # instantiate each one of the calculation classes and save the list as 
        # an object property
        self.calc_objects = [cl(db, self.reach_back) for cl in calc_class_list]
        
    def dataForID(self, sensorID, start_ts=0):
        """
        Returns timestamp and values numpy arrays for the sensor with an
        ID of 'sensorID' and having timestamps greater than 'start_ts'.
        """
        ts = []
        vals = []
        # in statement below, need to add 1 second to start_ts because the
        # 'rowsForOneID' method uses a >= test.
        for flds in self.db.rowsForOneID(sensorID, start_tm=start_ts+1):
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
            sync_vals = np.interp(sync_ts, ser_ts, ser_vals, left=np.nan, right=np.nan)
            
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
        are assigned the sensor ID of 'calc_id'.  The method returns the number of 
        records inserted.

        'calcFuncName' is a string giving the name of a method of this class.  The method
        is used to calculate new readings for the sensor database.  'calcParams' is one string
        that is YAML formatted to provide keyword parameters to the function.
        
        There are two categories of functions that can be named by 'calcFuncName':
            *  Functions that expect at least one of the parameters to be the ID of an 
            sensor (or prior calculated field) that already exists in the sensor
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
            id_flow: "12345"
            (all sensor IDs are strings and are therefore quoted, although code has been
            included to assume a string even if the quotes are forgotten)
        If instead there were no flow sensor readings but you know the flow to have the value
        of 60.5, you would pass:
            flow: 60.5
        in the 'calcParams' string.

        If you are using multiple existing sensor readings as inputs to the calculation function,
        the timestamps of the calculated values are synchronized with the first sensor listed in
        the parameter string. To designate a different sensor to be used for synchronization,
        append '_sync' to that parameter name.  For example, to synchronize on the flow sensor in 
        the 'fluidHeatFlow' function, pass:
            id_flow_sync: "12345"
        For the other sensor inputs, sensor values are interpolated to the timestamps of the 
        synchronized sensor.

        For functions that don't operate on existing sensor values, the functions must return a
        list of timestamps and a list of calculated values, since there are no existing sensor
        timestamps to synchronize to.
        """
        
        # Get the function parameters as a dictionary
        params = yaml.load(calcParams, Loader=yaml.FullLoader)
        if params is None:
            params = {}    # substitute empty dictionary for no parameters
        
        # Start a List to hold the sensor IDs that need to be synchronized.  Also start
        # a separate dictionary that will map the parameter names to these IDs, since the
        # the parameter names will be modified.
        ids = []
        id_dict = {}   # keys are modified parameter names, values are sensor IDs.
        
        # Walk through the parameter list finding parameters that are sensor IDs and extract
        # those out.  Put the special sensor that identifies the sensor to synchronize
        # timestamps on at the front of the 'ids' list.
        for nm, id in list(params.items()):

            if nm.startswith('id_'):
                str_id = str(id)    # convert id to string
                if nm.endswith('_sync'):
                    # the sensor to sync on needs to be the first in the ID list.
                    ids.insert(0, str_id)
                    id_dict[nm[3:-5]] = str_id  # strip 'id_' and '_sync' from the name
                else:
                    ids.append(str_id)
                    id_dict[nm[3:]] = str_id    # strip 'id_' from the name

                # delete the parameter from the main parameter dictionary, since it is now
                # stored in the id_dict.
                del params[nm]
        
        # Find the function to call in the list of calculation objects
        func_name = calcFuncName.strip()
        for calc_obj in self.calc_objects:
            if hasattr(calc_obj, func_name):
                calc_obj.calc_id = calc_id   # calc object may need the calc_id
                calc_func = getattr(calc_obj, func_name)
                break

        if len(ids):
            # There are some sensors in the parameter list.  Get a DataFrame of 
            # synchronized readings for those sensors.
            df = self.getDFofSyncedValues(ids, calc_id, time.time() - self.reach_back)
            
            # If there are no rows in the DataFrame, there are no records to add to the
            # database.
            if len(df)==0:
                return 0
            
            # Put the array of values for each sensor back into the main parameter dictionary
            for nm, id in list(id_dict.items()):
                params[nm] = df[id].values
                
            # Save the array of timestamps from the synchronized values
            ts_sync = df.index.values

            # call the calculation function with parameters
            vals = calc_func(**params)
            
            # make the lists for insertion into the database
            # Had trouble inserting numpy data types, so convert to regular python data
            # types.
            ts = list(map(int, ts_sync))
            vals = list(map(float, vals))

        else:
            # There were no sensor IDs in the parameter list.  This calculate function must
            # be the kind that returns a list of timestamps and a list of values for the 
            # records it wants to add to the database.
            stamps, vals = calc_func(**params)

            # Had trouble inserting numpy data types, so convert to regular python data
            # types.
            ts = list(map(int, stamps))
            vals = list(map(float, vals))
        
        # insert the records into the database.
        self.db.insert_reading(ts, len(ts)*[calc_id], vals)  
            
        return len(ts)
    

class CalcReadingFuncs_base:
    """Base class for classes that contain functions for producing calculated
    readings.

    The functions are split into two categories: those for which at least one 
    of the parameters is a NumPy array of sensor readings, and those where none 
    of the input parameters are an array of sensor readings.

    For the functions where one of the parameters is an array of sensor readings, 
    the function must return a list or numpy array of the calculated values, the
    length of that array being the same length as the input sensor value array(s).

    For the functions with none of the parameters being an array of sensor readings,
    the function must return two items: 1) a list (or numpy array) of timestamps
    (Unix seconds) and 2) a list/array of calculated values.
    """

    def __init__(self, db, reach_back_secs):
        """Args:
            db: A bmsdata.BMSdata object holding the sensor reading database.
            
            reach_back_secs (number): Calculated values will not be created more 
            than this number of seconds into the past.
        """
        self.db = db
        self.reach_back = reach_back_secs

        # This is the reading ID string that will be assigned to the calculated 
        # readings. This attribute should be set by the routine calling one of 
        # these functions as some functions need to know the id string to look up
        # past readings in the reading database.
        self.calc_id = None    

