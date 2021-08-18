'''
Utilities used in the data analysis used to produce data for charts and reports.
'''

from datetime import datetime
import pytz, calendar, time, math
from dateutil import parser
import numpy as np
import pandas as pd
from django.conf import settings


# Default timezone used when a datetime value needs to be created
default_tz = pytz.timezone(getattr(settings, 'TIME_ZONE', 'US/Alaska'))

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
    try:
        if val != int(val):
            return float('%.4g' % val)
        else:
            return val
    except:
        return None

def decimals_needed(vals, sig_figures):
    '''Returns the number of digits past the decimal needed to ensure
    that 'sig_figures' significant figures are displayed for the largest
    value (in absolute value terms) in the array of values 'vals'. 
    '''
    if len(vals):
        max_val = max(abs(min(vals)), abs(max(vals)))
        if max_val != 0:
            return max(0, sig_figures - int(math.log10(max_val)) - 1)
        else:
            return 0
    else:
        # No values in the array, just return 0.
        return 0

def formatCurVal(val):
    """
    Helper function for formatting current values to 3 significant digits, but 
    avoiding the use of scientific notation for display.  Also, integers are
    shown at full precision.
    """
    if val is None:
        return ''
    elif val == int(val):
        return '{:,}'.format(int(val))
    elif abs(val) >= 1000.0:
        return '{:,}'.format( int(float('%.4g' % val)))
    else:
        return '%.4g' % val

def histogram_from_series(pandas_series):
    '''
    Returns a list of histogram bins ( [bin center point, count] ) for the Pandas
    Time Series 'pandas_series'.  The values of the series (index not involved) are used
    to create the histogram.  The histogram has 30 bins.
    '''

    cts, bins = np.histogram(pandas_series.values, 20)   # 20 bin histogram
    avg_bins = (bins[:-1] + bins[1:]) / 2.0       # calculate midpoint of bins

    # round these values for better display in charts
    avg_bins = [round4(x) for x in avg_bins]

    # Convert count bins into % of total reading count
    reading_ct = float(sum(cts))
    cts = cts.astype('float64') / reading_ct * 100.0
    cts = [round4(x) for x in cts]

    # weirdly, some integer are "not JSON serializable".  Had to 
    # convert counts to float to avoid the error.  Also, round bin average
    # to 4 significant figures
    return list(zip(avg_bins, cts))

def resample_timeseries(pandas_dataframe, averaging_hours, use_rolling_averaging=False, drop_na=False, interp_method='pad'):
    '''
    Returns a new pandas dataframe that is resampled at the specified "averaging_hours"
    interval.  If the 'averaging_hours' parameter is fractional, the averaging time 
    period is truncated to the lesser minute.
    If 'drop_na' is True, rows with any NaN values are dropped.
    
    For some reason the pandas resampling sometimes fails if the datetime index is timezone aware...
    '''

    interval_lookup = {
        0.5: {'rule':'30min', 'loffset': '15min'}, 
        1: {'rule': '1H', 'loffset': '30min'},
        2: {'rule': '2H', 'loffset': '1H'},
        4: {'rule': '4H', 'loffset': '2H'},
        8: {'rule': '8H', 'loffset': '4H'},
        24: {'rule': '1D', 'loffset': '12H'},
        168: {'rule': '1W', 'loffset': '108H'},
        720: {'rule': '1M', 'loffset': '16D'},
        8760: {'rule': 'AS', 'loffset': '6M'}
        }
    params = interval_lookup.get(averaging_hours, {'rule':str(int(averaging_hours * 60)) + 'min', 'loffset':str(int(averaging_hours * 30)) + 'min'})

    if not use_rolling_averaging:
        # apply averaging weighted by duration
        dfResampled = weighted_resample_timeseries(pandas_dataframe,params['rule'],params['loffset'],interp_method)

    else:
        # apply rolling averaging
        dfResampled = pandas_dataframe.sort_index().rolling(str(int(averaging_hours * 60)) + 'min').mean()
        dfResampled = dfResampled[pandas_dataframe.index.min() + pd.tseries.frequencies.to_offset(params['rule']):]
    
        # offset the index label to the center of each period
        dfResampled.index = dfResampled.index - pd.tseries.frequencies.to_offset(params['loffset'])

    if drop_na:
        dfResampled = dfResampled.dropna()    

    return dfResampled

def weighted_resample_timeseries(pandas_dataframe, averaging, offset, interp_method='pad'):
    '''
    Returns a new pandas dataframe that is resampled at the specified
    interval. 
    '''

    # discard duplicate values in the index
    pandas_dataframe = pandas_dataframe[~pandas_dataframe.index.duplicated()]

    # insert new rows representing the breaks for each averaging period
    window_breaks = pandas_dataframe.resample(averaging, label='left').asfreq().shift(freq=pd.tseries.frequencies.to_offset('-1N'))
    window_breaks[:] = np.nan

    # calculate the average number of hours in the resampling periods
    averaging_hours = (window_breaks.index.to_series().diff() / pd.Timedelta(1,'hour')).mean()
    interp_limit = int(24 / averaging_hours) + 1 # limit interpolation to 24 hours or 1 averaging period

    # also create breaks that are shifted 1 day forward
    window_breaks_shifted = window_breaks.shift(freq='1D')
    window_breaks_shifted = window_breaks_shifted[window_breaks_shifted.index < pandas_dataframe.index.max()]
    window_breaks = window_breaks.append(window_breaks_shifted[~window_breaks_shifted.index.isin(window_breaks.index)])

    df = pandas_dataframe.append(window_breaks[~window_breaks.index.isin(pandas_dataframe.index)]).sort_index()

    # interpolate values
    df = df.interpolate(method=interp_method,limit=interp_limit)

    # calculate the 'duration' weights for each row and for each time period (based on difference from previous timestamp)
    value_duration = (df.index.to_series() - df.index.to_series().shift(1)) / pd.Timedelta(1,'hour')
    value_duration = value_duration.clip(lower=None,upper=24) # maximum weight = 24 hours

    # shift the dataframe index to place values at the end of each peiod
    df = df.shift(1)

    # multiply values by weights
    df = df.multiply(value_duration,axis='index')
    df['value_duration_weight'] = value_duration

    # discard the last datapoint (because the weight is unknown)
    df = df[:-1]

    # resample and calculate the weighted average for each time period
    dfResampled = df.resample(rule=averaging, closed='right', label='left').sum(min_count=1)
    dfResampled = dfResampled[pandas_dataframe.columns].div(dfResampled['value_duration_weight'],axis='index')
    
    if offset:
        # offset the index label to the center of each period
        dfResampled.index = dfResampled.index + pd.tseries.frequencies.to_offset(offset)

    return dfResampled

def decimate_timeseries(df,bin_count=1000,col=None):
    '''
    Decimates a dataframe to limit the maximum number of datapoints for plotting
    
    '''
    if len(df) > bin_count * 2:
        if col == None:
            # default to using the first column
            col = df.columns[0]

        # bin the index values
        bins = df.groupby(pd.cut(df.index,bins=bin_count,labels=np.arange(0,bin_count)).astype(int))

        # keep the max and min value in each bin
        maximums = df.loc[bins[col].idxmax()]
        minimums = df.loc[bins[col].idxmin()]

        return pd.concat([maximums,minimums]).drop_duplicates().sort_index()
    else:
        return df

def old_resample_timeseries(pandas_dataframe, averaging_hours, use_rolling_averaging=False, drop_na=True):
    '''
    Returns a new pandas dataframe that is resampled at the specified "averaging_hours"
    interval.  If the 'averaging_hours' parameter is fractional, the averaging time 
    period is truncated to the lesser minute.
    If 'drop_na' is True, rows with any NaN values are dropped.
    
    For some reason the pandas resampling sometimes fails if the datetime index is timezone aware...
    '''

    interval_lookup = {
        0.5: {'rule':'30min', 'loffset': '15min'}, 
        1: {'rule': '1H', 'loffset': '30min'},
        2: {'rule': '2H', 'loffset': '1H'},
        4: {'rule': '4H', 'loffset': '2H'},
        8: {'rule': '8H', 'loffset': '4H'},
        24: {'rule': '1D', 'loffset': '12H'},
        168: {'rule': '1W', 'loffset': '108H'},
        720: {'rule': '1M', 'loffset': '16D'},
        8760: {'rule': 'AS', 'loffset': '6M'}
        }
    params = interval_lookup.get(averaging_hours, {'rule':str(int(averaging_hours * 60)) + 'min', 'loffset':str(int(averaging_hours * 30)) + 'min'})

    if not use_rolling_averaging:
        new_df = pandas_dataframe.resample(rule=params['rule'], loffset=params['loffset'],label='left').mean()
    else:
        # resample to consistent interval
        original_interval = pandas_dataframe.index.to_series().diff().quantile(.05)
        new_df = pandas_dataframe.resample(rule=original_interval).median().ffill(limit=1)

        # apply the rolling averaging
        window_size = int(pd.Timedelta(hours=averaging_hours) / original_interval)
        new_df = new_df.rolling(window_size,center=True,min_periods=int(window_size * 0.75) + 1).mean()

        # downsample the result if there are more than 1000 values
        if len(new_df) > 1000:
            new_df = new_df.resample(rule=(pandas_dataframe.index[-1] - pandas_dataframe.index[0]) / 1000).mean()

    if drop_na:
        new_df = new_df.dropna()

    return new_df