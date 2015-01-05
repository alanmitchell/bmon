"""
This module holds classes that create the HTML and supply the data for Charts and
Reports.
"""
import time, logging, copy
from django.template import Context, loader
from django.http import HttpResponse
import pandas as pd, numpy as np, xlwt
import models, global_vars, data_util, view_util, chart_config
from readingdb import bmsdata
from ..calcs import transforms

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
    BldgChartType(0, 'Dashboard', 'Dashboard'),
    BldgChartType(1, 'Current Sensor Values', 'CurrentValues'),
    BldgChartType(2, 'Plot Sensor Values over Time', 'TimeSeries'),
    BldgChartType(3, 'Hourly Profile of a Sensor', 'HourlyProfile'),
    BldgChartType(4, 'Histogram of a Sensor', 'Histogram'),
    BldgChartType(5, 'Sensor X vs Y Scatter Plot', 'XYplot'),
    BldgChartType(6, 'Download Sensor Data to Excel', 'ExportData')
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
    bldg_id = view_util.to_int(request_params['select_bldg'])
    chart_id = view_util.to_int(request_params['select_chart'])

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

def formatCurVal(val):
    """
    Helper function for formatting current values to 3 significant digits, but 
    avoiding the use of scientific notation for display.  Also, integers are
    shown at full precision.
    """
    if val == int(val):
        return '{:,}'.format(int(val))
    elif val >= 1000.0:
        return '{:,}'.format( int(float('%.3g' % val)))
    else:
        return '%.3g' % val


class BaseChart(object):
    """Base class for all of the chart classes.
    """

    def __init__(self, chart_info, bldg_id, request_params):
        """
        'chart_info' is the models.BuildingChart object for the chart.  'bldg_id'
        is the id of the building being charted. 'request_params' are the parameters
        passed in by the user through the Get http request.
        """
        self.chart_info = chart_info
        self.bldg_id = bldg_id

        # if this is a chart for a single building, get the associated building model object
        if bldg_id != 'multi':
            self.building = models.Building.objects.get(id=bldg_id)

        self.request_params = request_params

        # for the multi-building chart object, take the keyword parameter string 
        # and convert it to a dictionary.
        if bldg_id == 'multi':
            self.chart_params = transforms.makeKeywordArgs(chart_info.parameters)

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

    def result(self):
        '''
        This method should be overridden to return a dictionary with an 
        'html' key holding the HTML of the results and an 'objects' key
        holding a list of JavaScript objects to create.  Each object is a
        two-tuple with the first element being the string identifying the
        object type and the second element being a configuration dictionary
        for that object type.
        '''
        return {'html': self.__class__.__name__, 'objects': []}

