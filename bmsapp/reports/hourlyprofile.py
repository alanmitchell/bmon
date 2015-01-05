class HourlyProfile(BaseChart):

    def result(self):
        """
        Returns the HTML and chart object for an Hourly Profile chart.
        """
        # open the database 
        db = bmsdata.BMSdata(global_vars.DATA_DB_FILENAME)

        # determine the sensor to plot from the sensor selected by the user.
        the_sensor = models.Sensor.objects.get(pk=self.request_params['select_sensor'])

        # determine the start time for selecting records and loop through the selected
        # records to get the needed dataset
        st_ts, end_ts = self.get_ts_range()
        db_recs = db.rowsForOneID(the_sensor.sensor_id, st_ts, end_ts)
        recs = []
        for rec in  db_recs:
            dt = data_util.ts_to_datetime(rec['ts'])
            recs.append( {'da': dt.weekday(), 'hr': dt.hour, 'val': rec['val']} )

        series = []
        if len(recs):
            # make a pandas DataFrame that has average values for each weekday / hour
            # combination.  Remove the multi-index so that it easier to select certain days
            df = pd.DataFrame(recs).groupby(('da', 'hr')).mean().reset_index()

            # Here are the groups of days we want to chart as separate series
            da_groups = [ ('All Days', (0,1,2,3,4,5,6)),
                          ('Mon', (0,)),
                          ('Tue-Fri', (1,2,3,4)),
                          ('Mon-Fri', (0,1,2,3,4)),
                          ('Sat', (5,)),
                          ('Sun', (6,)),
                          ('Sat-Sun', (5,6)),
                        ]

            # Make a list of the series.  create the series in a form directly useable by
            # Highcharts.
            for nm, da_tuple in da_groups:
                a_series = {'name': nm}
                df_gp = df[df.da.isin(da_tuple)].drop('da', axis=1).groupby('hr').mean()
                a_series['data'] = [data_util.round4(df_gp.ix[hr, 'val']) if hr in df_gp.index else None for hr in range(24)]
                if nm != 'All Days':
                    a_series['visible'] = False
                series.append(a_series)

        # if normalization was requested, scale values 0 - 100%, with 100% being the largest
        # value across all the day groups.
        if 'normalize' in self.request_params:
            yTitle = "%"
            # find maximum of each series
            maxes = [max(ser['data']) for ser in series]
            scaler = 100.0 / max(maxes) if max(maxes) else 1.0
            # adjust the values
            for ser in series:
                for i in range(24):
                    if ser['data'][i]:   # don't scale None values
                        ser['data'][i] = data_util.round4(ser['data'][i] * scaler)
        else:
            yTitle = the_sensor.unit.label

        opt = self.get_chart_options()
        opt['series'] = series
        opt['yAxis']['title']['text'] = yTitle
        opt['xAxis']['categories'] = ['12a', '1a', '2a', '3a', '4a', '5a', '6a', '7a', '8a', '9a', 
            '10a', '11a', '12p', '1p', '2p', '3p', '4p', '5p', '6p', '7p', '8p', '9p', '10p', '11p']
        opt['xAxis']['title']['text'] = 'Hour of the Day'
        opt['title']['text'] = the_sensor.title + ' Hourly Profile: ' + self.building.title
        opt['title']['style']['fontSize'] = '20px'
        if 'normalize' in self.request_params:
            opt['yAxis']['min'] = 0
            opt['yAxis']['max'] = 100

        html = '<div id="chart_container"></div>'

        return {'html': html, 'objects': [('highcharts', opt)]}

