"""One set of functions for calculated readings.
"""

import time
import pandas as pd
import calcreadings, internetwx

class CalcReadingFuncs_01(calcreadings.CalcReadingFuncs_base):
    """A set of functions that can be used to create calculated readings.  
    """
    
    def fluidHeatFlow(self, flow, Thot, Tcold, heat_capacity, heat_recovery=0.0):
        """** One or more parameters must be an array of sensor readings **

        Heat flow (power) in a fluid.  Inputs are flow rate of fluid, hot and cold
        temperatures and a heat capacity.  A heat_recovery fraction can also
        be provided, which if greater than 0 will dimish the calculated heat flow.
        Any of these parameters can be passed to 'processCalc' as sensor IDs, as 
        array math is used in the calculation below.
        """
    
        # return the records to insert
        return flow * (Thot - Tcold) * heat_capacity * (1.0 - heat_recovery)

    def linear(self, val, slope=1.0, offset=0.0):
        """** One or more parameters must be an array of sensor readings **

        Returns a new value, linearly related to input value, 'val'.  
        Any parameters can be passed to 'processCalc' as sensor IDs.
        """
        return val * slope + offset
    
    def AminusB(self, A, B):
        """** One or more parameters must be an array of sensor readings **

        Subtracts the 'B' values from the 'A' values.
        Any parameters can be passed to 'processCalc' as sensor IDs.
        """
        return A - B
    
    def AplusBplusCplusD(self, A, B, C=0.0, D=0.0):
        """** One or more parameters must be an array of sensor readings **

        Adds together A, B, C, and D values, with C and D being optional.
        Any parameters can be passed to 'processCalc' as sensor IDs.
        """
        return A + B + C + D
    
    # ******** The following functions don't receive arrays of sensor values as
    # The functions below must return two items: a list (or numpy array) of timestamps
    # (Unix seconds) and a list/array of calculated values.

    def getInternetTemp(self, stnCode):
        """** No parameters are sensor reading arrays **

        Returns an outdoor dry-bulb temperature from an NWS weather station in degrees F.
        Returns just one record of information, timestamped with the current time.
        """
        obs = internetwx.getWeatherObservation(stnCode)
        return [int(time.time())], [obs.temp.value() * 1.8 + 32.0]
    
    def getInternetWindSpeed(self, stnCode):
        """** No parameters are sensor reading arrays **

        Returns a wind speed in mph from an NWS weather station.
        Returns just one record of information, timestamped with the current time.
        """
        obs = internetwx.getWeatherObservation(stnCode)
        return [int(time.time())], [obs.wind_speed.value() * 1.1508]  # mph

    def getWUtemperature(self, stn, stn2=None):
        """** No parameters are sensor reading arrays **

        Returns a temperature (deg F) from a Weather Underground station.
        'stn' is the primary station to use.  'stn2' is a backup station.
        """
        obs = internetwx.getWUobservation( [stn, stn2] )
        temp_val = float(obs['temp_f'])
        if temp_val>-120.0 and temp_val < 150.0:
            return [int(time.time())], [temp_val]
        else:
            return [], []

    def getWUwindSpeed(self, stn, stn2=None):
        """** No parameters are sensor reading arrays **

        Returns a wind speed (mph) from a Weather Underground station.
        'stn' is the primary station to use.  'stn2' is a backup station.
        """
        obs = internetwx.getWUobservation( [stn, stn2] )
        wind_val = float(obs['wind_mph'])
        if wind_val >= 0.0 and wind_val < 150.0:
            return [int(time.time())], [wind_val]
        else:
            return [], []
    
    def runtimeFromOnOff(self, onOffID, runtimeInterval=30):
        """** No parameters are sensor reading arrays **

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
        for rec in self.db.rowsForOneID(onOffID, start_tm=last_ts - 7200):
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
