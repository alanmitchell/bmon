import numpy as np, pandas as pd
from datetime import datetime
import pytz
import textwrap
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
        if 'averaging_time' in self.request_params:
            averaging_hours = float(self.request_params['averaging_time'])
        else:
            averaging_hours = 0

        # determine the start time for selecting records and loop through the selected
        # records to get the needed dataset
        st_ts, end_ts = self.get_ts_range()

        # Get the timezone for the building
        tz = pytz.timezone(self.timezone)

        # Create the series to plot and add up total points to plot and the points
        # in the longest series.
        series = []
        # determine suitable line width
        line_width = 1 if len(sensor_list) > 1 else 2
        for sensor in sensor_list:

            # get the database records
            df = self.reading_db.dataframeForOneID(sensor.sensor_id, st_ts, end_ts,tz)

            if not df.empty:
                # perform average (if requested)
                if averaging_hours:
                    df = bmsapp.data_util.resample_timeseries(df,averaging_hours)

                # create lists for plotly
                if np.absolute(df.val.values).max() < 10000:
                    values = np.char.mod('%.4g',df.val.values).astype(float).tolist()
                else:
                    values = np.round(df.val.values).tolist()
                times = df.index.strftime('%Y-%m-%d %H:%M:%S').tolist()
            else:
                times = []
                values = []

            series_opt = {'x': times,
                          'y': values,
                          'type': 'scatter',
                          'mode': 'lines', 
                          'name': sensor.title, 
                          'yaxis': 'y'+(str(y_axes[sensor.unit.label]) if y_axes[sensor.unit.label] > 1 else ''),
                          'line': {'width': line_width},
                         }

            # if the sensor has defined states, make the series a Step type series.
            if sensor.unit.measure_type == 'state':
                series_opt['line']['shape'] = 'hv'
            series.append( series_opt )

        # Set the basic chart options
        chart_type = 'plotly'
        opt = self.get_chart_options(chart_type)

        # set the chart data
        opt['data'] = series

        # If there there are more than 12 sensors, hide the legend
        if len(sensor_list) > 12:
            opt['layout']['showLegend'] = False

        opt['layout']['xaxis']['title'] =  "Date/Time (%s)" % self.timezone
        opt['layout']['xaxis']['type'] =  'date'
        opt['layout']['xaxis']['hoverformat'] = '%a %m/%d %H:%M'

        opt['layout']['annotations'] = []
        opt['layout']['shapes'] = []

        # Make the chart y axes configuration objects
        if len(y_axes) == 1:
            opt['layout']['margin']['l'] = 60
            opt['layout']['margin']['r'] = 20
            opt['layout']['yaxis']['title'] = y_axes.keys()[0]
        elif len(y_axes) == 2:
            opt['layout']['margin']['l'] = 60
            opt['layout']['margin']['r'] = 60
            y_axes_by_id = {v: k for k, v in y_axes.iteritems()}
            opt['layout']['yaxis']['title'] = y_axes_by_id[1]
            opt['layout']['yaxis2'] = {'title': y_axes_by_id[2],
                                              'overlaying':'y',
                                              'side': 'right',
                                              'titlefont': opt['layout']['yaxis']['titlefont']}
        else:
            opt['layout']['margin']['l'] = 60
            opt['layout']['margin']['r'] = 20           
            opt['layout']['xaxis']['domain'] = [0.10 * (len(y_axes) - 1), 1]          
            for label, id in y_axes.items():
                if id == 1:
                    opt['layout']['yaxis']['title'] = label
                else:
                    opt['layout']['yaxis'+str(id)] = {'title': label,
                                                      'overlaying':'y',
                                                      'side': 'left',
                                                      'anchor': 'free',
                                                      'position': 0.10 * (id - 2),
                                                      'ticks': 'outside',
                                                      'ticklen': 8,
                                                      'tickwidth': 1,
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
                opt['layout']['shapes'].append(band)
        
        # If the building has timeline annotations, add them to the chart
        if self.building.timeline_annotations:
            # Parse the timeline_annotations string
            t_a_list = self.building.timeline_annotations.splitlines()
            for t_a in t_a_list:
                try:
                    t_a_text, t_a_datetimestring = t_a.split(":",1)
                    t_a_ts = bmsapp.data_util.datestr_to_ts(t_a_datetimestring, tz)
                    if t_a_ts >= st_ts and t_a_ts <= end_ts:
                        # Add the text annotation to the top of the chart
                        opt['layout']['annotations'].append({
                                                             'x': datetime.fromtimestamp(t_a_ts,tz).strftime('%Y-%m-%d %H:%M:%S'),
                                                             'y': 1,
                                                             'xref': 'x',
                                                             'yref': 'paper',
                                                             'text': "<br>".join(textwrap.wrap(t_a_text,8,break_long_words=False)),
                                                             'showarrow': False,
                                                             'bgcolor': 'white'
                                                          })
                        # Add a vertical dotted line to the chart
                        opt['layout']['shapes'].append({
                                                        'type': 'line',
                                                        'xref': 'x',
                                                        'yref': 'paper',
                                                        'line': {'width': 1.25, 'color': 'black', 'dash': 'dot'},
                                                        'x0': datetime.fromtimestamp(t_a_ts,tz).strftime('%Y-%m-%d %H:%M:%S'),
                                                        'y0': 0,
                                                        'x1': datetime.fromtimestamp(t_a_ts,tz).strftime('%Y-%m-%d %H:%M:%S'),
                                                        'y1': 1
                                                        })
                except:
                    # ignore annotations that create errors
                    pass

        html = basechart.chart_config.chart_container_html(opt['layout']['title'])

        return {'html': html, 'objects': [(chart_type, opt)]}

