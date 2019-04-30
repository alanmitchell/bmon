import pandas as pd
import numpy as np
import bmsapp.models
import bmsapp.data_util
from . import basechart
import pytz

class Histogram(basechart.BaseChart):
    """Class that creates Histogram plot.
    """

    # see BaseChart for definition of these constants
    CTRLS = 'refresh, ctrl_sensor, ctrl_avg, time_period_group'

    def result(self):
        """
        Returns the HTML and chart object for an Histogram chart.
        """

        chart_series = []   # will hold all the series created

        # determine the sensor to plot from the sensor selected by the user.
        the_sensor = bmsapp.models.Sensor.objects.get(pk=self.request_params['select_sensor'])

        # get the requested averaging interval in hours
        averaging_hours = float(self.request_params['averaging_time'])

        # determine the start time for selecting records
        st_ts, end_ts = self.get_ts_range()

        # get the database records
        df = self.reading_db.dataframeForOneID(the_sensor.sensor_id, st_ts, end_ts, pytz.timezone(self.timezone))

        if not df.empty:

            # info needed to create each series (selection list, series name, visible)
            if self.schedule:
                occupied_times = df.ts.apply(self.schedule.is_occupied)
                unoccupied_times = -occupied_times

                series_info = [(None, 'All Data', True),
                               (occupied_times, 'Occupied Periods', False),
                               (unoccupied_times, 'Unoccupied Periods', False)]
            else:
                # no schedule, so just return the 'All Data' series
                series_info = [(None, 'All Data', True)]

            for mask, series_name, visibility in series_info:
                if mask is None:
                    select_df = df
                else:
                    select_df = df[mask]

                if averaging_hours:
                    select_df = bmsapp.data_util.resample_timeseries(select_df, averaging_hours)

                histogram_series = bmsapp.data_util.histogram_from_series(select_df.val)

                chart_series.append({'x': [x for x,y in histogram_series],
                                     'y': [y for x,y in histogram_series],
                                     'type': 'scatter',
                                     'mode': 'lines', 
                                     'name': series_name, 
                                     'visible': 'true' if visibility else 'legendonly'
                                     })

        opt = self.get_chart_options('plotly')
        opt['data'] = chart_series
        opt['layout']['title'] = the_sensor.title + ' Histogram: ' + self.building.title
        opt['layout']['xaxis']['title'] =  the_sensor.unit.label
        opt['layout']['xaxis']['type'] =  'linear'
        opt['layout']['yaxis']['title'] =  '% of Readings'
        opt['layout']['yaxis']['rangemode'] = 'tozero'

        html = basechart.chart_config.chart_container_html(opt['layout']['title'])

        return {'html': html, 'objects': [('plotly', opt)]}
