import pandas as pd
import bmsapp.models
import bmsapp.data_util
from . import basechart
from . import chart_config


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

        if len(recs):
            df = pd.DataFrame(recs)
            z_list = []
            text_list = []
            for da in range(0,7):
                z_vals = []
                text_vals = []
                for hr in range(0,24):
                    val = bmsapp.data_util.round4(df.loc[(df['da'] == da) & (df['hr'] == hr), 'val'].mean())
                    z_vals.append(val)
                    text_vals.append('Avg: '+str(val)+' '+the_sensor.unit.label)
                z_list.append(z_vals)
                text_list.append(text_vals)
        else:
            z_list = [[None for hr in range(0,24)] for da in range(0,7)]
            text_list = z_list

        data = [{'z': z_list,
                 'x': ['12a', '1a', '2a', '3a', '4a', '5a', '6a', '7a',
                       '8a', '9a', '10a', '11a', '12p', '1p', '2p', '3p',
                       '4p', '5p', '6p', '7p', '8p', '9p', '10p', '11p'],
                 'y': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday','Saturday', 'Sunday'],
                 'text': text_list,
                 'name': 'Hourly Average',
                 'type': 'heatmap',
                 'colorscale': [[0, '#FFFFFF'],[1,'#0066FF']],
                 'hoverinfo': 'x+y+text',
                 'xgap': 1,
                 'ygap': 1
                 }]

        opt = self.get_chart_options('plotly')
        opt['data'] = data
        opt['layout']['title'] = the_sensor.title + ' Hourly Profile: ' + self.building.title
        opt['layout']['xaxis']['title'] =  'Hour of the Day'
        opt['layout']['yaxis']['title'] =  ''
        opt['layout']['margin']['b'] =  60
        opt['layout']['margin']['l'] =  80

        html = basechart.chart_config.chart_container_html(opt['layout']['title'])

        return {'html': html, 'objects': [('plotly', opt)]}

