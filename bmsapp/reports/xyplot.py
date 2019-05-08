import time
from datetime import datetime
from datetime import timedelta
from dateutil import parser
import numpy as np
import pandas as pd, pytz
import bmsapp.models, bmsapp.data_util
from . import basechart

class XYplot(basechart.BaseChart):
    """Class that creates XY Plot.
    """

    # see BaseChart for definition of these constants
    CTRLS = 'refresh, xy_controls, time_period_group, get_embed_link'

    def result(self):
        """
        Returns the HTML and chart object for a scatter plot of one sensor vs. another.  
        """

        # determine the X and Y sensors to plot from those sensors selected by the user.
        sensorX = bmsapp.models.Sensor.objects.get(pk=self.request_params['select_sensor_x'])
        sensorY = bmsapp.models.Sensor.objects.get(pk=self.request_params['select_sensor_y'])

        # determine the averaging time
        averaging_hours = float(self.request_params['averaging_time_xy'])

        # get the building's timezone
        tz = pytz.timezone(self.timezone)

        # determine the start and end time for selecting records
        st_ts, end_ts = self.get_ts_range()

        # get the dividing date, if there is one
        div_datestring = self.request_params['div_date']
        div_dt = tz.localize(parser.parse(div_datestring)) if len(div_datestring) else None


        # The list that will hold each series
        series = []

        # get the X and Y sensor records and perform the requested averaging
        dfX = self.reading_db.dataframeForOneID(sensorX.sensor_id, st_ts, end_ts, tz)
        dfY = self.reading_db.dataframeForOneID(sensorY.sensor_id, st_ts, end_ts, tz)

        if not dfX.empty and not dfY.empty:  # both sensors have some data, so proceed to average the data points
            
            dfX = bmsapp.data_util.resample_timeseries(dfX,averaging_hours)
            dfX.rename(columns = {'val':'X'}, inplace = True)

            dfY = bmsapp.data_util.resample_timeseries(dfY,averaging_hours)
            dfY.rename(columns = {'val':'Y','ts':'tsY'}, inplace = True)

            # Join the X and Y values for the overlapping time intervals and make
            # a list of points.
            df_all = dfX.join(dfY, how='inner')  # inner join does intersection of timestamps

            # make sure there are matched records before continuing
            if len(df_all):

                # add a point name column to be used in the tooltip.
                df_all['name'] = df_all.index.strftime('%a %m/%d/%y %H:%M')

                # add a column identifying whether point is in occupied or unoccupied period.
                resolution = self.occupied_resolution()
                if (self.schedule is None) or (resolution is None):
                    # no schedule or data doesn't lend itself to classifying
                    # consider all points to be occupied
                    df_all['occupied'] = 1
                else:
                    df_all['occupied'] = [self.schedule.is_occupied(ts, resolution=resolution) for ts in df_all.ts]

                # Set up the parameters for the different series of data
                # Required Info is (starting datetime, ending datetime, occupied status (0 or 1), series name, 
                # series color, series symbol, series radius, series zindex).
                now_dt = datetime.now()
                if div_dt:
                    # A dividing date was provided by the user.
                    div_dt = div_dt.replace(tzinfo=None)  # needs to be naive
                    ser_params = ( (datetime(1970,1,1), div_dt, 1, 'Prior to %s' % div_datestring, '#2f7ed8', 'circle', 4.5),
                                   (datetime(1970,1,1), div_dt, 0, 'Prior to %s, Unoccupied' % div_datestring, '#2f7ed8', 'triangle-up', 3),
                                   (div_dt, now_dt, 1, '%s and beyond' % div_datestring, '#FF0000', 'circle', 4.5),
                                   (div_dt, now_dt, 0, '%s and beyond, Unoccupied' % div_datestring, '#FF0000', 'triangle-up', 3) )
                else:
                    # Divide data by how recent it is.
                    ser_params = ( (now_dt - timedelta(days=1), now_dt, 1, 'Last 24 Hours', '#FF0000', 'circle', 4.5),
                                   (now_dt - timedelta(days=1), now_dt, 0, 'Last 24 Hours, Unoccupied', '#FF0000', 'triangle-up', 3),
                                   (now_dt - timedelta(days=7), now_dt - timedelta(days=1), 1, 'Last 7 Days', '#00CC00', 'circle', 4.5),
                                   (now_dt - timedelta(days=7), now_dt - timedelta(days=1), 0, 'Last 7 Days, Unoccupied', '#00CC00', 'triangle-up', 3),
                                   (datetime(1970,1,1), now_dt - timedelta(days=7), 1, '7+ Days Old', '#2f7ed8', 'circle', 4.5),
                                   (datetime(1970,1,1), now_dt - timedelta(days=7), 0, '7+ Days Old, Unoccupied', '#2f7ed8', 'triangle-up', 3),
                                  )

                for t_start, t_end, occup, ser_name, ser_color, ser_symbol, radius in reversed(ser_params):
                    mask = (df_all.index >= t_start) & (df_all.index < t_end) & (df_all.occupied==occup)
                    if mask.max():
                        series.append( {'x': np.char.mod('%.4g',df_all[mask].X.values).astype(float).tolist(),
                                        'y': np.char.mod('%.4g',df_all[mask].Y.values).astype(float).tolist(),
                                        'text': df_all[mask].name.values.tolist(),
                                        'type': 'scatter',
                                        'mode': 'markers', 
                                        'name': ser_name,
                                        'marker': { 'color': ser_color,
                                                    'symbol': ser_symbol,
                                                    'size': radius * 2
                                                  }
                                        } )

        # create the X and Y axis labels and the series
        x_label = '%s, %s' % (sensorX.title, sensorX.unit.label)
        y_label = '%s, %s' % (sensorY.title, sensorY.unit.label)

        opt = self.get_chart_options('plotly')
        opt['data'] = series
        opt['layout']['title'] = sensorY.title + " vs. " + sensorX.title
        opt['layout']['xaxis']['title'] =  x_label
        opt['layout']['yaxis']['title'] =  y_label
        opt['layout']['legend']['traceorder'] = 'reversed'

        html = basechart.chart_config.chart_container_html(opt['layout']['title'])

        return {'html': html, 'objects': [('plotly', opt)]}

