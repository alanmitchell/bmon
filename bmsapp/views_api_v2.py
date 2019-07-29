"""Version 2.x of the API.  Relies on functions in API v1.
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

def sensor_readings(request):
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
    """Returns information about one or more sensors.

    Parameters
    ----------
    request:    Django request object

    The 'request' object can have the following query parameters:
        sensor_id: The Sensor ID of a sensor to include.  This parameter can occur
            multiple times to request data from multiple sensors.  If the sensor_id
            parameter is not present, information for **all** sensors is returned.

    Returns
    -------
    A JSON response containing an indicator of success or failure, a list of
    sensors including sensor properties and building association information
    if available.
    """

    try:
        #------ Check the query parameters
        messages = invalid_query_params(request, ['sensor_id'])
        # get a list of all the Sensor IDs in the reading database
        db = bmsdata.BMSdata()  # reading database
        all_sensor_ids = db.sensor_id_list()

        # determine the list of Sensor IDs requested by this call
        sensor_ids = request.GET.getlist('sensor_id')

        if len(sensor_ids) == 0:
            # no sensors were in the request, which means this should
            # return all sensors.
            sensor_ids = all_sensor_ids
        else:
            # check to make sure all the Sensor IDs are valid.
            invalid_ids = set(sensor_ids) - set(all_sensor_ids)
            if len(invalid_ids):
                messages['sensor_id'] = f"Invalid Sensor IDs: {', '.join(list(invalid_ids))}"
        
        if messages:
            return fail_payload(messages)

        fields_to_exclude = ['_state']
        def clean_sensor(s):
            """Function to clean up Sensor object property dictionary and
            add some additional info.
            Parameter 's' is the dictionary of the Django Sensor object, gotten
            from sensor.__dict__
            """
            # remove fields to exclude
            for fld in fields_to_exclude:
                s.pop(fld, None)

            # look up the sensor units if present
            unit_id = s.pop('unit_id')
            if unit_id:
                unit = models.Unit.objects.get(pk=unit_id)
                s['unit'] = unit.label
            else:
                s['unit'] = ''

            # Add a list of buildings that this sensor is associated with.
            if s['id'] is not None:
                bldgs = []
                for link in models.BldgToSensor.objects.filter(sensor=s['id']):
                    bldgs.append( 
                        {'bldg_id': link.building.pk, 
                        'sensor_group': link.sensor_group.title,
                        'sort_order': link.sort_order} 
                    )
                s['buildings'] = bldgs
            else:
                # no buildings 
                s['buildings'] = []
            
            return s

        sensors = []    # list holding sensor information to return

        # get a default dictionary to use if the Sensor ID is not in the Django model
        # object list.
        default_props = models.Sensor().__dict__
        for sensor_id in sensor_ids:

            try:
                sensor = models.Sensor.objects.get(sensor_id=sensor_id)
                sensor_props = sensor.__dict__
            except:
                # No Django sensor object yet (this is an unassigned sensor).
                # Use default values
                sensor_props = default_props.copy()
                sensor_props['sensor_id'] = sensor_id
            sensors.append(clean_sensor(sensor_props))

        result = {
            'status': 'success',
            'data': {
                'sensors': sensors,
            }
        }
        return JsonResponse(result)

    except Exception as e:
        # A processing error occurred.
        _logger.exception('Error retrieving sensor information')
        result = {
            'status': 'error',
            'message': str(e)
        }
        return JsonResponse(result, status=500)


def buildings(request):
    """Returns information about one or more buildings.

    Parameters
    ----------
    request:    Django request object

    The 'request' object can have the following query parameters:
        building_id: The Building ID (Django model primary key) of a building to include.
            This parameter can occur multiple times to request data from multiple buildings.
            If the building_id parameter is not present, information for **all** 
            buildings is returned.

    Returns
    -------
    A JSON response containing an indicator of success or failure, a list of
    buildings including building properties and sensor association information
    if available.
    """

    try:
        #------ Check the query parameters
        messages = invalid_query_params(request, ['building_id'])

        # Make a list of all building IDs.
        all_bldg_ids =  [b.pk for b in models.Building.objects.all()]
        print(all_bldg_ids)

        # determine the list of Building IDs requested by this call
        bldg_ids = request.GET.getlist('building_id')
        bldg_ids = [int(i) for i in bldg_ids]

        if len(bldg_ids) == 0:
            # no builidings were in the request, which means this should
            # return all buildings.
            bldg_ids = all_bldg_ids
        else:
            # check to make sure all the Building IDs are valid.
            invalid_ids = set(bldg_ids) - set(all_bldg_ids)
            if len(invalid_ids):
                invalid_ids = [str(i) for i in invalid_ids]
                messages['building_id'] = f"Invalid Building IDs: {', '.join(list(invalid_ids))}"
        
        if messages:
            return fail_payload(messages)

        fields_to_exclude = ['_state']
        def clean_bldg(b):
            """Function to clean up Building object property dictionary and
            add some additional info.
            Parameter 'b' is the dictionary of the Django Building object, gotten
            from building.__dict__
            """
            # remove fields to exclude
            for fld in fields_to_exclude:
                b.pop(fld, None)

            # look up the current Building mode if present
            current_mode_id = b.pop('current_mode_id')
            if current_mode_id:
                current_mode = models.BuildingMode.objects.get(pk=current_mode_id)
                b['current_mode'] = current_mode.name
            else:
                b['current_mode'] = ''

            # Add a list of sensors that this sensor is associated with.
            # Note that the Sensor ID here is not the Django model primay key; it
            # is the sensor_id field of the Sensor object, to be consistent with the
            # sensors() endpoint of this API.
            sensors = []
            for link in models.BldgToSensor.objects.filter(building=b['id']):
                sensors.append( 
                    {'sensor_id': link.sensor.sensor_id, 
                    'sensor_group': link.sensor_group.title,
                    'sort_order': link.sort_order} 
                )
            b['sensors'] = sensors
            
            return b

        bldgs = []    # list holding building information to return
        for bldg_id in bldg_ids:
            bldg = models.Building.objects.get(pk=bldg_id)
            bldg_props = bldg.__dict__
            bldgs.append(clean_bldg(bldg_props))

        result = {
            'status': 'success',
            'data': {
                'buildings': bldgs,
            }
        }
        return JsonResponse(result)

    except Exception as e:
        # A processing error occurred.
        _logger.exception('Error retrieving building information')
        result = {
            'status': 'error',
            'message': str(e)
        }
        return JsonResponse(result, status=500)
