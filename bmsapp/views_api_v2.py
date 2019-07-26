"""Version 2.x of the API.  Relies on views from API v1.
"""
import logging
from collections import Counter

import pytz
from django.http import JsonResponse
from dateutil.parser import parse

from bmsapp import models
from bmsapp.readingdb import bmsdata
from bmsapp.views_api_v1 import (
    fail_payload, 
    invalid_query_params, 
    sensor_info,
    check_sensor_reading_params
)

# Version number of this API
API_VERSION = 2.0

# Make a logger for this module
_logger = logging.getLogger('bms.' + __name__)

def api_version(request):
    """API method that returns the version number of the API
    """
    result = {
            'status': 'success',
            'data': {
                'version': API_VERSION,
            }
        }

    return JsonResponse(result)

def sensor_readings_multiple(request):
    """API Method.  Returns readings from multiple sensors, perhaps time-averaged
    and filtered by a date/time range.

    Parameters
    ----------
    request:    Django request object

    The 'request' object can have the following query parameters:
        sensor_id: The Sensor ID of a sensor to include.  This parameter can occur
            multiple times to request data from multiple sensors.
        start_ts: (optional) A date/time indicating the earliest reading to return.
            If not present, the earliest reading in the database is returned.
            Format is a string date/time, interpretable by dateutil.parser.parse.
        end_ts: (optional) A date/time indicating the latest reading to return.
            If not present records through the latest record in the database are returned.
            Format is a string date/time, interpretable by dateutil.parser.parse.
        timezone: (optional) A timezone name, present in the pytz.timezone database
            see https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
            e.g. "US/Alaska".  The timestamps for the sensor readings are returned
            consistent with this timezone.  Also, 'start_ts' and 'end_ts' are interpreted
            as being in this timezone.  If this parameter is not provided, the timezone of
            the first building associated with the requested sensor is used.  If no
            building is associated with the sensor, UTC is the assumed timezone.
        averaging: (optional) If provided, sensor readings are averaged into evenly spaced
            time intervals as indicated by this parameter.  The 'averaging' time interval
            must be provided as a string such as '4H' (4 hours), '2D' (2 days), or any interval
            describable by Pandas time offset notation:
            http://pandas.pydata.org/pandas-docs/stable/timeseries.html#offset-aliases
        label_offset: (optional) Only used if an 'averaging' parameter is provided.  This
            parameter controls what point in the time averaging interval is used to produce
            the timestamp for the returned reading.  'label_offset' uses the same format as
            'averaging', i.e. Pandas time offset notation, and the value is the time distance
            from the start of averaging interval to the location of the timestamp. For example,
            a value of '30min' means place the timestamp 30 minutes after the start of the
            interval.
            If no 'label_offset' is provided, the 'label_offset' is assumed to be 0, i.e.
            the starting edge of the averaging interval is marked by the timestamp.  Note
            that the convention in all of the BMON timeseries plots is to place the timestamp
            at the *center* of the averaging interval; that is *not* the default in this
            function because of the difficulty in automatically calculating the proper
            label_offset for the middle of the interval.

    Returns
    -------
    A JSON response containing an indicator of success or failure, the readings organized
    how they would be exported from a Pandas DataFrame using the "to_json(orient='split')"
    method, and the timezone of the timestamps returned.

    """
    try:

        db = bmsdata.BMSdata()  # reading database

        messages = {}   # used to store input validity messages.

        # get the list of requested sensors
        sensor_ids = request.GET.getlist('sensor_id')

        # must be at least one sensor.
        if len(sensor_ids) == 0:
            messages['sensor_id'] =  'There must be at least one requested sensor.' 

        # check to see if any are invalid
        sensors_not_valid = []
        for sensor_id in sensor_ids:
            if not db.sensor_id_exists(sensor_id):
                sensors_not_valid.append(sensor_id)
        if len(sensors_not_valid):
            messages['sensor_id'] = f"Sensors {', '.join(sensors_not_valid)} not present in the reading database."

        # Check the input parameters and get the values
        param_messages, start_ts, end_ts, timezone, averaging, label_offset = \
            check_sensor_reading_params(request)
        messages.update(param_messages)

        # check for extra, improper query parameters
        messages.update(invalid_query_params(request,
                                             ['sensor_id', 'timezone', 'start_ts', 'end_ts', 'averaging', 'label_offset']))

        if messages:
            # Input errors occurred
            return fail_payload(messages)

        # if there is no requested timezone (or an invalid one), use the
        # the most common timezone from the buildings associated with the list of sensors.
        if timezone is None:
            timezone = pytz.timezone('UTC')   # default timezone if no valid building tz present
            tzs = []
            for sensor in sensor_ids:
                for bldg in sensor_info(sensor)['buildings']:
                    tzs.append(bldg['timezone']) 
            most_common_tz = Counter(tzs).most_common(1)
            if most_common_tz:
                tz_name, tz_count = most_common_tz[0]
                try:
                    timezone = pytz.timezone(tz_name)
                except:
                    # stick with default
                    pass

        # record the name of the final timezone
        tz_name = str(timezone)

        # ---- Get the Sensor Readings
        # if start and end timestamps are present, convert to Unix Epoch values
        if start_ts:
            ts_aware = timezone.localize(start_ts)
            start_ts = ts_aware.timestamp()

        if end_ts:
            ts_aware = timezone.localize(end_ts)
            end_ts = ts_aware.timestamp()

        # get the sensor readings
        df = db.dataframeForMultipleIDs(sensor_ids, start_ts=start_ts, end_ts=end_ts, tz=timezone)

        # if averaging is requested, do it!
        if averaging and len(df) > 0:
            df = df.resample(rule = averaging, loffset = label_offset, label = 'left').mean().dropna()

        # make a dictionary that is formatted with orientation 'split', which is the most
        # compact form to send the DataFrame
        result = {
            'status': 'success',
            'data': {
                'readings': df.to_dict(orient='split'),
                'reading_timezone': tz_name,
            }
        }

        return JsonResponse(result)

    except Exception as e:
        # A processing error occurred.
        _logger.exception('Error retrieving sensor readings.')
        result = {
            'status': 'error',
            'message': str(e)
        }
        return JsonResponse(result, status=500)

def sensors(request):
    pass

def buildings(request):
    pass
