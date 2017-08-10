.. _api-data-access:

API Data Access
===============

A basic Application Programming Interface is available to read data from
the BMON application.  Currently, there are two available API methods, one
for extracting sensor readings from BMON and a second for obtaining the full
list of sensors that are available in the database.  All of these methods
return their results in JSON format, conforming to the
`JSend Specification <https://labs.omniti.com/labs/jsend>`_
The two methods are documented below, including example usage.

API Method to Obtain Sensor Readings
------------------------------------

This method allows you to obtain readings from one sensor in the BMON database.
You can limit the time range of readings returned and you can also have BMON
first perform time-averaging of the readings (e.g. daily
average readings).

Request URL
~~~~~~~~~~~

::

    GET /api/v1/readings/<sensor ID>/?<parameters>

where ``<sensor ID>`` is the BMON Sensor ID for the desired sensor.
``<parameters>`` are optional query parameters that can cause filtering
and transformation of the returned readings; these are described in the
next section.

The BMON Sensor ID for a sensor can be obtained in at least two ways:

- If you use BMON to display a Current Values report that contains the sensor,
  you can hover your mouse over the Sensor Name to reveal pop-up sensor notes.
  At the bottom of the sensor notes, the Sensor ID will be shown.
- The ``/api/v1/sensors/`` API method, described next, returns a list of all
  the sensors in the database.  For each sensor returned, the Sensor ID is
  shown.

Here is a sample method call requesting sensor readings from a sensor with an
ID of ``kake_temp`` from a BMON site accessed at
``https://bmon.analysisnorth.com``::

    https://bmon.analysisnorth.com/api/v1/readings/kake_temp/?averaging=1D

Request Parameters
~~~~~~~~~~~~~~~~~~

Below are optional request query parameters that can be used to filter or
transform the returned sensor readings.

``timezone``, optional, a timezone name string
    If specified, the timestamps of the sensor readings returned are
    expressed in this timezone.  Also, time filter query parameters,
    discussed below, are interpreted to be in this timezone.  The timezone
    name must be one of the ones found in `this timezone database
    list <https://en.wikipedia.org/wiki/List_of_tz_database_time_zones>`_.
    If this parameter is not provided, the timezone of the first building
    associated with this sensor is used in the method response; if that
    timezone is not available or invalid, the UTC timezone is used in
    the response.

``start_ts``, optional, a Date/Time string, such as ``2017-02-14 13:44``
    Sensor readings on or after this date/time will be returned.  If no
    time component is given, the start of the day, 00:00:00, is used.
    If ``start_ts`` is not provided, readings will be returned
    starting with the earliest reading
    in the database.  ``start_ts`` is interpreted to be in the response
    timezone, as discussed in the ``timezone`` parameter above.
    The format of the date/time string can be any format that is
    interpretable by the ``parse`` method of the Python package
    ``dateutil.parser``.

``end_ts``, optional, a Date/Time string, such as ``2017-03-01 18:45:59``
    Sensor readings on or before this date/time will be returned.  If no
    time component is given, the start of the day, 00:00:00, is used.
    If ``end_ts`` is not provided, all readings on or after
    ``start_ts`` will be returned. ``end_ts`` is interpreted to be in
    the response timezone, as discussed in the ``timezone`` parameter above.
    The format of the date/time string can be any format that is
    interpretable by the ``parse`` method of the Python package
    ``dateutil.parser``.

``averaging``, optional, a Python Pandas Offset Alias string
    If this parameter is given, sensor readings are averaged into evenly
    spaced time intervals.
    The `Pandas Offset Alias <https://pandas.pydata.org/pandas-docs/stable/timeseries.html#offset-aliases>`_
    is a string such as ``2D`` (two days) or ``1H30min`` (one hour and 30 minutes)
    that determines the size of the averaging interval used.

``label_offset``, optional, a Python Pandas Offset Alias string
    If time averaging is being requested through use of the ``averaging``
    parameter, a ``label_offset`` can also be specified, and this
    parameter affects where the timestamp for the averaged reading is placed
    within the averaging interval.  The default if no ``label_offset`` is
    provided is to use the start of the averaging interval as the location
    of the returned timestamp (some.  If a ``label_offset`` is provided, it
    specifies the time distance from the start of the averaging interval to
    the location of the timestamp.  For example, a value of ``30min`` would
    place the timestamp 30 minutes past the start of the interval.


Response Fields
~~~~~~~~~~~~~~~

A successful request results in a returned response Status Code of 200, and
a JSON response with the following JSON key/value fields.

``status``, a string
    For a successful request, this field will have the value ``success``.

``data``, a collection of JSON key/value fields
    For a successful request, the collection of ``data`` fields are described
    in the next section.

``data`` Fields for a Successful Request
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``reading_timezone``, string
    This gives the name of the timezone that the readings are expressed in.
    It was determined by the procedure outlined in the ``timezone`` request
    parameter documentation.

``readings``, array of 2-element arrays
    This is an array of 2-element arrays; each 2-element array is one sensor
    reading.  The first element of that array is a timestamp in the format
    of ``YYYY-MM-DD HH:MM:SS``.  The second element of the array is a floating
    point sensor value.  See the example method response below.

``sensor_info``, a collection of JSON key/value fields
    This collection gives information about the requested sensor, including
    buildings that the sensor is associated with.  See the details in the
    next section.

``sensor_info`` Fields
++++++++++++++++++++++

If a sensor is shown in the BMON interface, then BMON has additional information
about the sensor, such as its name and the engineering units associated with
the sensor values.  Most of these values are returned in the fields below.

There are also sensors that may be present in the sensor
reading database but not shown in the BMON interface.  For those sensors, most of
the information below is not available and ``null`` JSON values are returned.

Note that some of these fields are related to internal BMON programming and may
require examination of BMON source code for full understanding.  Those fields
are marked '(advanced)' in the list below.

``sensor_id``, string
    This plays back the Sensor ID that was in the original request.

``name``, string
    The name of the sensor as displayed in the BMON interface.

``units``, string
    The engineering units associated with the sensor values, e.g. "deg F".

``notes``, string
    Additional notes about the sensor.

``other_props``, string
    These are miscellaneous properties that the BMON System Administrator
    has assigned to the sensor.  The properties are in YAML format.

``formatting_func``, string, (advanced)
    The name of a BMON formatting function that is applied to the sensor
    value before displaying in the BMON interface.

``calculated``, boolean, i.e. ``true`` or ``false``, (advanced)
    Indicates whether this sensor is a sensor that is calculated from other
    sensor values or acquired from the Internet.

``calc_order``, number, (advanced)
    If this is a 'calculated' sensor, this ``calc_order`` number determines
    when this particular sensor is calculated relative to all the other
    calculated sensors.

``tran_calc_func``, string, (advanced)
    The name of a BMON calculated field function or a transformation function
    that is applied to the sensor value before storing in the reading
    database.

``buildings``, array of building descriptions
    These are the buildings that the sensor is assigned to.  Most sensors are
    only assigned to one building, but weather site sensors may be associated
    with multiple builidngs.  Each building in this array is a collection of
    key/value properties, including: ``bldg_id`` - the unique ID number for
    the building; ``name`` - the building name; ``timezone`` - the
    timezone name where the building is located; ``latitude`` and ``longitude``
    coordinates of the building; and the ``sensor_group`` that this sensor
    falls into for this building.


Example Usage
~~~~~~~~~~~~~

Here is a sample successful request that asks for monthly average sensors values
for the ``kake_temp`` sensor, but only including sensor readings
from May 1, 2017 (start of day) onward::

    https://bmon.analysisnorth.com/api/v1/readings/kake_temp/?start_ts=5/1/2017&averaging=MS

Here is the JSON response:

.. code-block:: json

    {
        "status": "success",
        "data": {
            "reading_timezone": "US/Alaska",
            "readings": [
                [
                    "2017-05-01 00:00:00",
                    47.842
                ],
                [
                    "2017-06-01 00:00:00",
                    51.402
                ],
                [
                    "2017-07-01 00:00:00",
                    55.961
                ],
                [
                    "2017-08-01 00:00:00",
                    58.963
                ]
            ],
            "sensor_info": {
                "sensor_id": "kake_temp",
                "name": "Kake Temp",
                "units": "deg F",
                "notes": "No sensor notes available.",
                "other_props": "",
                "formatting_func": "",
                "calculated": true,
                "calc_order": 0,
                "tran_calc_func": "getInternetTemp",
                "buildings": [
                    {
                        "bldg_id": 2,
                        "name": " Kake Senior Center",
                        "timezone": "US/Alaska",
                        "latitude": 56.97,
                        "longitude": -133.94
                        "sensor_group": "Weather",
                    }
                ]
            }
        }
    }

Errors
~~~~~~

