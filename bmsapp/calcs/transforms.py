﻿'''
Transform functions for scaling and transforming sensor readings
'''


from math import *
import sys
import logging
import yaml

from bmsapp import models

# Make a logger for this module
_logger = logging.getLogger('bms.' + __name__)


class Transformer:

    def __init__(self, db=None):
        '''
        Creates Transforms object.  'db' is the a bmsdata.BMSdata object that gives
        gives access to the reading database, as some of the transform functions
        need that access. 
        '''

        # store database as an object variable
        self.db = db


    def transform_value(self, ts, id, val, trans_func, trans_params):
        '''
        Returns transformed sensor reading information, using a transformation
        function identified by the string trans_func, and additional parameters to that function
        given by the string 'trans_params'.  That string is in YAML format and must
        convert to a Python dictionary.
        All three elements of the reading--ts, id, and val--can be transformed by the function.
        '''
        
        params = yaml.load(trans_params, Loader=yaml.FullLoader)
        if params is None:
            params = {}    # substitute an empty dictionary for empty parameter string
        if hasattr(self, trans_func.strip()):
            the_func = getattr(self, trans_func.strip())
            return the_func(ts, id, val, **params)
        else:
            # the transform must be a general expression.
            return self._eval_expression(ts, id, val, trans_func, **params)
            
    def _eval_expression(self, ts, id, val, expression, 
                         rollover=2**16,
                         max_rate=5.0,
                         min_interval=30,
                         ignore_zero=True,
                         ignore_negative=True):
        """Returns ts, id, and val transformed by the expression 'expression'.
        If invalid conditions occur, None values are returned.
        The expression can use any variables and functions visible to this 
        method.  Mostly, this will be 'val', the raw value passed into the 
        function.  Floating point division is always done with the expression,
        due to importing 'division' from '__future__'.  The 'math' module was 
        imported above as well, giving the expressions access to many math
        functions.
        
        An expression can also use the variable 'rate', which forces
        this routine to interpret the 'val' reading as cumulative counter 
        reading. 'rate' is then calculated to be the count per second that has
        occurred since the last time this method received a reading for the 
        sensor 'id'.  Additional optional parameters affect this calculation.
        Counters with rollover are addressed by the 'rollover' parameter, 
        indicating the count they rollover at.  'max_rate' is the maximum count 
        rate in counts/second that is considered valid.  'min_interval' is the
        minimum time in seconds between the current and prior read that is
        considered valid. 'ignore_zero' indicates whether a counter value of
        zero should be ignored, probably because it was generated by a reset of
        the sensor and therefore is not a legitimate value (defaults to True).
        'ignore_negative' indicates whether a negative change should be ignored.
        """
        expr_clean = expression.strip().lower()
        
        if 'rate' in expr_clean:

            # add the raw count to a raw count table associated with this sensor; thus there 
            # will be two tables--a table with a counter rate related value and this table that
            # stores raw counts.  The raw count table will have the passed in sensor ID with a
            # "_raw" appended to it.  Also, make sure to apply a transform if one is set up for
            # the "_raw" sensor
            raw_id = id + '_raw'
            val_conv = val          # default is no transform of the value

            # get the Sensor object, if available, to see if there is a transform function to apply
            # to the raw count
            sensors = models.Sensor.objects.filter( sensor_id=raw_id )
            if len(sensors) > 0: 
                # look at the first sensor (there only should be one).  Don't do a transform if this
                # is a calculated field
                if not sensors[0].is_calculated:
                    transform_func = sensors[0].tran_calc_function
                    transform_func = transform_func.strip().lower()
                    if len(transform_func):
                        val_conv = eval(transform_func)

            self.db.insert_reading(ts, raw_id, val_conv)

            # Done with the absolute count value, move on to the rate calculation.

            # A count rate is used in the expression.  Determine it so the
            # expression can be evalulated.
            # Get the last raw reading with timestamp, and replace it with
            # this newer reading.
            last_ts, last_val = self.db.replaceLastRaw(id, ts, val)
            
            # Check for a zero value that should be ignored
            if val==0 and ignore_zero:
                _logger.warn('Counter value is zero and requested to be ignored: ts=%s, id=%s, val=%s' % (ts, id, val))
                return None, None, None
                
            if last_ts:
                
                interval = ts - last_ts
                count_chg = val - last_val
                
                if interval < min_interval:
                    # too short of an interval for valid reading
                    _logger.warn('Too short of interval to calculate rate: ts=%s, last_ts=%s, id=%s, val=%s' % (ts, last_ts, id, val))
                    return None, None, None

                # Calculate the rate of change in units/second
                rate = count_chg / float(interval)

                if count_chg < 0:
                    # Counter moved backward.  Either this is a legitimate negative change or a rollover.
                    if ignore_negative:
                        # negative changes are not proper, assume this is a rollover
                        count_chg += rollover
                        rate = count_chg / float(interval)
                    else:
                        # This could be a legit negative value. But, if the rate of change exceeds the max_rate
                        # then treat it as a rollover instead.
                        if abs(rate) > max_rate:
                            count_chg += rollover
                            rate = count_chg / float(interval)
                    
                if abs(rate) > max_rate:
                    # calculated rate is too high, indicates invalid reading.
                    _logger.warn('Too high of counter rate: ts=%s, id=%s, val=%s, rate=%s' % (ts, id, val, rate))
                    return None, None, None
                
                # Stamp the reading at the average of the current and last
                # timestamp.
                return int((ts + last_ts)/2.0), id, eval(expr_clean)
                
            else:
                # there was no last reading in database
                _logger.warn('No last reading available to determine rate: ts=%s, id=%s, val=%s' % (ts, id, val))
                return None, None, None
            
        else:
            # Just a simple transformation of the value
            return ts, id, eval(expr_clean)
        

    # ******** Add Transform Functions below Here *********
    #
    # Transform functions must accept the ts, id, and val components of the sensor reading
    # as the first three function parameters after self.  The functions must return the same
    # three values, transformed.  Any of the three values can be transformed by the function.

    def linear(self, ts, id, val, slope=1.0, offset=0.0):
        '''Linear transformation of value'''
        return ts, id, val * slope + offset


    def count_rate(self, ts, id, val, typical_minutes=30.0, slope=1.0, offset=0.0, no_zero_after_link=True):
        '''
        Determines the rate/second of the count value 'val'.  Assumes the 'val' count
        occurred since the last reading in the database for this sensor (i.e. count readings are reset
        after each read).  After determining
        the rate per second, 'slope' and 'offset' are used to linearly scale that value.  
        If there is no readings in the database for this sensor,
        this function assumes the interval is 'typical_minutes' long and calulates a rate based on
        that.  If the interval between this reading and the last is different than typical_minutes by
        more than 10%, the best interval to use is determined in the code below.
        If 'no_zero_after_link' is True, then a zero count value is rejected if the sensor has not reported
        for four or more 'typical_minutes'.  This feature is present because Monnit sensors report a 0 
        after having been asleep in link mode.  This routine substitutes the last reading value for the zero
        value reported by the sensor.
        '''

        # for convenience, translate typical_minutes into seconds
        typ_secs = typical_minutes * 60.0

        # First, transform the timestamp to approximately the center of the read interval, since the
        # count has occurred across the read interval and a mid-point timestamp is more appropriate.
        # Use typ_secs to do this translation, not the actual interval, because we want to the use the
        # same translation for every reading so that differences between readings are not distorted.
        new_ts = ts - typ_secs * 0.5

        # get the last reading for this sensor
        last_read = self.db.last_read(id)
        if last_read:

            # calculate interval between current read and last.  Override the interval if
            # is more than 10% different from the typical interval.
            interval = new_ts - float(last_read['ts'])    # last read has a mid-point ts already

            if no_zero_after_link and (interval >= 0.9 * 4.0 * typ_secs) and val==0.0:   # 0.9 to account for timing inaccuracy
                # sensor was probably in link mode; use the last reading
                return new_ts, id, last_read['val']

            elif interval / typ_secs < 0.9:
                # interval is substantially shorter than standard one, probably a doubled up transmission.  
                # Just use the last reading value.
                return new_ts, id, last_read['val']

            elif interval / typ_secs > 1.1:
                # interval is longer than standard interval.  This could be a reboot, a missed prior
                # transmission, etc.  So, its not clear what the interval is, but it has to be a multiple 
                # of heartbeat.  Use the typical seconds value as the heartbeat, and try multiples of the
                # heartbeat up to 4.  Use the one that yields the closest value to the last value

                # track the minimum deviation from the last value.
                # initialize to a large deviation.
                min_dev = sys.float_info.max
                for mult in range(1, 5):
                    test_val = slope * val / (mult * typ_secs) + offset
                    deviation = abs(test_val - last_read['val'])
                    if deviation < min_dev:
                        min_dev = deviation
                        best_val = test_val
                
                return new_ts, id, best_val

        else:
            # no prior reading, so use the typical heartbeat value to calculate pulse rate.
            interval = typ_secs

        # calculate count/sec and apply slope and offset
        return new_ts, id, (slope * val / interval  + offset)


    # ******** End of Transform Function Section **********
