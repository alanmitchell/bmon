'''
Transform functions for scaling and transforming sensor readings
'''

import sys

def makeKeywordArgs(keyword_str):
    '''
    Turns a string that looks like a set of keyword arguments into a dictionary of those
    arguments.  Numbers are converted to floats, except the 'id_' exception mentioned below.
    Boolean are created if the text looks like a boolean.  Otherwise a string is created as 
    the value.  There is a special exception for keyword names that start with the string 'id_':
    these are always converted to strings.  This conveniently allows sensor ids to be entered 
    without quotes in parameter lists.
    '''
    result = {}
    keyword_str = keyword_str.strip()
    # need to exit if this is a blank string
    if len(keyword_str)==0:
        return result

    for it in keyword_str.strip().split(','):
        kw, val = it.split('=')
        kw = kw.strip()
        val = val.strip()
        if kw.startswith('id_'):
            # special case of keyword starting with 'id_'.  Assume val is a string
            # and strip any surrounding quotes of both types.
            val = val.strip('"\'')
        else:
            try:
                val = float(val)
            except:
                if val in ('True', 'true', 'Y', 'y', 'Yes', 'yes'):
                    val = True
                elif val in ('False', 'false', 'N', 'n', 'No', 'no'):
                    val = False
                else:
                    # must be a string.
                    # get rid of surrounding quotes of both types.
                    val = val.strip('"\'')

        result[kw] = val

    return result


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
        given by the string 'trans_params'.  That string is in keyword format, like "abc=23.3, xyz=True".
        All three elements of the reading--ts, id, and val--can be transformed by the function.
        '''
        the_func = getattr(self, trans_func.strip())
        params = makeKeywordArgs(trans_params)
        return the_func(ts, id, val, **params)


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


# ------------ Test functions --------------

def test_kw():
    '''
    Test function for makeKeywordArgs.
    '''

    print makeKeywordArgs('abc=True, xyz=23.3, jlk="Hello"')
    print makeKeywordArgs("abc=Yes, xyz=23.3, jlk='Hello'")
    print makeKeywordArgs("abc=Yes, xyz=23.3, jlk=Hello")

