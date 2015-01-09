import pandas as pd
import numpy as np
import bmsapp.models
import bmsapp.data_util
import basechart


class Histogram(basechart.BaseChart):
    """Class that creates Histogram plot.
    """

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

                chart_series.append({'data': bmsapp.data_util.histogram_from_series(select_series),
                                     'name': series_name,
                                     'visible': visibility})
        else:
            chart_series = []

        opt = self.get_chart_options()
        opt['series'] = chart_series
        opt['yAxis']['title']['text'] = '% of Readings'
        opt['yAxis']['min'] = 0
        opt['xAxis']['title']['text'] = the_sensor.unit.label
        opt['title']['text'] = the_sensor.title + ' Histogram: ' + self.building.title
        opt['title']['style']['fontSize'] = '20px'

        html = '<div id="chart_container"></div>'

        return {'html': html, 'objects': [('highcharts', opt)]}
