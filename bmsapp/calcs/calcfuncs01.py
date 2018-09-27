"""One set of functions for calculated readings.
"""

import time
import math
from math import *      # make math functions available also without the math. qualifier
import logging
import pandas as pd
import numpy as np
import pytz
import calcreadings
import internetwx
import aris_web_api
import sunny_portal
import bmsapp.data_util
from bmsapp.models import Sensor, BldgToSensor

# Make a logger for this module
_logger = logging.getLogger('bms.' + __name__)

class CalcReadingFuncs_01(calcreadings.CalcReadingFuncs_base):
    """A set of functions that can be used to create calculated readings.  
    """
    
    def fluidHeatFlow(self, flow, Thot, Tcold, multiplier, heat_recovery=0.0):
        """** One or more parameters must be an array of sensor readings **

        Heat flow (power) in a fluid.  Inputs are flow rate of fluid, hot and cold
        temperatures and a multiplier.  A heat_recovery fraction can also
        be provided, which if greater than 0 will dimish the calculated heat flow.
        Any of these parameters can be passed to 'processCalc' as sensor IDs, as 
        array math is used in the calculation below.
        """
    
        # return the records to insert
        return flow * (Thot - Tcold) * multiplier * (1.0 - heat_recovery)

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

    def getInternetRH(self, stnCode):
        """** No parameters are sensor reading arrays **

        Returns a Relative Humidity value in % (0 - 100) from an NWS
        weather station.  Uses the August-Roche-Magnus approximation.
        Returns just one record of information, timestamped with the current time.
        """
        obs = internetwx.getWeatherObservation(stnCode)
        if obs.dewpt is not None and obs.temp is not None:
            dewpt = obs.dewpt.value()
            temp = obs.temp.value()
            RH = 100.0*(math.exp((17.625*dewpt)/(243.04+dewpt))/math.exp((17.625*temp)/(243.04+temp)))
            return [int(time.time())], [RH]
        else:
            # not info info available for calculation.
            return [], []

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
    
    def runtimeFromOnOff(self, onOffID, runtimeInterval=30, state_xform_func=None):
        """** No parameters are sensor reading arrays **

        Calculates runtime fraction data for a sensor having the id of 'onOffID' that produces
        On/Off state change values.  The state change values are either 0.0 (Turns Off) or 
        1.0 (Turns On).  The calculated runtime fractions vary from 0.0 to 1.0, indicating the 
        fraction of the time that the device was On in a particular time interval.  
        'runtimeInterval' is the width of the runtime intervals produced in minutes.
        If 'state_xform_func' is provided (not None), it will be applied to the 
        'onOffID' sensor values to convert them into 0.0 or 1.0 On/Off values; it is useful
        if the sensor values are *not* already 0.0 or 1.0.
        The timestamp returned for each interval is placed at the midpoint of the interval.  Records
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
            if state_xform_func:
                state.append(state_xform_func(rec['val']))
            else:
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

    def trueTimeAverage(self, sensorID, averageInterval=30):
        """** No parameters are sensor reading arrays **

        Calculates the time average of a sensor in a fashion that properly
        addresses readings that are not evenly spaced in time.  These unevenly spaced
        readings can occur when the sensor records values more frequently when the the
        sensor's value is changing.  A simple average of the sensor readings would
        oversample the readings that occur during the periods with a high rate of change
        of sensor readings.

        'sensorID' is the Sensor ID of the target sensor.  'averageInterval' is the 
        desired averaging interval expressed in minutes.
        
        The timestamp returned for each interval is placed at the midpoint of the interval.  Records
        are returned for times after the last stored runtime reading, subject to the reach_back
        constraint established in the constructor of this class.

        The required calculation algorithm is identical to that used in the 'runtimeFromOnOff'
        function.  So that function is simply called from this function.
        """
        self.runtimeFromOnOff(sensorID, runtimeInterval=averageInterval)

    def lastCount(self, sensorID):
        """Returns the last raw count from a sensor that has been set up to
        store a counter rate of change; i.e. a sensor that uses the "rate"
        transform function.
        'sensorID' is the Sensor ID of the sensor that is currently set up
            to store the counter rate of change (it uses a transform function
            using the 'rate' variable).
        """
        last_ts, last_val = self.db.last_raw(sensorID)
        if last_ts:
            return [last_ts], [last_val]
        else:
            return [], []

    def OkoValueFromStatus(self, statusID, value=1.0):
        """Converts Okofen Boiler Status values into Pellet Consumption
        of Heat output values.  When the Boiler status value is 5 or 6
        the boiler is consuming pellets and producing output.  This function
        returns a set of 5 minute average pellet consumption or output values
        based on those status values.
        The 'statusID' parameter is the Sensor ID giving the boiler Status.
        The 'value' parameter is the pellet consumption rate or heat output
        rate that occurs when status is 5 or 6.
        Note: this function is somewhat complicated because it does not just 
        provide a consumption point for each Status value, because the Status
        values are *not* evenly spaced in time; Status values are produced at
        every state change or every 10 minutes, whichever comes first.  To determine
        average pellet use or heat output, it is important to consider is uneven
        spacing of Status values, which this function does.
        """
        # function to convert a status of 5 or 6 to a value of 1.0
        convert_func = lambda x: 1.0 if x==5.0 or x==6.0 else 0.0

        # Use the Runtime from On/Off function to get 5 minute average runtime averages
        tstamps, vals = self.runtimeFromOnOff(statusID, 5, convert_func)
        # convert runtime averages to the desired consumption rate
        vals = vals * value

        return tstamps, vals

    def getUsageFromARIS(self,
                         building_id,
                         energy_type_id,
                         energy_parameter='EnergyQuantity',
                         energy_multiplier=1,
                         expected_period_months=1):
        """** No parameters are sensor reading arrays **

        Returns energy use via the ARIS web API
        """

        # determine the timestamp of the last update that was read for this sensor.
        last_ts, last_val = self.db.replaceLastRaw(self.calc_id, 0, 0)
        if last_ts is None:
            last_ts = 0

        # Retrieve the data from ARIS
        update_ts, timestamp_list, values_list = aris_web_api.get_energy_use(building_id,
                                                                             energy_type_id,
                                                                             last_ts,
                                                                             energy_parameter,
                                                                             energy_multiplier,
                                                                             expected_period_months)
        # print 'Updating '+ str(len(timestamp_list)) + ' values for ' + str(self.calc_id)

        # Update the last update timestamp for the sensor
        self.db.replaceLastRaw(self.calc_id, update_ts, 0)

        # return the timestamps and runtime values
        return timestamp_list, values_list

    def getSunnyPortalData(self,
                           plant_id,
                           plant_tz='US/Alaska',
                           menu_text='Energy and Power',
                           fill_NA=False,
                           graph_num=None
                           ):
        """Retrieves detailed time-resolution power production data from a Sunny
        Portal PV system.

        Parameters
        ----------
        plant_id:  The Plant ID of the system to retrieve in the Sunny Portal system.
        plant_tz:  The Olson timezone database string identifying the timezone
            that is used for the plant on the Sunny Portal.
        menu_text: text that occurs in the title attribute of the menu item in
            the left navigation bar; this menu item should bring up the desired
            Power graph.
        fill_NA: If fill_NA is False (the default), Power values that are blank
            are not posted, because these are time slots that have not occurred yet.
            But, for some systems, the Power value is left blank when the power
            production is 0.  Setting fill_NA to True will cause these blank power
            values to be changed to 0 and posted.
        graph_num: On the page containing the desired Power graph, sometimes multiple
            graphs will appear.  If so, this parameter needs to be set to 0 to use
            the first graph on the page, 1 for the second, etc.  If there is only one
            graph on the page, this parameter must be set to None.

        Returns
        -------
        Data from the current day and the day prior are returned.  The return type
        is a two-tupe with the first item being a list of timestamps and the second
        being a list of reading values.
        """
        return sunny_portal.get_data(plant_id,
                                     plant_tz=plant_tz,
                                     menu_text=menu_text,
                                     fill_NA=fill_NA,
                                     graph_num=graph_num
                                     )

    def genericCalc(self,
                    A,   # required
                    B=None,
                    C=None,
                    D=None,
                    E=None,
                    expression='',
                    averaging_hours=None,
                    rolling_average=False,
                    time_label='center'):
        """Calculates a set of sensor readings based on other sensor readings. 
        Up to 5 different sensors can be used in the calculation.  The calculation 
        is expressed in terms of the variables: A, B, C, D, and E corresponding to the 
        5 sensors, and the expression is passed into this method in the parameter
        
        'expression'.  'A / B * 0.023' is an example of an expression. The input
        parameters A through E give the Sensor IDs of the sensor used in the calculation. 
        
        'averaging_hours' if present specifies the time averaging interval in hours
        that is applied before the calculation occurs.  A reading is computed for each
        distinct time period spanning 'averaging_hours'.
        For purposes of deciding where time-averaging bin boundaries occur, timestamps
        are expressed in the timezone of the first building associated with sensor A.
        For example, with 24 hour averaging, boundaries will be Midnight to Midnight
        in the timezone of sensor A.

        If there is no 'averaging_hours' specified, interpolation is used to determine 
        B through E readings that align with the Sensor A timestamps, and a new calculated
        reading is returned for each Sensor A timestamp.

        'rolling_average': If set to True, a rolling average is computed for each
        of the sensor values before the 'expression' is calculated.  For this rolling
        average, the time period used is given by the 'averaging_hours' parameter.  
        Fractional hours are truncated to the lesser minute. A calculated reading is
        returned for each timestamp that occurs for sensor A.  So, the calculated reading
        for a particular timestamp ts will encompass sensor values that occur in the
        interval of (ts - averaging_hours) to ts.

        'time_label': This parameter determines where the timestamp is placed when
        averaging is requested (both types of averaging, rolling or standard).
        The valid values are 'left', 'right', 'center' (the default). 'center', the
        default, places the timestamp at the center of the averaging period. 'left' places
        the timestamp at the left (earliest) edge of the interval. 'right' places it
        at the right (latest) edge of the interval.
        
        This routine only returns calculated values for timestamps after the last
        calculated readings stored in the reading database.
        """

        # determine the timestamp of the last entry in the database for this calculated field.
        last_calc_rec = self.db.last_read(self.calc_id)
        last_ts = int(last_calc_rec['ts']) if last_calc_rec else 0   # use 0 ts if no records
        
        # constrain this value to greater or equal to 'reach_back'
        last_ts = max(last_ts, int(time.time() - self.reach_back))

        # IDs and variable names
        sensors = ((A, 'A'), (B, 'B'), (C, 'C'), (D, 'D'), (E, 'E'))
        sensor_ids = []
        col_names = []
        for sensor_id, var in sensors:
            if sensor_id:
                sensor_ids.append(sensor_id)
                col_names.append(var)

        # if time averaging is requested, do that, otherwise interpolate readings to 
        # match Sensor A timestamps.
        if averaging_hours > 0 and not rolling_average:
            # get the timezone of the first building associated with Sensor 'A'.
            A_sensor = Sensor.objects.filter(sensor_id = A)
            try:
                bl_sens_link = BldgToSensor.objects.filter(sensor=A_sensor)[0]    # First building associated with Sensor
                tz_name = bl_sens_link.building.timezone
                tz = pytz.timezone(tz_name)
            except:
                # there may be no buildings associated with the sensor; if so an error
                # will be thrown and we'll use no timezone.
                tz = None
            # get a Dataframe with all the sensor data
            df = self.db.dataframeForMultipleIDs(sensor_ids, col_names, start_ts=last_ts, tz=tz)
            df = bmsapp.data_util.resample_timeseries(df, averaging_hours, drop_na=True)
            
            # Drop the last row as it is probably a partial interval
            df = df[:-1]

            # Convert the index back to UTC naive
            df.index = df.index.tz_localize(tz).tz_convert('UTC').tz_localize(None)

        else:
            # get a dataframe with the all the sensors.  Index is naive UTC.
            # Go back enough time before the last calculated timestamp so that a proper
            # rolling average can be calculated (if requested); if a rolling average is
            # not requested, provide enough readings so an interpolation can be performed.
            go_back = averaging_hours * 3600 if averaging_hours else 3600
            df = self.db.dataframeForMultipleIDs(sensor_ids, col_names, start_ts=last_ts-go_back)

            # interpolate values of B through D sensors, and then drop rows that
            # have any NAs (mostly rows where A sensor is NA, but also could be
            # leading and trailing NA rows for other sensors where interpolation 
            # was not possible).
            for col in col_names:
                if col != 'A':
                    # the limit parameters make sure trailing NaN's are *not* filled by interpolation
                    df[col] = df[col].interpolate(method='index', limit=10, limit_direction='backward')

            # drop the rows that have NaN values
            df = df.dropna()

        if averaging_hours > 0 and rolling_average:
            # compute the rolling average of sensor values. The averaging interval is given
            # by 'averaging_hours' but truncated to the lesser minute.
            df = df.rolling('%smin' % int(averaging_hours * 60)).mean()

        #import ipdb; ipdb.set_trace()

        # convert the index back to integer Unix timestamps.
        df.index = df.index.astype(np.int64) // 10**9

        # put the timestamp in requested place if averaging occurred
        if averaging_hours > 0:
            if rolling_average:
                # prior to adjustment, stamp is at right edge
                adj = {'left': -averaging_hours * 3600,
                       'center': -averaging_hours * 3600 * 0.5,
                       'right': 0.0}
            else:
                # prior to adjustment, stamp is at the center
                adj = {'left': -averaging_hours * 3600 * 0.5,
                       'center': 0.0,
                       'right': averaging_hours * 3600 * 0.5}
            df.index += adj.get(time_label, adj['center'])    # default to center if bad parameter

        # only keep rows that are for timestamps after the last timestamp for 
        # this calculated field.
        df = df[df.index > last_ts]

        # walk the rows, calculating the expression and adding timestamps and values to the list
        ts = []
        vals = []
        # delete these paramter values as we are using these variables below
        del A, B, C, D, E
        for ix, row in df.iterrows():

            # Get the variables that are part of the expression
            A = row['A'] if 'A' in row else None
            B = row['B'] if 'B' in row else None
            C = row['C'] if 'C' in row else None
            D = row['D'] if 'D' in row else None
            E = row['E'] if 'E' in row else None
            
            # Evaluate the expression on these variables and append to value list
            try:
                vals.append(float(eval(expression)))
                ts.append(int(ix))
            except:
                # if an evaluation error occurs, just don't add anything to the list
                _logger.warning('Error calculating %s with inputs %s' % (self.calc_id, row))

        return ts, vals

