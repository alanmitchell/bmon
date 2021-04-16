import pandas as pd
import bmsapp.models
import bmsapp.data_util
from . import basechart


class HourlyProfile(basechart.BaseChart):
    """Class that creates Hourly Profile graph.
    """

    # see BaseChart for definition of these constants
    CTRLS = 'refresh, ctrl_sensor, ctrl_normalize, time_period_group, get_embed_link'

    def result(self):
        """
        Returns the HTML and chart object for an Hourly Profile chart.
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

        series = []
        if len(recs):
            # make a pandas DataFrame that has average values for each weekday / hour
            # combination.  Remove the multi-index so that it easier to select certain days
            df = pd.DataFrame(recs).groupby(['da', 'hr']).mean().reset_index()

            # Here are the groups of days we want to chart as separate series
            if self.schedule:
                da_groups = [('All Days', (0, 1, 2, 3, 4, 5, 6), False),
                             ('Occupied Days', (da for da in self.schedule.predominantly_occupied_days), True),
                             ('Un-Occupied Days', (da for da in range(7)
                                                   if da not in self.schedule.predominantly_occupied_days), True)]
            else:
                da_groups = [('All Days', (0, 1, 2, 3, 4, 5, 6), True)]

            da_groups += [('Mon', (0,), False),
                          ('Tue-Fri', (1, 2, 3, 4), False),
                          ('Sat', (5,), False),
                          ('Sun', (6,), False)]

            # Make a list of the series.
            for nm, da_tuple, visibility in da_groups:
                df_gp = df[df.da.isin(da_tuple)].drop('da', axis=1).groupby('hr').mean()
                a_series = {'x': ['12a', '1a', '2a', '3a', '4a', '5a', '6a', '7a',
                                  '8a', '9a', '10a', '11a', '12p', '1p', '2p', '3p',
                                  '4p', '5p', '6p', '7p', '8p', '9p', '10p', '11p'],
                            'y': [bmsapp.data_util.round4(df_gp.loc[hr, 'val'])
                                    if hr in df_gp.index else None for hr in range(24)],
                            'type': 'scatter',
                            'mode': 'lines', 
                            'name': nm, 
                            'visible': 'true' if visibility else 'legendonly'
                            }

                series.append(a_series)

        # if normalization was requested, scale values 0 - 100%, with 100% being the largest
        # value across all the day groups.
        if 'normalize' in self.request_params:
            yTitle = "%"
            # find maximum of each series
            maxes = [max(ser['y']) for ser in series]
            scaler = 100.0 / max(maxes) if max(maxes) else 1.0
            # adjust the values
            for ser in series:
                for i in range(24):
                    if ser['y'][i]:   # don't scale None values
                        ser['y'][i] = bmsapp.data_util.round4(ser['y'][i] * scaler)
        else:
            yTitle = the_sensor.unit.label


        opt = self.get_chart_options('plotly')
        opt['data'] = series
        opt['layout']['title'] = the_sensor.title + ' Hourly Profile: ' + self.building.title
        opt['layout']['xaxis']['title'] =  'Hour of the Day'
        opt['layout']['xaxis']['type'] =  'category'
        opt['layout']['yaxis']['title'] =  yTitle
        if 'normalize' in self.request_params:
            opt['layout']['yaxis']['range'] = [0, 100]

        html = basechart.chart_config.chart_container_html(opt['layout']['title'])

        return {'html': html, 'objects': [('plotly', opt)]}

