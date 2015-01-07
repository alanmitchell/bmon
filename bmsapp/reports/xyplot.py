import time
from datetime import datetime
import pandas as pd, pytz
import bmsapp.models, bmsapp.data_util
import basechart

class XYplot(basechart.BaseChart):
    """Class that creates XY Plot.
    """

    def result(self):
        """
        Returns the HTML and chart object for a scatter plot of one sensor vs. another.  
        """

        # determine the X and Y sensors to plot from those sensors selected by the user.
        sensorX = bmsapp.models.Sensor.objects.get(pk=self.request_params['select_sensor_x'])
        sensorY = bmsapp.models.Sensor.objects.get(pk=self.request_params['select_sensor_y'])

        # make a timestamp binning object
        binner = bmsapp.data_util.TsBin(float(self.request_params['averaging_time_xy']))

        # determine the start and end time for selecting records
        st_ts, end_ts = self.get_ts_range()

        # get the dividing date, if there is one
        div_date = self.request_params['divide_date']
        div_ts = bmsapp.data_util.datestr_to_ts(div_date) if len(div_date) else 0


        # The list that will hold each Highcharts series
        series = []

        # get the X and Y sensor records and perform the requested averaging
        db_recsX = self.reading_db.rowsForOneID(sensorX.sensor_id, st_ts, end_ts)
        db_recsY = self.reading_db.rowsForOneID(sensorY.sensor_id, st_ts, end_ts)
        if len(db_recsX)>0 and len(db_recsY)>0:
            # both sensors have some data, so proceed to average the data points
            dfX = pd.DataFrame(db_recsX).set_index('ts').groupby(binner.bin).mean()
            dfX.columns = ['X']
            dfY = pd.DataFrame(db_recsY).set_index('ts').groupby(binner.bin).mean()
            dfY.columns = ['Y']

            # Join the X and Y values for the overlapping time intervals and make
            # a list of points.
            df_all = dfX.join(dfY, how='inner')  # inner join does intersection of timestamps

            # add a point name column to be used in the tooltip.  Use the Date/Time for this.
            tz = pytz.timezone(self.timezone)
            df_all['name'] = [datetime.fromtimestamp(ts, tz).strftime('%b %d, %Y %H:%M') for ts in df_all.index]

            # add a column identifying whether point is in occupied or unoccupied period.
            resolution = self.occupied_resolution()
            if (self.schedule is None) or (resolution is None):
                # no schedule or data doesn't lend itself to classifying
                # consider all points to be occupied
                df_all['occupied'] = 1
            else:
                df_all['occupied'] = [self.schedule.is_occupied(ts, resolution=resolution) for ts in df_all.index]

            # Set up the parameters for the different series of data
            # Required Info is (starting timestamp, ending timestamp, series name, series color, series symbol).
            ts_now = time.time()
            if div_ts:
                # A dividing date was provided by the user.
                ser_params = ( (0, div_ts, 'Prior to %s' % div_date, '#2f7ed8', 'circle'),
                               (div_ts, ts_now, '%s and beyond' % div_date, '#FF0000', 'circle') )
            else:
                # Divide data by how recent it is.
                ser_params = ( (0, ts_now - 7 * 24 * 3600, 'Older than 1 Week', '#2f7ed8', 'diamond'),
                               (ts_now - 7 * 24 * 3600, ts_now - 24 * 3600, 'Last Week', '#00CC00', 'circle'),
                               (ts_now - 24 * 3600, ts_now, 'Last 24 Hours', '#FF0000', 'square') )
            series = []

            for t_start, t_end, ser_name, ser_color, ser_symbol in ser_params:
                mask = (df_all.index >= t_start) & (df_all.index < t_end)
                pts = [ {'x': bmsapp.data_util.round4(row['X']), 'y': bmsapp.data_util.round4(row['Y']), 'name': row['name'] } 
                        for ix, row in df_all[mask].iterrows() ]
                if len(pts):
                    series.append( { 'data': pts, 'name': ser_name, 'color': ser_color, 'marker': {'symbol': ser_symbol} } )

        # create the X and Y axis labels and the series in Highcharts format
        x_label = '%s, %s' % (sensorX.title, sensorX.unit.label)
        y_label = '%s, %s' % (sensorY.title, sensorY.unit.label)

        opt = self.get_chart_options()
        opt['series'] = series
        opt['tooltip']['pointFormat'] = 'X: <b>{point.x}</b><br/>Y: <b>{point.y}</b><br/><b>{point.name}</b>'
        opt['plotOptions']['series']['turboThreshold'] = 0    # with object points, need to disable to allow all points to be displayed
        opt['yAxis']['title']['text'] = y_label
        opt['xAxis']['title']['text'] = x_label
        opt['chart']['type'] = 'scatter'
        opt['plotOptions']['series']['marker']['enabled'] = True
        opt['title']['text'] = sensorY.title + " vs. " + sensorX.title
        opt['title']['style']['fontSize'] = '20px'

        html = '<div id="chart_container"></div>'
        return {'html': html, 'objects': [('highcharts', opt)]}

