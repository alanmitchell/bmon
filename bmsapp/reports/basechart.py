"""
This module holds classes that create the HTML and supply the data for Charts and
Reports.
"""
import time, logging, copy, importlib
from django.conf import settings
import yaml
import bmsapp.models, bmsapp.readingdb.bmsdata
import bmsapp.schedule
import bmsapp.view_util, bmsapp.data_util
import chart_config

# Make a logger for this module
_logger = logging.getLogger('bms.' + __name__)


class BldgChartType:
    """Class to provide descriptive information about a particular type of chart related
    to one building.
    """

    def __init__(self, id, title, class_name):
        """Initializes the chart type.

            Args:
                id (int): ID number uniquely identifying this chart type.
                title (string): Text that will be displayed in select controls and chart titles.
                class_name (string): The name of the Python class in this charts.py used to create the chart.
        """
        self.id = id        
        self.title = title  
        self.class_name = class_name   

# These are the possible chart types currently implemented, in the order they will be 
# presented to the User.
BLDG_CHART_TYPES = [
    BldgChartType(0, 'Dashboard', 'dashboard.Dashboard'),
    BldgChartType(1, 'Current Sensor Values', 'currentvalues.CurrentValues'),
    BldgChartType(2, 'Plot Sensor Values over Time', 'timeseries.TimeSeries'),
    BldgChartType(3, 'Hourly Profile of a Sensor', 'hourlyprofile.HourlyProfile'),
    BldgChartType(4, 'Histogram of a Sensor', 'histogram.Histogram'),
    BldgChartType(5, 'Sensor X vs Y Scatter Plot', 'xyplot.XYplot'),
    BldgChartType(6, 'Download Sensor Data to Excel', 'exportdata.ExportData')
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

def get_chart_object(request_params):
    """Returns the appropriate chart object identified by the arguments.

        Args:
            request_params: The parameters (request.GET) passed in by the user further qualifying the chart.

        Returns:
            A chart object descending from BaseChart.
    """

    # Get building ID and chart ID from the request parameters
    bldg_id = bmsapp.view_util.to_int(request_params['select_bldg'])
    chart_id = bmsapp.view_util.to_int(request_params['select_chart'])

    if bldg_id=='multi':
        chart_info = bmsapp.models.MultiBuildingChart.objects.get(id=chart_id)
        class_name = chart_info.chart_class
    else:
        chart_info = find_chart_type(chart_id)
        class_name = chart_info.class_name

    # need to dynamically get a class object based on the class_name.
    # class_name is in the format <module name>.<class name>; break it apart.
    mod_name, bare_class_name = class_name.split('.')
    mod = importlib.import_module('bmsapp.reports.%s' % mod_name.strip())
    
    # get a reference to the class referred to by class_name
    chart_class = getattr(mod, bare_class_name.strip())

    # instantiate and return the chart from this class
    return chart_class(chart_info, bldg_id, request_params)


class BaseChart(object):
    """Base class for all of the chart classes.
    """

    def __init__(self, chart_info, bldg_id, request_params):
        """
        'chart_info' is the models.MultiBuildingChart object for the chart if it
        is a multi-building chart; for single-building charts, it is the BldgChartType
        object (the BldgChartType class is in this module).  'bldg_id'
        is the id of the building being charted, or 'multi' for multi-building
        charts. 'request_params' are the parameters
        passed in by the user through the Get http request.
        """
        self.chart_info = chart_info
        self.bldg_id = bldg_id

        # if this is a chart for a single building, get the associated building model object,
        # and the occupied schedule for the building if it is present.  Also, determine a 
        # timezone appropriate for this chart.
        self.schedule = None
        self.timezone = getattr(settings, 'TIME_ZONE', 'US/Alaska').strip()
        if bldg_id != 'multi':
            self.building = bmsapp.models.Building.objects.get(id=bldg_id)
            # override  the timezone if the building has one explicitly set
            if len(self.building.timezone.strip()):
                self.timezone = self.building.timezone.strip()
            if len(self.building.schedule.strip()):
                self.schedule = bmsapp.schedule.Schedule(self.building.schedule, self.timezone)

        self.request_params = request_params

        # for the multi-building chart object, take the keyword parameter string 
        # and convert it to a Python dictionary or list.
        if bldg_id == 'multi':
            self.chart_params = yaml.load(chart_info.parameters)

        # open the reading database and save it for use by the methods of this object.
        # It is closed automatically in the destructor of the BMSdata class.
        self.reading_db = bmsapp.readingdb.bmsdata.BMSdata()

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
            st_ts = bmsapp.data_util.datestr_to_ts(st_date) if len(st_date) else 0
            end_date = self.request_params['end_date']
            end_ts = bmsapp.data_util.datestr_to_ts(end_date + " 23:59:59") if len(end_date) else time.time() + 3600.0

        return st_ts, end_ts

    def get_chart_options(self, chart_type='highcharts'):
        """
        Returns a configuration object for a Highcharts or Highstock chart.  Must make a
        copy of the original so that it is not modified.
        """
        opt = chart_config.highcharts_opt if chart_type=='highcharts' else chart_config.highstock_opt
        opt = copy.deepcopy(opt)
        if hasattr(self, 'building'):
            opt['title']['text'] = '%s: %s' % (self.chart_info.title, self.building.title)
        else:
            opt['title']['text'] = self.chart_info.title
        return opt

    def occupied_resolution(self):
        """Returns a string indicating the resolution to use when determining
        whether a timestamp is in the Occupied or Unoccupied period.  The return
        value depends on how many hours the data is averaged over; this is 
        indicated by the 'averaging_time' GET parameter.
        The possible return values are 
            'exact': classify the timestamp based on the exact schedule times.
            'day': classify the timestamp according to whether it falls in a day
                that is predominantly occupied.
            None: Data averaging is across long intervals that make occupied / 
                unoccupied classification not meaningful.
        """
        # get info about the requested chart
        cht_info = find_chart_type(int(self.request_params['select_chart']))

        # get the requested averaging interval in hours.  The relevant 
        # averaging input control depends on the chart type.
        if 'XY' in cht_info.class_name:
            averaging_hours = float(self.request_params['averaging_time_xy'])    
        elif 'Export' in cht_info.class_name:
            averaging_hours = float(self.request_params['averaging_time_export'])
        else:
            averaging_hours = float(self.request_params['averaging_time'])

        if averaging_hours < 24.0:
            return 'exact'
        elif averaging_hours==24.0:
            return 'day'
        else:
            return None

    def result(self):
        '''
        This method should be overridden to return a dictionary with an 
        'html' key holding the HTML of the results and an 'objects' key
        holding a list of JavaScript objects to create.  Each object is a
        two-tuple with the first element being the string identifying the
        object type and the second element being a configuration dictionary
        for that object type.  'bmsappX-Y.Z.js' must understand the string
        describing the JavaScript object.
        Alternatively, this method can return a django.http.HttpResponse
        object, which will be returned directly to the client application;
        this approach is used the exportdata.ExportData class to return an
        Excel spreadsheet.
        '''
        return {'html': self.__class__.__name__, 'objects': []}

