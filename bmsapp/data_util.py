'''
Utilities used in the data analysis used to produce data for charts and reports.
'''

from datetime import datetime
import pytz, calendar, time
from dateutil import parser
import numpy as np

# Default timezone used when a datetime value needs to be created
default_tz = pytz.timezone('US/Alaska')

def ts_to_datetime(unix_ts=time.time(), tz=default_tz):
    '''
    Converts a UNIX timestamp (seconds) to a Python datetime object in a
    particular timezone.  The timezone info is stripped from the returned
    datetime to make it naive, which works better with the Pandas library
    '''
    return datetime.fromtimestamp(unix_ts, tz).replace(tzinfo=None)

def datestr_to_ts(datestr, tz=default_tz):
    '''
    Converts a date/time string into a Unix timestamp, assuming the date/time is expressed
    in the timezone 'tz'.
    '''
    dt = parser.parse(datestr)
    dt_aware = tz.localize(dt)
    return calendar.timegm(dt_aware.utctimetuple())

def round4(val):
    '''
    Rounds a number to a 4 significant digits, unless it is an integer.
    '''
    if val != int(val):
        return float('%.4g' % val)
    else:
        return val

class TsBin:
    '''
    Class to determine a timestamp bin value (UNIX seconds) for purposes of time-averaging
    data.  Bins are aligned to the start of a Monday, standard time, in the requested timezone.
    No accounting of daylight savings time occurs for establishment of the bins.
    '''

    def __init__(self, bin_width, tz=default_tz):
        '''
        'bin_width' is the bin width in hours.
        '''
        self.bin_wid_secs = bin_width * 3600.0  # bin width in seconds

        # determine a reference timestamp that occurs at the start of a bin boundary for all
        # binning widths.  That would be a Monday at 0:00 am.
        ref_dt = tz.localize(datetime(2013, 1, 7))
        self.ref_ts = time.mktime(ref_dt.timetuple())

    def bin(self, ts):
        '''
        Returns the bin midpoint for 'ts' in Unix seconds.
        '''
        bin_int = int((ts - self.ref_ts) / self.bin_wid_secs)
        return bin_int * self.bin_wid_secs + self.bin_wid_secs * 0.5 + self.ref_ts

def histogram_from_series(pandas_series):
    '''
    Returns a list of histogram bins ( [bin center point, count] ) for the Pandas
    Time Series 'pandas_series'.  The values of the series (index not involved) are used
    to create the histogram.  The histogram has 30 bins.
    '''

    cts, bins = np.histogram(pandas_series.values, 20)   # 20 bin histogram
    avg_bins = (bins[:-1] + bins[1:]) / 2.0       # calculate midpoint of bins

    # round these values for better display in Highcharts
    avg_bins = [round4(x) for x in avg_bins]

    # Convert count bins into % of total reading count
    reading_ct = float(sum(cts))
    cts = cts.astype('float64') / reading_ct * 100.0
    cts = [round4(x) for x in cts]

    # weirdly, some integer are "not JSON serializable".  Had to 
    # convert counts to float to avoid the error.  Also, round bin average
    # to 4 significant figures
    return zip(avg_bins, cts)
