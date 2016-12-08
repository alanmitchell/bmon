import numpy as np, pandas as pd
from datetime import datetime
import pytz
import bmsapp.models, bmsapp.data_util
import basechart

class TimeSeries(basechart.BaseChart):
    """Chart class for creating Time Series graph.
    """

    # see BaseChart for definition of these constants
    CTRLS = 'refresh, ctrl_sensor, ctrl_avg, ctrl_occupied, time_period'
    MULTI_SENSOR = 1

    def result(self):
        """
        Returns the HTML and configuration for a Time Series chart.  
        """

        # Determine the sensors to plot. This creates a list of Sensor objects to plot.
        sensor_list = [ bmsapp.models.Sensor.objects.get(pk=id) for id in self.request_params.getlist('select_sensor') ]

        # determine the Y axes that will be needed to cover the the list of sensor, based on the labels
        # of the units
        y_axes = {label:index for index, label in enumerate(list(set([sensor.unit.label for sensor in sensor_list])), start=1)}

        # get the requested averaging interval in hours
        averaging_hours = float(self.request_params['averaging_time'])

        # determine the start time for selecting records and loop through the selected
        # records to get the needed dataset
        st_ts, end_ts = self.get_ts_range()

        # Create the series to plot and add up total points to plot and the points
        # in the longest series.
        series = []
        # determine suitable line width
        line_width = 1 if len(sensor_list) > 1 else 2
        for sensor in sensor_list:
            db_recs = self.reading_db.rowsForOneID(sensor.sensor_id, st_ts, end_ts)
            # put timestamps and values into arrays
            times = []
            values = []
            for rec in db_recs:
                times.append(rec['ts'])
                values.append(rec['val'])
            # convert timestamps to a numpy array to be consistent with Pandas index below and 
            # to allow easy multiplication
            times = np.array(times)
            if averaging_hours:
                # averaging is requested, so do it using a Pandas Series
                ser = pd.Series(values, index=times).groupby(bmsapp.data_util.TsBin(averaging_hours).bin).mean()
                values = ser.values
                times = ser.index

            # Plotly uses datetime strings instead of timestamps
            tz = pytz.timezone(self.timezone)
            times = [datetime.fromtimestamp(ts,tz).strftime('%Y-%m-%d %H:%M:%S') for ts in times]

            # Format the values
            values = [bmsapp.data_util.round4(val) for val in values]
                
            series_opt = {'x': times,
                          'y': values,
                          'type': 'scatter',
                          'mode': 'lines', 
                          'name': sensor.title, 
                          'yaxis': 'y'+(str(y_axes[sensor.unit.label]) if y_axes[sensor.unit.label] > 1 else ''),
                          'line': {'width': line_width},
                         }

            # TODO: Do we need to set the tooltip format, either through the data.text or through data.hoverinfo and layout.hovermode+axis.hoverformat?
            """
                          'tooltip': {
                              'valueSuffix': ' ' + sensor.unit.label,
                              'valueDecimals': bmsapp.data_util.decimals_needed(values, 4)
                          }
            """

            # if the sensor has defined states, make the series a Step type series.
            if sensor.unit.measure_type == 'state':
                series_opt['line']['shape'] = 'hv'
            series.append( series_opt )

        # Set the basic chart options
        chart_type = 'plotly'
        opt = self.get_chart_options(chart_type)

        # set the chart data
        opt['data'] = series

        opt['layout']['xaxis']['title'] =  "Date/Time (%s)" % self.timezone
        opt['layout']['xaxis']['type'] =  'date'


        # Make the chart y axes configuration objects
        # TODO: still need to adjust positioning so that axes don't draw on top of each other
        for label, id in y_axes.items():
            if id == 1:
                opt['layout']['yaxis']['title'] = label
            else:
                opt['layout']['yaxis'+str(id)] = {'title': label,
                                                  'overlaying':'y',
                                                  'side': 'right',
                                                  'titlefont': opt['layout']['yaxis']['titlefont']}


        # If occupied period shading is requested, do it, as long as data
        # is averaged over 1 day or less
        if ('show_occupied' in self.request_params):

            # get resolution to use in determining whether a timestamp is
            # occupied.
            resolution = self.occupied_resolution()  

            # determine the occupied periods
            if (self.schedule is None) or (resolution is None):
                # no schedule or data doesn't lend itself to classifying
                periods = [(st_ts, end_ts)]
            else:
                periods = self.schedule.occupied_periods(st_ts, end_ts, resolution=resolution)

            bands = []
            for occ_start, occ_stop in periods:
                band = {'type': 'rect',
                        'xref': 'x',
                        'layer': 'below',
                        'yref': 'paper',
                        'fillcolor': '#d0f5dd',
                        'opacity': 0.75,
                        'line': {'width': 0},
                        'x0': datetime.fromtimestamp(occ_start,tz).strftime('%Y-%m-%d %H:%M:%S'),
                        'y0': 0,
                        'x1': datetime.fromtimestamp(occ_stop,tz).strftime('%Y-%m-%d %H:%M:%S'),
                        'y1': 1
                        }
                bands.append(band)

            opt['layout']['shapes'] = bands

        html = '<div id="chart_container" style="border-style:solid; border-width:2px; border-color:#4572A7"></div>'

        return {'html': html, 'objects': [(chart_type, opt)]}

