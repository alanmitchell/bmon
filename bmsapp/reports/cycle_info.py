"""Creates Report analyzing cycle length and info.
"""
from collections import namedtuple
from django.template import loader
import pandas as pd
import numpy as np
import bmsapp.models
from bmsapp.data_util import formatCurVal
import basechart


def find_cycles(df_in):
    """Finds the On/Off cycles in a DataFrame of sensor readings.

    Parameters
    ----------
    df_in: Pandas DataFrame of sensor readings, having a 'ts'
        timestamp column and a 'val' column.  The 'val' column
        normally contains values of 1 or 0 representing On and Off.
        If the 'val' column contains something other than 1s and 0s,
        it is converted to 1s and 0s by determining a threshold midway
        between the minimum 'val' and maximum 'val', and classifying all
        vals above the threshold as 1 and the rest as 0.

    Returns
    -------
    A three tuple:
        * A DataFrame with a row for each complete cycle; cycles at the
            beginning or end of the data set where the start or finish
            of the cycle is unknown are *not* included.  Columns in the
            DataFrame are 'start': timestamp of cycle start, 'end':
            timestamp of cycle end, 'cycle_len': length of the cycle in
            minutes.
        * A copy of the input DataFrame with 'val' transformed if it was not
            1s and 0s.  Also a 'v_diff' colmun is added which has the difference
            in 'val' relative to the prior reading.
        * Notes that give info about the 'val' transformation, if it occurred.
    """
    df = df_in.copy()

    # variable to accumulate notes to return from function
    notes = ''

    # check to see whether all of the values are either 0.0 or 1.0.
    # If not, find a midpoint threshold and use that to translate
    # analog values to 0.0 or 1.0
    if not set(df.val.values).issubset({0.0, 1.0}):
        midpoint = (df.val.max() + df.val.min()) / 2.0
        df['val'] = (df.val > midpoint) * 1.0
        notes += '  Values were converted to On/Off states using a threshold of %s.' % formatCurVal(midpoint)

    df['v_diff'] = df.val.diff()
    starts = df[df.v_diff == 1.0]
    ends = df[(df.v_diff == -1.0)]
    if not starts.empty:
        ends = ends[ends.ts > starts.ts.values[0]]

    df_cycles = pd.DataFrame({'start': starts.ts.values[:len(ends)], 'end': ends.ts.values})
    df_cycles['cycle_len'] = (df_cycles.end - df_cycles.start) / 60.0  # in minutes

    return df_cycles, df, notes

def NaNtoNone(val):
    """ Returns 'val' unless it is NaN, and then returns None.
    """
    return None if np.isnan(val) else val

def analyze_cycles(df_in):
    """Summarizes the On/Off cycles present in a DataFrame of sensor readings.

    Parameters
    ----------
    df_in: Pandas DataFrame structured as described in the documentation for the
        find_cycles() function above.

    Returns
    -------
    A three tuple of:
        * A DataFrame with a row for each complete Cycle in the input DataFrame.
            See further description in the find_cycles() function.
        * A named tuple with a number of summary statistics about the cycles
            in the data set.
        * A string of Notes about any transform of the input data that may have
            occurred.
    """

    # make a DataFrame showing all of the complete cycles, not counting
    # partial cycles at beginning and end of data set.
    df_complete_cycles, df_transformed, notes = find_cycles(df_in)

    # now make a dataframe including the possible partial cycles at beginning
    # and end of data set.  Use this for calculating runtime
    if not df_in.empty:
        df_full = pd.concat([pd.DataFrame({'ts': [df_in.ts.values[0]], 'val': [0]}),
                             df_in,
                             pd.DataFrame({'ts': [df_in.ts.values[-1]], 'val': [0]})],
                            ignore_index=True)
    else:
        df_full = df_in.copy()

    df_cycles_w_partial, _, _ = find_cycles(df_full)

    # create some named tuples to hold statistics results
    Stats = namedtuple('Stats', 'mean min max')
    CycleStats = namedtuple('CycleStats', 'runtime cycle_length cycles_per_hour')

    # --- Determine average runtime percentage
    try:
        runtime = Stats(df_cycles_w_partial.cycle_len.sum() * 60.0 / float(df_in.ts.values[-1] - df_in.ts.values[0]),
                        None,
                        None)  # only use the mean element; no min and max
    except:
        runtime = Stats(None, None, None)

    # --- Cycle Length stats; only complete cycles
    if not df_complete_cycles.empty:
        cycle_length = Stats(df_complete_cycles.cycle_len.mean(),
                             df_complete_cycles.cycle_len.min(),
                             df_complete_cycles.cycle_len.max())
    else:
        cycle_length = Stats(None, None, None)

    # --- Determine cycles per hour
    # Start with the transformed input dataframe; this differs from the input
    # dataframe only if analog values were converted to On/Offs.
    df_starts = df_transformed.copy()

    # This is the default mean cycles/hour that will be used if an Error occurs
    # when calculating. An empty dataframe will cause an error.
    mean_cyc_p_hr = None

    try:
        df_starts['starts'] = (df_starts.v_diff == 1.0) * 1.0  # make column with 1's when a cycle starts

        # Calculate the mean cycles/hour from the whole set of records
        mean_cyc_p_hr = NaNtoNone(
            df_starts.starts.sum() * 3600.0 / (df_in.ts.values[-1] - df_in.ts.values[0])
        )

        # Use a rolling sum to find the 1 hour periods with the minimum and maximum starts.
        df_starts.index = df_starts.ts.astype('datetime64[s]')
        df_starts.drop(['ts', 'val', 'v_diff'], axis=1, inplace=True)
        df_starts_1H = df_starts.rolling('1H').sum()

        # The rolling sum does not include a full hour for the first values
        # in the dataframe.  So, we need to ignore the records in the first
        # hour.
        min_ts = df_starts.index[0] + pd.DateOffset(hours=1)
        df_starts_1H = df_starts_1H[df_starts_1H.index >= min_ts]
        min_cyc_p_hr = NaNtoNone(df_starts_1H.starts.min())
        max_cyc_p_hr = NaNtoNone(df_starts_1H.starts.max())
        cycles_per_hour = Stats(mean_cyc_p_hr,
                                min_cyc_p_hr,
                                max_cyc_p_hr)
    except:
        cycles_per_hour = Stats(mean_cyc_p_hr,
                                None,
                                None)

    cstats = CycleStats(runtime, cycle_length, cycles_per_hour)

    return df_complete_cycles, cstats, notes


class CycleInfo(basechart.BaseChart):
    """Class that creates Cycle Length Plot and other cycle-related statistics.
    """

    # see BaseChart for definition of these constants
    CTRLS = 'refresh, ctrl_sensor, time_period'

    def result(self):
        """
        Returns the HTML and chart object for the Cycle Length Analysis
        """

        # determine the sensor to plot from the sensor selected by the user.
        the_sensor = bmsapp.models.Sensor.objects.get(pk=self.request_params['select_sensor'])

        # determine the start time for selecting records
        st_ts, end_ts = self.get_ts_range()

        # get the database records
        df = self.reading_db.dataframeForOneID(the_sensor.sensor_id, st_ts, end_ts)

        # analyze the cycles
        df_cycles, stats, notes = analyze_cycles(df)

        chart_data = {'x': list(df_cycles.cycle_len.values),
                      'type': 'histogram',
                      'nbinsx': 40,
                     }

        opt = self.get_chart_options('plotly')
        opt['data'] = [chart_data]
        opt['layout']['title'] = 'Cycle Length Histogram'
        opt['layout']['xaxis']['title'] =  'Cycle Length in Minutes'
        opt['layout']['yaxis']['title'] =  'Number of Cycles'
        opt['layout']['showlegend'] = False
        opt['layout']['margin']['b'] = 60

        # context for template
        context = {}

        # create a report title
        context['report_title'] = 'On/Off Cycle Information: %s' % the_sensor.title

        if stats.runtime.mean is not None:
            context['runtime_avg'] = formatCurVal(stats.runtime.mean * 100.0)

        context['cycle_length_avg'] = formatCurVal(stats.cycle_length.mean)
        context['cycle_length_min'] = formatCurVal(stats.cycle_length.min)
        context['cycle_length_max'] = formatCurVal(stats.cycle_length.max)

        context['cycles_per_hour_avg'] = formatCurVal(stats.cycles_per_hour.mean)
        context['cycles_per_hour_min'] = formatCurVal(stats.cycles_per_hour.min)
        context['cycles_per_hour_max'] = formatCurVal(stats.cycles_per_hour.max)

        # Notes about statistical analysis
        context['notes'] = notes

        template = loader.get_template('bmsapp/cycle-info.html')

        return {'html': template.render(context), 'objects': [('plotly', opt)]}
