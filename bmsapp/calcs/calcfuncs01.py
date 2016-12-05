"""One set of functions for calculated readings.
"""

import time
import math
import pandas as pd
import calcreadings
import internetwx
import aris_web_api
import sunny_portal

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
