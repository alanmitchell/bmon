"""
This module holds classes that create the HTML and supply the data for Charts and
Reports.
"""
import time, logging
from django.template import Context, loader
from django.core.urlresolvers import reverse
import pandas as pd, numpy as np, xlwt
import models, global_vars, data_util, view_util
from readingdb import bmsdata
from calcs import transforms

# Make a logger for this module
_logger = logging.getLogger('bms.' + __name__)


class BldgChartType:
    """Class to provide descriptive information about a particular type of chart related
    to one building.
    """

    def __init__(self, id, title, class_name, multi_sensor_select):
        """Initializes the chart type.

            Args:
                id (int): ID number uniquely identifying this chart type.
                title (string): Text that will be displayed in select controls and chart titles.
                class_name (string): The name of the Python class in this charts.py used to create the chart.
                multi_sensor_select (bool): True if chart allows selection of multiple sensors to plot.
        """
        self.id = id        
        self.title = title  
        self.class_name = class_name   
        self.multi_sensor_select = multi_sensor_select

# These are the possible chart types currently implemented, in the order they will be 
# presented to the User.
BLDG_CHART_TYPES = [
    BldgChartType(0, 'Dashboard', 'Dashboard', False),
    BldgChartType(1, 'Current Sensor Values', 'CurrentValues', False),
    BldgChartType(2, 'Plot Sensor Values over Time', 'TimeSeries', True),
    BldgChartType(3, 'Hourly Profile of a Sensor', 'HourlyProfile', False),
    BldgChartType(4, 'Histogram of a Sensor', 'Histogram', False),
    BldgChartType(5, 'Sensor X vs Y Scatter Plot', 'XYplot', False),
    BldgChartType(6, 'Download Sensor Data to Excel', 'ExportData', True)
]

# The ID of the Time Series chart above, as it is needed in code below.
TIME_SERIES_CHART_ID = 2

def find_chart_type(chart_id):
    """Returns the BldgChartType for a given ID.

        Args:
            chart_id (int): The ID number of the requested chart type.

        Returns:
            The BldgChartType having the requested ID.  Returns None if no match.
    """
    for ch in BLDG_CHART_TYPES:
        if ch.id == chart_id:
            return ch

    return None

def get_chart_object(bldg_id, chart_id, request_params):
    """Returns the appropriate chart object identified by the arguments.

        Args:
            bldg_id (int or the string 'multi'): Identifies the building this chart will be used for.
                If bldg_id == 'multi', the chart is a multiple-building chart.
            chart_id (int): The ID number uniquely identifying the chart.
            request_params: The parameters (request.GET) passed in by the user further qualifying the chart.

        Returns:
            A chart object descending from BaseChart.
    """

    if bldg_id=='multi':
        chart_info = models.MultiBuildingChart.objects.get(id=chart_id)
        class_name = chart_info.chart_type.class_name
    else:
        chart_info = find_chart_type(chart_id)
        class_name = chart_info.class_name

    # get a reference to the class referred to by class_name
    chart_class = globals()[class_name]

    # instantiate and return the chart from this class
    return chart_class(chart_info, bldg_id, request_params)


class BaseChart(object):
    """Base class for all of the chart classes.
    """

    def __init__(self, chart_info, bldg_id, request_params):
        """
        'chart' is the models.BuildingChart object for the chart.  'request_params' are the parameters
        passed in by the user through the Get http request.
        """
        self.chart_info = chart_info
        self.bldg_id = bldg_id

        # if this is a chart for a single building, get the associated building model object
        if bldg_id != 'multi':
            self.building = models.Building.objects.get(id=bldg_id)

        self.request_params = request_params

        # the name of this class as it determines templates to use and JavaScript functions to call.
        self.class_name = self.__class__.__name__

        # for the multi-building chart object, take the keyword parameter string 
        # and convert it to a dictionary.
        if bldg_id == 'multi':
            self.chart_params = transforms.makeKeywordArgs(chart_info.parameters)

        # Make a context variable for use by templates including useful template
        # data.
        self.context = Context( {} )

    def html(self, selected_sensor=None):
        """
        Returns the HTML necessary to configure and display the chart.
        """
        template = loader.get_template('bmsapp/%s.html' % self.class_name)
        self.context['chart_func'] = self.class_name    # this is the name of a Javascript function to call in the browser
        if self.bldg_id != 'multi':
            self.context['select_sensor'] = self.make_sensor_select_html(selected_sensor)
        return template.render(self.context)

    def data(self):
        """
        This method should be overridden.  Returns the series data and any other
        data that is affected by user configuration of the chart.
        """
        return [1,2,3]

    def make_sensor_select_html(self, selected_sensor=None, control_id='select_sensor'):
        """Helper method that returns the HTML for a Select control that allows 
        selection of a sensor(s) associated with this building.  
        'selected_sensor' is the ID of the sensor to select; if not provided, 
        the first sensor is selected.
        'control_id' is the string to use for the HTML Select control id and name.
        """

        # convert the selected sensor to an integer, if possible
        select_id = view_util.to_int(selected_sensor)

        grp = ''    # tracks the sensor group
        html = '<select id="%s" name="%s" ' % (control_id, control_id)
        html += 'multiple="multiple">' if self.chart_info.multi_sensor_select else '>'
        first_sensor = True
        for b_to_sen in self.building.bldgtosensor_set.all():
            if b_to_sen.sensor_group != grp:
                if first_sensor == False:
                    # Unless this is the first group, close the prior group
                    html += '</optgroup>'
                html += '<optgroup label="%s">' % b_to_sen.sensor_group.title
                grp = b_to_sen.sensor_group
            sensor_id = b_to_sen.sensor.sensor_id
            html += '<option value="%s" %s>%s</option>' % \
                (b_to_sen.sensor.sensor_id, 'selected' if (first_sensor and select_id==None) or (b_to_sen.sensor.id==select_id) else '', b_to_sen.sensor.title)
            first_sensor = False
        html += '</optgroup></select>'
        return html

    def get_ts_range(self):
        """
        Returns the start and stop timestamp as determined by the GET parameters that were posted
        from the "time_period" Select control.
        """
        tm_per = self.request_params['time_period']
        if tm_per != "custom":
            st_ts = int(time.time()) - int(tm_per) * 24 * 3600
            end_ts = time.time() + 3600.0    # adding an hour to be sure all records are caught
        else:
            st_date = self.request_params['start_date']
            st_ts = data_util.datestr_to_ts(st_date) if len(st_date) else 0
            end_date = self.request_params['end_date']
            end_ts = data_util.datestr_to_ts(end_date + " 23:59:59") if len(end_date) else time.time() + 3600.0

        return st_ts, end_ts


class Dashboard(BaseChart):

    def html(self, selected_sensor=None):

        # create a report title
        self.context['report_title'] = '%s Dashboard' % self.building.title
        return super(Dashboard, self).html()


    def data(self):

        # open the database 
        db = bmsdata.BMSdata(global_vars.DATA_DB_FILENAME)

        widgets = []
        cur_row = []
        cur_row_num = None
        cur_time = time.time()   # needed for calculating how long ago reading occurred
        for dash_item in self.building.dashboarditem_set.all():
            if dash_item.row_number != cur_row_num:
                if len(cur_row):
                    widgets.append(cur_row)
                cur_row = []
                cur_row_num = dash_item.row_number
    
            new_widget = {'type': dash_item.widget_type}
            # Determine title, either from user entry or from sensor's title
            new_widget['title'] = dash_item.title if len(dash_item.title) or (dash_item.sensor is None) else dash_item.sensor.sensor.title

            if dash_item.sensor is not None:
                last_read = db.last_read(dash_item.sensor.sensor.sensor_id)
                cur_value = float(formatCurVal(last_read['val'])) if last_read else None
                age_secs = time.time() - last_read['ts'] if last_read else None    # how long ago reading occurred
                minAxis, maxAxis = dash_item.get_axis_range()
                new_widget.update( {'units': dash_item.sensor.sensor.unit.label,
                                    'value': cur_value,
                                    'minNormal': dash_item.minimum_normal_value,
                                    'maxNormal': dash_item.maximum_normal_value,
                                    'minAxis': minAxis,
                                    'maxAxis': maxAxis,
                                    'urlClick': reverse('bmsapp.views.reports', args=(self.bldg_id, TIME_SERIES_CHART_ID, dash_item.sensor.sensor.id)),
                                   } )
                # check to see if data is older than 2 hours or missing, and change widget type if so.
                if cur_value is None:
                    new_widget['type'] = models.DashboardItem.NOT_CURRENT
                    new_widget['age'] = 'Not Available'
                elif 7200 <= age_secs < 86400:
                    new_widget['type'] = models.DashboardItem.NOT_CURRENT
                    new_widget['age'] = '%.1f hours Old' % (age_secs/3600.0)
                elif age_secs >= 86400:
                    new_widget['type'] = models.DashboardItem.NOT_CURRENT
                    new_widget['age'] = '%.1f days Old' % (age_secs/86400.0)

            cur_row.append(new_widget)

        # append the last row if anything is present in that row
        if len(cur_row):
            widgets.append(cur_row)

        # close the reading database
        db.close()

        return { 'widgets': widgets }


class TimeSeries(BaseChart):

    def data(self):
        """
        Returns the data for a Time Series chart.  Return value is a dictionary
        containing the dynamic data used to draw the chart.
        """
        # open the database 
        db = bmsdata.BMSdata(global_vars.DATA_DB_FILENAME)

        # Determine the sensors to plot. This creates a list of Sensor objects to plot.
        sensor_list = [ models.Sensor.objects.get(sensor_id=id) for id in self.request_params.getlist('select_sensor') ]

        # determine the Y axes that will be needed to cover the the list of sensor, based on the labels
        # of the units
        y_axes_ids = list(set([sensor.unit.label for sensor in sensor_list]))

        # get the requested averaging interval in hours
        averaging_hours = float(self.request_params['averaging_time'])

        # determine the start time for selecting records and loop through the selected
        # records to get the needed dataset
        st_ts, end_ts = self.get_ts_range()

        # Create the series to plot
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
            series_opt = {'data': series_data, 
                          'name': sensor.title, 
                          'yAxis': sensor.unit.label,
                          'lineWidth': line_width}
            # if the sensor has defined states, make the series a Step type series.
            if sensor.unit.measure_type == 'state':
                series_opt['step'] = 'left'
            series.append( series_opt )

        return {"series": series, "y_axes": y_axes_ids}


class HourlyProfile(BaseChart):

    def data(self):
        """
        Returns the data for an Hourly Profile chart.  Return value is a dictionary
        containing the dynamic data used to draw the chart.
        """
        # open the database 
        db = bmsdata.BMSdata(global_vars.DATA_DB_FILENAME)

        # determine the sensor to plot from the sensor selected by the user.
        the_sensor = models.Sensor.objects.get(sensor_id=self.request_params['select_sensor'])

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

        return {"series": series, 'y_label': yTitle}

class Histogram(BaseChart):

    def data(self):
        """
        Returns the data for an Histogram chart.  Return value is a dictionary
        containing the dynamic data used to draw the chart.
        """
        # open the database 
        db = bmsdata.BMSdata(global_vars.DATA_DB_FILENAME)

        # determine the sensor to plot from the sensor selected by the user.
        the_sensor = models.Sensor.objects.get(sensor_id=self.request_params['select_sensor'])

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
                series.append( {'data': data_util.histogram_from_series(avg_series), 'name': series_name} )
        else:
            series = []

        return {"series": series, "x_label": the_sensor.unit.label}


def formatCurVal(val):
    """
    Helper function for formatting current values to 3 significant digits, but 
    avoiding the use of scientific notation for display
    """
    if val >= 1000.0:
        return '{:,}'.format( int(float('%.3g' % val)))
    else:
        return '%.3g' % val

class CurrentValues(BaseChart):

    def html(self, selected_sensor=None):

        # open the database 
        db = bmsdata.BMSdata(global_vars.DATA_DB_FILENAME)

        # make a list with the major items being a sensor group and the 
        # minor items being a list of sensor info: 
        #   (sensor name, most recent value, units, how many minutes ago value occurred)
        cur_group = ''
        cur_group_sensor_list = []
        sensor_list = []
        cur_time = time.time()   # needed for calculating how long ago reading occurred
        for b_to_sen in self.building.bldgtosensor_set.all():
            if b_to_sen.sensor_group.title != cur_group:
                if cur_group:
                    sensor_list.append( (cur_group, cur_group_sensor_list) )
                cur_group = b_to_sen.sensor_group.title
                cur_group_sensor_list = []
            last_read = db.last_read(b_to_sen.sensor.sensor_id)
            cur_value = formatCurVal(last_read['val']) if last_read else ''
            minutes_ago = '%.1f' % ((cur_time - last_read['ts'])/60.0) if last_read else ''
            cur_group_sensor_list.append( {'title': b_to_sen.sensor.title, 
                                           'cur_value': cur_value, 
                                           'unit': b_to_sen.sensor.unit.label, 
                                           'minutes_ago': minutes_ago,
                                           'sensor_id': b_to_sen.sensor.id} )
        # add the last group
        if cur_group:
            sensor_list.append( (cur_group, cur_group_sensor_list) )

        # close the reading database
        db.close()

        # make this sensor list available to the template
        self.context['sensor_list'] = sensor_list

        # create a report title
        self.context['report_title'] = 'Current Values: %s' % self.building.title

        # template needs building ID.
        self.context['bldg_id'] = self.bldg_id

        # Get the ID of the first time series chart for this building
        self.context['ts_chart_id'] = TIME_SERIES_CHART_ID

        return super(CurrentValues, self).html()


class XYplot(BaseChart):

    def html(self, selected_sensor=None):
        """Return the html necessary for the XY scatter plot.
        """
        # Make the HTML for the X and Y sensor and save in the context
        self.context['select_sensorX'] = self.make_sensor_select_html(selected_sensor, control_id='select_sensorX')
        self.context['select_sensorY'] = self.make_sensor_select_html(selected_sensor, control_id='select_sensorY')
        return super(XYplot, self).html()

    def data(self):
        """
        Returns the data for a scatter plot of one sensor vs. another.  
        Return value is a dictionary containing the dynamic data used to draw the chart.
        """
        # open the database 
        db = bmsdata.BMSdata(global_vars.DATA_DB_FILENAME)

        # determine the X and Y sensors to plot from those sensors selected by the user.
        sensorX = models.Sensor.objects.get(sensor_id=self.request_params['select_sensorX'])
        sensorY = models.Sensor.objects.get(sensor_id=self.request_params['select_sensorY'])

        # make a timestamp binning object
        binner = data_util.TsBin(float(self.request_params['averaging_time']))

        # determine the start and end time for selecting records
        st_ts, end_ts = self.get_ts_range()

        # get the dividing date, if there is one
        div_date = self.request_params['divide_date']
        div_ts = data_util.datestr_to_ts(div_date) if len(div_date) else 0


        # The list that will hold each Highcharts series
        series = []

        # get the X and Y sensor records and perform the requested averaging
        db_recsX = db.rowsForOneID(sensorX.sensor_id, st_ts, end_ts)
        db_recsY = db.rowsForOneID(sensorY.sensor_id, st_ts, end_ts)
        if len(db_recsX)>0 and len(db_recsY)>0:
            # both sensors have some data, so proceed to average the data points
            dfX = pd.DataFrame(db_recsX).set_index('ts').groupby(binner.bin).mean()
            dfX.columns = ['X']
            dfY = pd.DataFrame(db_recsY).set_index('ts').groupby(binner.bin).mean()
            dfY.columns = ['Y']

            # Join the X and Y values for the overlapping time intervals and make
            # a list of points.
            df_all = dfX.join(dfY, how='inner')  # inner join does intersection of timestamps

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
                pts = [ (data_util.round4(row['X']), data_util.round4(row['Y'])) for ix, row in df_all[mask].iterrows() ]
                if len(pts):
                    series.append( { 'data': pts, 'name': ser_name, 'color': ser_color, 'marker': {'symbol': ser_symbol} } )

        # create the X and Y axis labels and the series in Highcharts format
        x_label = '%s, %s' % (sensorX.title, sensorX.unit.label)
        y_label = '%s, %s' % (sensorY.title, sensorY.unit.label)

        return {"series": series, "x_label": x_label, "y_label": y_label}


class ExportData(BaseChart):

    def download_many(self, resp_object):
        """
        Extracts the requested sensor data, averages it, and creates an Excel spreadsheet
        which is then written to the returned HttpResponse object 'resp_object'.
        """

        # determine a name for the spreadsheet and fill out the response object
        # headers.
        xls_name = 'sensors_%s.xls' % data_util.ts_to_datetime().strftime('%Y-%m-%d_%H%M%S')
        resp_object['Content-Type']= 'application/vnd.ms-excel'
        resp_object['Content-Disposition'] = 'attachment; filename=%s' % xls_name
        resp_object['Content-Description'] = 'Sensor Data - readable in Excel'

        # start the Excel workbook and format the first row and first column
        wb = xlwt.Workbook()
        ws = wb.add_sheet('Sensor Data')
        # column title style
        t1_style = xlwt.easyxf('font: bold on; borders: bottom thin; align: wrap on, vert bottom, horiz center')
        # date formatting style
        dt_style = xlwt.easyxf(num_format_str='M/D/yy  h:mm AM/PM;@')

        ws.write(0, 0, "Timestamp", t1_style)
        ws.col(0).width = 4300

        # make a timestamp binning object
        binner = data_util.TsBin(float(self.request_params['averaging_time']))

        # open the database 
        db = bmsdata.BMSdata(global_vars.DATA_DB_FILENAME)

        # walk through sensors, setting column titles and building a Pandas DataFrame
        # that aligns the averaged timestamps of the different sensors.
        col = 1   # tracks spreadsheet column
        df = pd.DataFrame()
        blank_col_names = []   # need to remember columns that have no readings
        for id in self.request_params.getlist('select_sensor'):
            sensor = models.Sensor.objects.get(sensor_id=id)

            # write column heading in spreadsheet
            ws.write(0, col, '%s, %s' % (sensor.title, sensor.unit.label), t1_style)
            ws.col(col).width = 3600

            # determine the start time for selecting records and make a DataFrame from
            # the records
            st_ts, end_ts = self.get_ts_range()
            db_recs = db.rowsForOneID(sensor.sensor_id, st_ts, end_ts)
            if len(db_recs)!=0:
                df_new = pd.DataFrame(db_recs).set_index('ts')
                df_new.columns = ['col%03d' % col]
                df_new = df_new.groupby(binner.bin).mean()    # do requested averaging

                # join this with the existing DataFrame, taking the union of all timestamps
                df = df.join(df_new, how='outer')
            else:
                # there are no records.  Save this column name to be added at end of join
                # process.  Can't add the column right now because DataFrame may be totally
                # empty, and it doesn't seem possible to add a column to an empty DataFrame.
                blank_col_names.append('col%03d' % col)

            col += 1
        
        # add any blank columns to the dataframe
        for col_name in blank_col_names:
            df[col_name] = np.NaN
        # but now need sort the columns back to order they arrived
        df = df.sort_index(axis=1)

        # put the data in the spreadsheet
        row = 1
        for ix, ser in df.iterrows():
            ws.write(row, 0, data_util.ts_to_datetime(ix), dt_style)
            col = 1
            for v in ser.values:
                if not np.isnan(v):
                    ws.write(row, col, float('%.4g' % v))
                col += 1
            row += 1
            # flush the row data every 1000 rows to save memory.
            if (row % 1000) == 0:
                ws.flush_row_data()

        # Write the spreadsheet to the HttpResponse object
        wb.save(resp_object)
        return resp_object


# **********************  Multi-Building Charts Below Here ***************************

class NormalizedByDDbyFt2(BaseChart):
    """
    Chart that normalizes a quantity by degree-days and floor area.  Value being normalized
    must be a rate per hour quantity; the normalization integrates by the hour.  For example
    a Btu/hour value integrates to total Btus in this chart.

    CHART PARAMETERS:
        'base_temp': the base temperature in degrees F to use in the degree-day calculation.
        'value_units': the units, for example 'Btus', to label the Y-axis with; '/ft2/degree-day'
            will be appended to this value.
        'multiplier' (optional, defaults to 1.0): a scaling multiplier that will be applied to 
            the final value for a building.

    BUILDING PARAMETERS:
        'id_value': the sensor ID of the quantity to sum up and normalize.
        'id_out_temp': the sensor ID of an outdoor temperature measurement used to calculate
            degree-days.
        'floor_area': the floor area in square feet of the building.
    """
    
    def data(self):
        """
        Returns the data for a chart that normalizes a value by degree-days and floor area.
        Return value is a dictionary containing the dynamic data needed to draw the chart.
        """

        # open the database 
        db = bmsdata.BMSdata(global_vars.DATA_DB_FILENAME)

        # get the time range  used in the analysis
        st_ts, end_ts = self.get_ts_range()

        # make a timestamp binning object to bin the data into 1 hour intervals
        binner = data_util.TsBin(1.0)

        # get the base temperature for degree day calculations
        base_temp = self.chart_params['base_temp']

        # get the scaling multiplier if present in the parameters
        multiplier = self.chart_params.get('multiplier', 1.0)

        # start a list of building names and energy use values
        bldg_names = []
        values = []

        # loop through the buildings determining the Btu/ft2/dd for each building
        for bldg_info in self.chart_info.chartbuildinginfo_set.all():

            bldg_name = bldg_info.building.title   # get the building name

            # get the parameters associated with this building
            bldg_params = transforms.makeKeywordArgs(bldg_info.parameters)

            # get the value records and average into one hour intervals
            db_recs = db.rowsForOneID(bldg_params['id_value'], st_ts, end_ts)
            if len(db_recs)==0:
                continue
            df = pd.DataFrame(db_recs).set_index('ts')
            df.columns = ['value']
            df = df.groupby(binner.bin).mean()    # do one hour averaging

            # get outdoor temp data and average into one hour intervals.  
            db_recs = db.rowsForOneID(bldg_params['id_out_temp'], st_ts, end_ts)
            if len(db_recs)==0:
                continue
            df_temp = pd.DataFrame(db_recs).set_index('ts')
            df_temp.columns = ['temp']
            df_temp = df_temp.groupby(binner.bin).mean()    # do one hour averaging

            # inner join, matching timestamps
            df = df.join(df_temp, how='inner') 

            # calculate total degree-days; each period is an hour, so need to divide by
            # 24.0 at end.
            total_dd = sum([max(base_temp - t, 0.0) for t in df['temp'].values]) / 24.0

            # calculate total of the values and apply the scaling multiplier
            total_values = df['value'].sum() * multiplier

            # if there are any degree-days, append a new point to the list
            if total_dd > 0.0:
                bldg_names.append(bldg_name)
                values.append( round(total_values / total_dd / bldg_params['floor_area'], 2) )

        return {"series": [{'data': values}], "bldgs": bldg_names, "value_units": self.chart_params["value_units"]}

class NormalizedByFt2(BaseChart):
    
    """
    Chart that normalizes a quantity by floor area.  The value being normalized is first averaged
    over the requested time period and then divided by floor area.  A scaling multiplier is optionally
    applied to the result.

    CHART PARAMETERS:
        'value_units': the units, for example 'kWh/year', to label the Y-axis with; '/ft2'
            will be appended to this value.
        'multiplier' (optional, defaults to 1.0): a scaling multiplier that will be applied to 
            the final value for a building.

    BUILDING PARAMETERS:
        'id_value': the sensor ID of the quantity to sum up and normalize.
        'floor_area': the floor area in square feet of the building.
    """
    
    def data(self):
        """
        Returns the data for a chart that normalizes a value by floor area.
        Return value is a dictionary containing the dynamic data needed to draw the chart.
        """

        # open the database 
        db = bmsdata.BMSdata(global_vars.DATA_DB_FILENAME)

        # get the time range  used in the analysis
        st_ts, end_ts = self.get_ts_range()

        # get the scaling multiplier if present in the parameters
        multiplier = self.chart_params.get('multiplier', 1.0)

        # start a list of building names and energy use values
        bldg_names = []
        values = []

        # loop through the buildings determining the value per ft2 for each building
        for bldg_info in self.chart_info.chartbuildinginfo_set.all():

            bldg_name = bldg_info.building.title   # get the building name

            # get the parameters associated with this building
            bldg_params = transforms.makeKeywordArgs(bldg_info.parameters)

            # get the value records
            db_recs = db.rowsForOneID(bldg_params['id_value'], st_ts, end_ts)
            if len(db_recs)==0:
                continue

            # make a list of the values
            val_list = [rec['val'] for rec in db_recs]
            ct = len(val_list)
            if ct > 0:
                normalized_val = sum(val_list) / float(ct) / bldg_params['floor_area'] * multiplier
                bldg_names.append(bldg_name)
                values.append( round( normalized_val, 2) )

        return {"series": [{'data': values}], "bldgs": bldg_names, "value_units": self.chart_params["value_units"]}
