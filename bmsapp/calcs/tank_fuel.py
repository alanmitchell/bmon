#!/usr/bin/env python
# coding: utf-8

import pandas as pd
from pandas.tseries.frequencies import to_offset
from sklearn.linear_model import LinearRegression
import statsmodels.api as sm

# 'main()' function at bottom is the primary entry point to the module.

def clean_raw_data(df_raw):
    """Removes outliers from raw data and averages into consistent 15-minute data, filling in
    missing readings.  Duplicates the index as a 'ts' timestamp column as well.
    """

    # First make sure there is a temperature reading for each depth reading and then reduce
    # dataframe to just the rows having a depth value.
    df_raw['temp'] = df_raw.temp.interpolate(method='time')
    df_raw.dropna(inplace=True)

    # Fix outliers in depth column
    df_raw['depth'] = fix_depth_outliers(df_raw.depth, 0.2)   # 5 mm is 0.197 inches, so 0.2 keeps 5 mm and less changes

    # create consistent 15 minute data, using averages of depth and temperature.  For missing values after
    # averaging, backfill
    df1 = df_raw.resample('15min').mean()
    df1.index += to_offset('450s')     # timestamp middle of interval
    df2 = df1.reindex(pd.date_range(df1.index[0], df1.index[-1], freq='15min'))
    df2.fillna(method='bfill', inplace=True)

    # drop any remaining rows with NaNs (could only be at end)
    df = df2.dropna().copy()

    # put a timestamp column in the data
    df['ts'] = df.index
    
    return df

def fix_depth_outliers(ser_depth, max_valid_change):
    """Returns a Pandas Series of fuel depths that is the Series 'ser_depth' but with
    outliers fixed.  Outliers are identified by a reading-to-reading change (in absolute value) 
    greater than 'max_valid_change'.  An outlier is back-filled with the next valid reading.
    Fuel fills will be detected as outliers, and the back-filling technique will restore a reasonable
    value for those points.
    """
    # Fill outliers with NaNs based on excessive change between readings.  This also puts in a NaN 
    # where a fill occurred,since it is big change.  The fillna(0.0) component below forces the first
    # depth reading to be kept.
    ser_clean = ser_depth.where(ser_depth.diff().fillna(0.0).abs() <= max_valid_change)

    # backfill the NaNs so all data is present again, the fill points get a reasonable value (the high value
    # right after the fill)
    ser_clean = ser_clean.fillna(method='bfill')

    return ser_clean

def split_by_fill(df, min_fill_change):
    """Splits the DataFrame 'df' at the point of each tank fill. 'df' must have a 
    'depth' column that is the depth of fuel in the tank.  'min_fill_change' gives the
    minimum positive change in fuel depth that is considered a fill.
    The function returns a list of DataFrames, which are the original DataFrame split
    into pieces at each fill.
    """
    # find the fills
    fills = df.depth[df.depth.diff() >= min_fill_change]

    # break the DataFrame into pieces between the fills
    df_pieces = []      # list holding the smaller DataFrames
    if len(fills):
        st = df.index[0]
        for en in fills.index:
            df_piece = df[st:en][:-1]      # don't include last row
            df_pieces.append(df_piece)
            st = en
        df_pieces.append(df[st:])

    else:
        df_pieces = [df]

    return df_pieces

def optimal_shift(ser1, ser2, shift_range):
    """Determines the optimal shift of Pandas Series 'ser2' in order to maximize the
    correlation (maximum positive correlation, not negative because high temp should correlate
    with high depth) with Pandas series 'ser1'. 'shift_range' is a two-element tuple giving the 
    range of shifts to test; shift values can be negative. Returns two values:  optimal shift, 
    correlation at that shift.
    """
    shifts = range(shift_range[0], shift_range[1] + 1)
    corrs = [ser1.corr(ser2.shift(i)) for i in shifts]
    best_shift = shifts[pd.Series(corrs).idxmax()]
    return best_shift, max(corrs)

def lowess_frac(df, window_days):
    """Returns the fraction of the DataFrame data to use with LOWESS smoothing if the 
    objective is to include 'window_days' worth of data (days).
    """
    days_of_data = (df.ts[-1] - df.ts[0]).total_seconds() / (24*3600)
    if days_of_data <= window_days:
        frac = 1.0
    else:
        frac = window_days / days_of_data

    return frac

def calculate_smooth_depth(df):
    """Function takes the cleaned DataFrame 'df', which has no tank fills in it and has 'temp',
    'depth', and 'ts' columns, and determines a smooth depth trend by removing temperature effects and eliminating
    additional data noise.  The Facebook Prophet time series library is used for the heavy-lifting.
    The returned DataFrame also has 'ts', 'depth' and 'temp' columns but the 'depth' column is smoothed and
    the 'temp' data is time-shifted to best correlate with the depth data.
    """

    # preserve the DataFrame in the parameter list.
    dfp = df[['ts', 'depth', 'temp']].copy()

    # detrend the depth data so that the temperature effect can be determined.
    lowess = sm.nonparametric.lowess
    yhat = lowess(dfp.depth, dfp.ts, frac=lowess_frac(dfp, 5.0))   # use 5 day window for smoothing
    pred_depth = yhat[:,1]
    dfp['depth_detrend'] = dfp.depth - pred_depth
    best_shift, best_corr = optimal_shift(dfp.depth_detrend, dfp.temp, (0, 4*24))   # try 0 - 1 day of shift
    
    # replace the temperature column with the shifted temperature
    dfp['temp'] = dfp.temp.shift(best_shift)
    dfp.dropna(inplace=True)

    # do linear regression to determine temperature effect
    linear_regressor = LinearRegression()
    temp_array = dfp.temp.values.reshape(-1, 1)
    depth_array = dfp.depth_detrend.values.reshape(-1, 1)
    linear_regressor.fit(temp_array, depth_array)  # perform linear regression
    temp_coeff = linear_regressor.coef_[0][0]

    # all done with the detrended depth column so drop it.
    dfp.drop(columns=['depth_detrend'], inplace=True)

    # replace the depth column with depth that has the temperature effect removed
    dfp['depth'] = dfp.depth - (dfp.temp - dfp.temp.mean()) * temp_coeff

    # now smooth the no-temperature-effect depth, allowing more flexibility in the smoothness
    yhat = lowess(dfp.depth, dfp.ts, frac=lowess_frac(dfp, 4.0))   # 4 day window of data for smoothing
    pred_depth = yhat[:,1]

    # replace the depth column with a smoothed depth
    dfp['depth'] = pred_depth

    return dfp

def tank_rate_calcs(df_input, tank_gallons, tank_max_depth, report_hours, fuel_heat_content):
    """Calculates rate of fuel use from the tank across the requested reporting period.
    Assumes that the tank is a horizontal cyclindrical tank.
    Inputs are:
        df_input:  DataFrame with 'ts' (reading timestamp), 'depth' (depth of fuel in inches) and 
            'temp' (temperature at tank in deg F, can be measured anywhere that correlates with tank
                    fuel temperature)
        tank_gallons:    gallons of fuel in tank when full.
        tank_max_depth:  maximum fuel depth in inches
        report_hours:    spacing of rate of fuel use values produced by this function, in hours
        fuel_heat_content: BTUs per gallon of oil in tank at 15 deg-C (59 deg-F)

    Returns a DataFrame, indexed by a timestamp placed at the center of the reporting interval, with
    the columns of 'gal_hr' (gallons per hour of fuel used from the tank), and 'btu_hr' (BTUs per 
    hour of fuel used from the tank).  Usage values are clamped at 0.0 as a minimum (no negative usage).
    """    
    
    # copy input DataFrame so that we don't modify it.
    dff = df_input.copy()

    # calculate normalized depth, 0 - 1.0 (fraction of full-depth), and then calculate volume of 
    # fuel from that.
    d = dff.depth / tank_max_depth
    # Ben Loeffler developed this curve fit for a horizontal cylindrical tank.
    dff['gallons'] = (-1.1153 * d**3 + 1.6729 * d**2 + 0.4549 * d - 0.0063) * tank_gallons

    # drop the depth column, no longer needed.
    dff.drop(columns=['depth'], inplace=True)

    # Make a dataframe with the last gallon and ts values in each reporting interval,
    # and the average temperature (which will eventually be used to adjust the volume of fuel for 
    # thermal expansion/contraction). Timestamp that series in the middle of the interval.
    ts_offset = pd.tseries.frequencies.to_offset(f'{report_hours / 2}H')
    df_rpt = dff.resample(f'{report_hours}H').agg({'ts': 'last', 'gallons': 'last', 'temp': 'mean'})
    df_rpt.index += ts_offset

    # calculate changes in gallons and timestamps
    df_rpt['gal_chg'] =  df_rpt.gallons.diff()
    df_rpt['ts_chg'] =  df_rpt.ts.diff()

    # Convert the gallon change amount to standardized gallons at 15 deg-C (59 deg-F), correcting for thermal
    # expansion.
    df_rpt['gal_chg'] *= (1.0 + (59.0 - df_rpt.temp) * 0.00083 / 1.8)

    # drop last row because it is partial and the first row because
    # it has NaNs due to the diff() calculation above.
    df_rpt = df_rpt[1:-1]

    # calculate gallon/hour and BTU/hr of usage
    df_rpt['hours'] = df_rpt.ts_chg.dt.total_seconds() / 3600.0
    df_rpt['gal_hr'] = -df_rpt.gal_chg / df_rpt.hours

    # replace any negative usage values with zero.
    df_rpt['gal_hr'] = df_rpt.gal_hr.where(df_rpt.gal_hr >= 0.0, 0.0)

    # BTU/hr values are proportional
    df_rpt['btu_hr'] = df_rpt.gal_hr * fuel_heat_content

    # drop columns that aren't very informative
    df_rpt.drop(columns=['ts', 'gallons', 'temp', 'gal_chg', 'ts_chg', 'hours'], inplace=True)
    
    return df_rpt


def main(
    df_raw,                 # Input Pandas DataFrame with "depth" and "temp" columns
    tank_model=None,        # Model of tank, string. Only certain models are known
    tank_gallons=None,      # Alternative to specifying 'tank_model': total tank capacity in gallons
    tank_max_depth=None,    # Alternative to specifying 'tank_model': depth in inches of a full tank
    report_hours=24,        # Hours in the time intervals of BTU/hour and gallons/hour reported
    fuel_btus=137452,       # BTUs/gallon of the fuel in the tank.
    ):
    """Returns a list of DataFrames containing gallon/hour (column name 'gal_hr') and BTU/hour (column 
    name 'btu_hr') fuel use derived from changes in depth of fuel in a fuel tank.  Inputs are:

    df_raw: Pandas DataFrame with a 'depth' column (fuel depth in tank in inches) and a 'temp' column
            (temperature measured at the fuel tank or in the fuel.  The function is flexible enough to
            accommodate a range of location for temperature measurement.  The best location is the a
            a sensor measuring the fuel itself, the most economical and acceptable is the internal 
            temperature sensor of the Elsys ELT-2 connected to a Maxbotix ultrasonic sensor used to
            measure distance to fuel surface.)
    tank_model:  A string identifying a model of fuel tank.  Currently know models are Greer 300, 500,
            1000, and 1500 gallon tanks. Associated 'tank_model' strings are 'greer300', 'greer500',
            'greer1000', and 'greer1500' (capitalization is not important).  If 'tank_model' is not
            specified, both 'tank_gallons' and 'tank_max_depth' must be.
    tank_gallons:  If 'tank_model' is not specified, this input is required and is the full capacity of
            of the tank in gallons.  The tank is assumed to be a horizontal cylindrical tank.
    tank_max_depth:  If 'tank_model' is not specified, this input is required and is the depth of fuel 
            in inches of a full tank.
    report_hours:  The length of the reporting period in the results DataFrame.  Each reported usage
            reading spans this amount of time.  Durations shorter than 24 hours are likely to be noisy
            given the current sensing technology.
    fuel_btus:  The number of BTUs in a gallon of fuel in the tank.  Defaults to an average number
            for #1 Heating Oil.
    """

    # dictionary mapping Tank IDs to (tank capacity in gallons, tank max fuel depth in inches)
    tanks = {
        'greer300': (300, 37.78),
        'greer500': (500, 44.78),
        'greer1000': (1000, 63.72),
        'greer1500': (1500, 63.63),
    }

    # if a Tank ID is given, lookup size parameters for tank.
    if tank_model is not None:
        tmodel = tank_model.lower()
        tank_gallons, tank_max_depth = tanks[tmodel]

    # clean up data and add ts column
    df = clean_raw_data(df_raw)

    # split Data into sections between Tank Fills
    df_pieces = split_by_fill(df, 0.5)    # 0.5" or more considered a fill

    # Make a list of results DataFrames, frames being separated by fills
    list_df = []
    for df_no_fill in df_pieces:
        df_smooth = calculate_smooth_depth(df_no_fill)
        df_rpt = tank_rate_calcs(df_smooth, tank_gallons, tank_max_depth, report_hours, fuel_btus)
        list_df.append(df_rpt)

    return list_df

if __name__ == "__main__":

    # Do a test run by getting test data directly from the BMON server
    from bmondata import Server
    import numpy as np

    svr = Server('https://bmon.analysisnorth.com')
    df_raw = svr.sensor_readings(
        [('A81758FFFE0611F6_distance', 'depth'), ('A81758FFFE0611F6_temperature', 'temp')], 
        start_ts = '2022-06-03',
    )

    # alter data to look like two fills
    adder = np.array([0.0]*len(df_raw))
    adder[3000:] = 5.0
    adder[5000:] = 7.0
    df_raw['depth'] += adder

    df = main(df_raw, tank_model='greer300')
    print(df)
