class TimeSeries(BaseChart):

    def result(self):
        """
        Returns the HTML and configuration for a Time Series chart.  
        """
        # open the database 
        db = bmsdata.BMSdata(global_vars.DATA_DB_FILENAME)

        # Determine the sensors to plot. This creates a list of Sensor objects to plot.
        sensor_list = [ models.Sensor.objects.get(pk=id) for id in self.request_params.getlist('select_sensor') ]

        # determine the Y axes that will be needed to cover the the list of sensor, based on the labels
        # of the units
        y_axes_ids = list(set([sensor.unit.label for sensor in sensor_list]))

        # get the requested averaging interval in hours
        averaging_hours = float(self.request_params['averaging_time'])

        # determine the start time for selecting records and loop through the selected
        # records to get the needed dataset
        st_ts, end_ts = self.get_ts_range()

        # Create the series to plot and add up total points to plot and the points
        # in the longest series.
        pt_count = 0
        max_series_count = 0
        series = []
        # determine suitable line width
        line_width = 1 if len(sensor_list) > 1 else 2
        for sensor in sensor_list:
            db_recs = db.rowsForOneID(sensor.sensor_id, st_ts, end_ts)
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
                ser = pd.Series(values, index=times).groupby(data_util.TsBin(averaging_hours).bin).mean()
                values = ser.values
                times = ser.index
            # Highcharts uses milliseconds for timestamps, and convert to float because weirdly, integers have
            # problems with JSON serialization.
            times = times * 1000.0    
            # Create series data, each item being an [ts, val] pair.  
            # The 'yAxis' property indicates the id of the Y axis where the data should be plotted.
            # Our convention is to use the unit label for the axis as the id.
            series_data = [ [ts, data_util.round4(val)] for ts, val in zip(times, values) ]

            # update point count variables
            pts_in_series = len(series_data)
            pt_count += pts_in_series
            if pts_in_series > max_series_count:
                max_series_count = pts_in_series

            series_opt = {'data': series_data, 
                          'name': sensor.title, 
                          'yAxis': sensor.unit.label,
                          'lineWidth': line_width,
                          'tooltip': {
                              'valueSuffix': ' ' + sensor.unit.label,
                              'valueDecimals': data_util.decimals_needed(values, 4)
                          }
                         }
            # if the sensor has defined states, make the series a Step type series.
            if sensor.unit.measure_type == 'state':
                series_opt['step'] = 'left'
            series.append( series_opt )

        # Make the chart y axes configuration objects
        y_axes = [{ 'id': ax_id,
                    'opposite': False,
                    'title': {
                        'text': ax_id,
                        'style': {'fontSize': '16px'}
                    }
                  } for ax_id in  y_axes_ids]

        # Choose the chart type based on number of points
        if pt_count < 15000 and max_series_count < 5000:
            opt = self.get_chart_options()
            opt['xAxis']['title']['text'] =  "Date/Time (your computer's time zone)"
            opt['xAxis']['type'] =  'datetime'
            chart_type = 'highcharts'
        else:
            opt = self.get_chart_options('highstock')
            chart_type = 'highstock'

        opt['series'] = series
        opt['yAxis'] = y_axes

        html = '<div id="chart_container"></div>'

        return {'html': html, 'objects': [(chart_type, opt)]}

