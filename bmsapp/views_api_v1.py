"""Module that implements version 1 of an API to access
the data held in BMON.
Response are in JSON and implement the JSend specification;
see:  https://labs.omniti.com/labs/jsend .
"""

import logging
from datetime import datetime
import calendar
import pytz
from django.http import JsonResponse
from dateutil.parser import parse
import pandas as pd

import models
import readingdb.bmsdata

# Make a logger for this module
_logger = logging.getLogger('bms.' + __name__)

def fail_payload(messages):
    """Helper routine. Returns a JSON response with success = fail
    indicating improper input data.

    Parameters
    ----------
    messages: a dictionary of messages describing the bad input data

    Returns
    -------
    A Django response object appropriate for a JSON payload.
    """
    result = {'status': 'fail'}
    if messages:
        result['data'] = messages
    else:
        result['data'] = None

    return JsonResponse(result)


def sensor_readings(request, sensor_id):
    """API method. Returns a list of sensor readings for one sensor.  Time limits and
    time averaging can be requested for the returned readings.

    Parameters
    ----------
    request:    Django request object
    sensor_id:  The "sensor_id" of the sensor that readings are being requested for

    The 'request' object can have the following query parameters:
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
    A JSON response containing an indicator of success or failure, and a list of
    sensor readings (date, reading)
    """

    db = readingdb.bmsdata.BMSdata()  # reading database

    #------ Check all the input parameters

    messages = {}   # used to store input validity messages.

    # Is the sensor_id in the database?
    if not db.sensor_id_exists(sensor_id):
        messages['sensor_id'] = "Sensor '%s' is not present in the reading database." % sensor_id

    # Valid 'start_ts' ?
    start_ts = request.GET.get('start_ts', None)
    if start_ts:
        try:
            start_ts = parse(start_ts)
        except:
            messages['start_ts'] = "'%s' is not a valid date/time" % start_ts

    # Valid 'end_ts' ?
    end_ts = request.GET.get('end_ts', None)
    if end_ts:
        try:
            end_ts = parse(end_ts)
        except:
            messages['end_ts'] = "'%s' is not a valid date/time" % end_ts

    # Valid timezone?
    timezone = request.GET.get('timezone', None)
    if timezone:
        try:
            timezone = pytz.timezone(timezone)
        except:
            messages['timezone'] = "'%s' is not a valid timezone name." % timezone

    # Test averaging and label_offset strings for validity
    st = datetime(2017, 1, 1)  # datetime used for testing only
    averaging = request.GET.get('averaging', None)
    if averaging:
        try:
            pd.date_range(st, periods=1, freq=averaging)
        except:
            messages['averaging'] = "'%s' is an invalid time averaging string." % averaging

    label_offset = request.GET.get('label_offset', None)
    if label_offset:
        try:
            pd.date_range(st, periods=1, freq=label_offset)
        except:
            messages['label_offset'] = "'%s' is an invalid time label_offset string." % label_offset

    if messages:
        # Input errors occurred
        return fail_payload(messages)

    # If the timezone was not passed determine it from the building associated with the sensor.
    if not timezone:
        qs = models.Sensor.objects.filter(sensor_id=sensor_id)
        if len(qs)==0:
            # Sensor does not have a sensor object. UTC is default timezone
            timezone = pytz.timezone('UTC')
        else:
            sensor = qs[0]   # get the actual Sensor object
            # see if this sensor has links to a building
            links = models.BldgToSensor.objects.filter(sensor=sensor)
            if len(links)==0:
                # no links, so default to UTC
                timezone = pytz.timezone('UTC')
            else:
                # Use the building timezone, if it is valid
                tz_name = links[0].building.timezone
                try:
                    timezone = pytz.timezone(tz_name)
                except:
                    # invalid building timezone so use UTC
                    timezone = pytz.timezone('UTC')

    # if start and end timestamps are present, convert to Unix Epoch values
    if start_ts:
        ts_aware = timezone.localize(start_ts)
        start_ts = calendar.timegm(ts_aware.utctimetuple())

    if end_ts:
        ts_aware = timezone.localize(end_ts)
        end_ts = calendar.timegm(ts_aware.utctimetuple())

    # get the sensor readings
    df = db.dataframeForOneID(sensor_id, start_ts=start_ts, end_ts=end_ts, tz=timezone)

    # if averaging is requested, do it!
    if averaging:
        df = df.resample(rule = averaging, loffset = label_offset, label = 'left').mean().dropna()

    readings = zip(df.index.values, df.val.values)
    readings_str = [(str(ts), '%.4g' % val) for ts, val in readings]

    result = {'status': 'success', 'data': {'readings': readings_str}}

    return JsonResponse(result)
