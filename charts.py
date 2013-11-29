'''
This module holds classes that create the HTML and supply the data for Charts and
Reports.
'''
import models, bmsdata, global_vars, transforms, data_util, view_util
from django.template import Context, loader
import time, pandas as pd, numpy as np, logging, xlwt

# Make a logger for this module
_logger = logging.getLogger('bms.' + __name__)


class BldgChart(object):
    '''
    Base class for all of the chart classes.
    '''

    def __init__(self, chart, get_params):
        '''
        'chart' is the models.BuildingChart object for the chart.  'get_params' are the parameters
        passed in by the user through the Get http request.
        '''
        self.chart = chart
        self.get_params = get_params

        # the name of the class used to build and process this chart.
        self.class_name = chart.chart_type.class_name 

        # for the chart object, take the keyword parameter string and convert it to a dictionary.
        chart_params = transforms.makeKeywordArgs(chart.parameters)

        # for any parameter name that starts with "id_", strip the "id_" from the name and substitute
        # the models.Sensor object that corresponds to the id value.
        for nm, val in chart_params.items():
            if nm.startswith('id_'):
                del chart_params[nm]   # delete this item from the dictionary
                # make a new item in the dictionary to hold the sensor identified by this id
                chart_params[ nm[3:] ] = models.Sensor.objects.get(sensor_id=val)
        self.chart_params = chart_params   # store results in object

        # Make a context variable for use by templates including useful template
        # data.
        self.context = Context( {} )


    def html(self, selected_sensor=None):
        '''
        Returns the HTML necessary to configure and display the chart.
        '''
        template = loader.get_template('bmsapp/%s.html' % self.class_name)
        self.context['chart_func'] = self.class_name    # this is the name of a Javascript function to call in the browser
        return template.render(self.context)


    def data(self):
        '''
        This method should be overridden.  Returns the series data and any other
        data that is affected by user configuration of the chart.
        '''
        return [1,2,3]

    def make_sensor_select_html(self, multi_select=False, selected_sensor=None):
        '''
        Helper method that returns the HTML for a Select control that allows 
        selection of a sensor associated with this building.  If 'multi_select'
        is True, multi-select Select HTML is returned.  'selected_sensor' is the
        ID of the sensor to select; if not provided, the first sensor is selected.
        '''

        # convert the selected sensor to an integer, if possible
        select_id = view_util.to_int(selected_sensor)

        grp = ''    # tracks the sensor group
        html = '<select id="select_sensor" name="select_sensor" '
        html += 'multiple="multiple">' if multi_select else '>'
        first_sensor = True
        for b_to_sen in self.chart.building.bldgtosensor_set.all():
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
        '''
        Returns the start and stop timestamp as determined by the GET parameters that were posted
        from the "time_period" Select control.
        '''
        tm_per = self.get_params['time_period']
        if tm_per != "custom":
            st_ts = int(time.time()) - int(tm_per) * 24 * 3600
            end_ts = time.time() + 3600.0    # adding an hour to be sure all records are caught
        else:
            st_date = self.get_params['start_date']
            st_ts = data_util.datestr_to_ts(st_date) if len(st_date) else 0
            end_date = self.get_params['end_date']
            end_ts = data_util.datestr_to_ts(end_date + " 23:59:59") if len(end_date) else time.time() + 3600.0

        return st_ts, end_ts


class TimeSeries(BldgChart):

    def html(self, selected_sensor=None):
        if 'sensor' in self.chart_params:
            self.context['select_sensor'] = ''
        else:
            # provide sensor selection 
            self.context['select_sensor'] = self.make_sensor_select_html(True, selected_sensor)
        return super(TimeSeries, self).html()

    def data(self):
        '''
        Returns the data for a Time Series chart.  Return value is a dictionary
        containing the dynamic data used to draw the chart.
        '''
        # open the database 
        db = bmsdata.BMSdata(global_vars.DATA_DB_FILENAME)

        # determine the sensors to plot either from the chart configuration or from the
        # sensor selected by the user.  This creates a list of Sensor objects to plot
        if 'sensor' in self.chart_params:
            sensor_list = [ self.chart_params['sensor'] ]   # the sensor to chart
        else:
            sensor_list = [ models.Sensor.objects.get(sensor_id=id) for id in self.get_params.getlist('select_sensor') ]

        # determine the Y axes that will be needed to cover the the list of sensor, based on the labels
        # of the units
        y_axes_ids = list(set([sensor.unit.label for sensor in sensor_list]))

        # get the requested averaging interval in hours
        averaging_hours = float(self.get_params['averaging_time'])

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


class HourlyProfile(BldgChart):

    def html(self, selected_sensor=None):
        if 'sensor' in self.chart_params:
            self.context['select_sensor'] = ''
        else:
            # provide sensor selection 
            self.context['select_sensor'] = self.make_sensor_select_html(False, selected_sensor)
        return super(HourlyProfile, self).html()


    def data(self):
        '''
        Returns the data for an Hourly Profile chart.  Return value is a dictionary
        containing the dynamic data used to draw the chart.
        '''
        # open the database 
        db = bmsdata.BMSdata(global_vars.DATA_DB_FILENAME)

        # determine the sensor to plot either from the chart configuration or from the
        # sensor selected by the user.
        if 'sensor' in self.chart_params:
            the_sensor = self.chart_params['sensor']   # the sensor to chart
        else:
            the_sensor = models.Sensor.objects.get(sensor_id=self.get_params['select_sensor'])

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
        if 'normalize' in self.get_params:
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

class Histogram(BldgChart):

    def html(self, selected_sensor=None):
        if 'sensor' in self.chart_params:
            self.context['select_sensor'] = ''
        else:
            # provide sensor selection 
            self.context['select_sensor'] = self.make_sensor_select_html(False, selected_sensor)
        return super(Histogram, self).html()


    def data(self):
        '''
        Returns the data for an Histogram chart.  Return value is a dictionary
        containing the dynamic data used to draw the chart.
        '''
        # open the database 
        db = bmsdata.BMSdata(global_vars.DATA_DB_FILENAME)

        # determine the sensor to plot either from the chart configuration or from the
        # sensor selected by the user.
        if 'sensor' in self.chart_params:
            the_sensor = self.chart_params['sensor']   # the sensor to chart
        else:
            the_sensor = models.Sensor.objects.get(sensor_id=self.get_params['select_sensor'])

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
    '''
    Helper function for formatting current values to 3 significant digits, but 
    avoiding the use of scientific notation for display
    '''
    if val >= 1000.0:
        return '{:,}'.format( int(float('%.3g' % val)))
    else:
        return '%.3g' % val

class CurrentValues(BldgChart):

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
        for b_to_sen in self.chart.building.bldgtosensor_set.all():
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

        # make this sensor list available to the template
        self.context['sensor_list'] = sensor_list

        # create a report title
        self.context['report_title'] = 'Current Values: %s' % self.chart.building.title

        # template needs building ID.
        bldg_id = self.chart.building.id
        self.context['bldg_id'] = bldg_id

        # Get the ID of the first time series chart for this building
        self.context['ts_chart_id'] = models.BuildingChart.objects.filter(building__id=bldg_id).filter(chart_type__class_name='TimeSeries')[0].id

        return super(CurrentValues, self).html()


class ExportData(BldgChart):

    def html(self, selected_sensor=None):
        # provide sensor selection multi-select box
        self.context['select_sensor'] = self.make_sensor_select_html(True, selected_sensor)
        return super(ExportData, self).html()

    def download_many(self, resp_object):
        '''
        Extracts the requested sensor data, averages it, and creates an Excel spreadsheet
        which is then written to the returned HttpResponse object 'resp_object'.
        '''

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
        binner = data_util.TsBin(float(self.get_params['averaging_time']))

        # open the database 
        db = bmsdata.BMSdata(global_vars.DATA_DB_FILENAME)

        # walk through sensors, setting column titles and building a Pandas DataFrame
        # that aligns the averaged timestamps of the different sensors.
        col = 1   # tracks spreadsheet column
        df = pd.DataFrame()
        for id in self.get_params.getlist('select_sensor'):
            sensor = models.Sensor.objects.get(sensor_id=id)

            # write column heading in spreadsheet
            ws.write(0, col, '%s, %s' % (sensor.title, sensor.unit.label), t1_style)
            ws.col(col).width = 3600

            # determine the start time for selecting records and make a DataFrame from
            # the records
            st_ts, end_ts = self.get_ts_range()
            db_recs = db.rowsForOneID(sensor.sensor_id, st_ts, end_ts)
            df_new = pd.DataFrame(db_recs).set_index('ts')
            df_new.columns = ['col%s' % col]
            df_new = df_new.groupby(binner.bin).mean()    # do requested averaging

            # join this with the existing DataFrame, taking the union of all timestamps
            df = df.join(df_new, how='outer')

            col += 1

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

class NormalizedByDDbyFt2(BldgChart):
    '''
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
    '''
    
    def data(self):
        '''
        Returns the data for a chart that normalizes a value by degree-days and floor area.
        Return value is a dictionary containing the dynamic data needed to draw the chart.
        '''

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
        for bldg_info in self.chart.chartbuildinginfo_set.all():

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

class NormalizedByFt2(BldgChart):
    
    '''
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
    '''
    
    def data(self):
        '''
        Returns the data for a chart that normalizes a value by floor area.
        Return value is a dictionary containing the dynamic data needed to draw the chart.
        '''

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
        for bldg_info in self.chart.chartbuildinginfo_set.all():

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
