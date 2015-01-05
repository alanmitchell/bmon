class Histogram(BaseChart):

    def result(self):
        """
        Returns the HTML and chart object for an Histogram chart.
        """
        # open the database 
        db = bmsdata.BMSdata(global_vars.DATA_DB_FILENAME)

        # determine the sensor to plot from the sensor selected by the user.
        the_sensor = models.Sensor.objects.get(pk=self.request_params['select_sensor'])

        # determine the start time for selecting records and loop through the selected
        # records to get the needed dataset
        st_ts, end_ts = self.get_ts_range()
        db_recs = db.rowsForOneID(the_sensor.sensor_id, st_ts, end_ts)
        # extract out the values and the timestamps into numpy arrays.
        values = np.array([rec['val'] for rec in db_recs])
        times = np.array([rec['ts'] for rec in db_recs])
        if len(values):
            # create a Pandas Time Series to allow easy time averaging
            pd_ser = pd.Series(values, index=times)
            series = []   # will hold all the series created
            # info needed to create each series (time averaging function, series name)
            series_info = ( (None, 'Raw'),
                            (data_util.TsBin(1).bin, '1 Hr Averages'),
                            (data_util.TsBin(2).bin, '2 Hr Avg'),
                            (data_util.TsBin(4).bin, '4 Hr Avg'),
                            (data_util.TsBin(8).bin, '8 Hr Avg'),
                            (data_util.TsBin(24).bin, '1 Day Avg') )
            for avg_func, series_name in series_info:
                if avg_func:
                    avg_series = pd_ser.groupby(avg_func).mean()
                else:
                    avg_series = pd_ser
                one_series = {'data': data_util.histogram_from_series(avg_series), 'name': series_name}
                if series_name != 'Raw':
                    one_series['visible'] = False
                series.append( one_series )
        else:
            series = []

        opt = self.get_chart_options()
        opt['series'] = series
        opt['yAxis']['title']['text'] = '% of Readings'
        opt['yAxis']['min'] = 0
        opt['xAxis']['title']['text'] = the_sensor.unit.label
        opt['title']['text'] = the_sensor.title + ' Histogram: ' + self.building.title
        opt['title']['style']['fontSize'] = '20px'

        html = '<div id="chart_container"></div>'

        return {'html': html, 'objects': [('highcharts', opt)]}
