import pandas as pd
import bmsapp.models
import bmsapp.data_util
import basechart
import chart_config


class HourlyHeatMap(basechart.BaseChart):
    """Class that creates Hourly Profile Heat Map, which displays hourly averages
    for each day of the week.
    """

    # see BaseChart for definition of these constants
    CTRLS = 'refresh, ctrl_sensor, time_period'

    def result(self):
        """
        Returns the HTML and chart object for an Hourly Heat Map chart
        """
        # determine the sensor to plot from the sensor selected by the user.
        the_sensor = bmsapp.models.Sensor.objects.get(pk=self.request_params['select_sensor'])

        # determine the start time for selecting records and loop through the selected
        # records to get the needed dataset
        st_ts, end_ts = self.get_ts_range()
        db_recs = self.reading_db.rowsForOneID(the_sensor.sensor_id, st_ts, end_ts)
        recs = []
        for rec in db_recs:
            dt = bmsapp.data_util.ts_to_datetime(rec['ts'])
            recs.append({'da': dt.weekday(), 'hr': dt.hour, 'val': rec['val']})

        data = []
        if len(recs):
            # make a pandas DataFrame that has average values for each weekday / hour
            # combination.  Remove the multi-index so that it easier to select certain days
            df = pd.DataFrame(recs).groupby(('da', 'hr')).mean().reset_index()
            for i in range(len(df)):
                data.append([int(df.xs(i)['hr']), int(df.xs(i)['da']), bmsapp.data_util.round4(df.xs(i)['val'])])

        series = {'data': data,
                  'name': 'Hourly Average',
                  'borderWidth': 1,
                 }
        opt = self.get_chart_options('heatmap')

        opt['series'] = [series]
        opt['xAxis']['categories'] = ['12a', '1a', '2a', '3a', '4a', '5a', '6a', '7a', '8a', '9a',
            '10a', '11a', '12p', '1p', '2p', '3p', '4p', '5p', '6p', '7p', '8p', '9p', '10p', '11p']
        opt['yAxis']['categories'] = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday',
                                      'Saturday', 'Sunday']
        opt['yAxis']['title'] = None
        opt['title']['text'] = the_sensor.title + ' Hourly Profile: ' + self.building.title
        opt['tooltip']['pointFormat'] = "<b>{point.value} %s</b>" % (the_sensor.unit.label)

        html = '<div id="chart_container"></div>'

        return {'html': html, 'objects': [('highcharts', opt)]}

