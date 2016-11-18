import pandas as pd
import numpy as np
import bmsapp.models
import bmsapp.data_util
import basechart


class Histogram(basechart.BaseChart):
    """Class that creates Histogram plot.
    """

    # see BaseChart for definition of these constants
    CTRLS = 'refresh, ctrl_sensor, ctrl_avg, time_period'

    def result(self):
        """
        Returns the HTML and chart object for an Histogram chart.
        """

        # determine the sensor to plot from the sensor selected by the user.
        the_sensor = bmsapp.models.Sensor.objects.get(pk=self.request_params['select_sensor'])

        # get the requested averaging interval in hours
        averaging_hours = float(self.request_params['averaging_time'])

        # determine the start time for selecting records and loop through the selected
        # records to get the needed dataset
        st_ts, end_ts = self.get_ts_range()
        db_recs = self.reading_db.rowsForOneID(the_sensor.sensor_id, st_ts, end_ts)

        # extract out the values and the timestamps into numpy arrays.
        values = np.array([rec['val'] for rec in db_recs])
        times = np.array([rec['ts'] for rec in db_recs])
        if len(values):
            # create a Pandas Time Series
            pd_ser = pd.Series(values, index=times)

            chart_series = []   # will hold all the series created

            # info needed to create each series (selection list, series name, visible)
            if self.schedule:
                occupied_times = []
                unoccupied_times = []
                for ts in pd_ser.index:
                    if self.schedule.is_occupied(ts):
                        occupied_times.append(ts)
                    else:
                        unoccupied_times.append(ts)

                series_info = [(None, 'All Data', True),
                               (occupied_times, 'Occupied Periods', False),
                               (unoccupied_times, 'Unoccupied Periods', False)]
            else:
                # no schedule, so just return the 'All Data' series
                series_info = [(None, 'All Data', True)]

            for select_list, series_name, visibility in series_info:
                if select_list:
                    select_series = pd_ser[select_list]
                else:
                    select_series = pd_ser

                if averaging_hours:
                    select_series = select_series.groupby(bmsapp.data_util.TsBin(averaging_hours).bin).mean()

                histogram_series = bmsapp.data_util.histogram_from_series(select_series)

                chart_series.append({'x': [x for x,y in histogram_series],
                                     'y': [y for x,y in histogram_series],
                                     'type': 'scatter',
                                     'mode': 'lines', 
                                     'name': series_name, 
                                     'visible': 'true' if visibility else 'legendonly'
                                     })
        else:
            chart_series = []

        opt = self.get_chart_options('plotly')
        opt['data'] = chart_series
        opt['layout']['title'] = the_sensor.title + ' Histogram: ' + self.building.title
        opt['layout']['xaxis']['title'] =  the_sensor.unit.label
        opt['layout']['xaxis']['type'] =  'linear'
        opt['layout']['yaxis']['title'] =  '% of Readings'
        opt['layout']['yaxis']['rangemode'] = 'tozero'

        html = '<div id="chart_container" style="border-style:solid; border-width:2px; border-color:#4572A7"></div>'

        return {'html': html, 'objects': [('plotly', opt)]}
