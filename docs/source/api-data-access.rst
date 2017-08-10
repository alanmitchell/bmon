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
- The ``/api/v1/sensors/`` API call, described next, returns a list of all
  the sensors in the database.  For each sensor returned, the Sensor ID is
  shown.

Here is a sample method call for a BMON site located at
``https://bmon.analysisnorth.com``::

    https://bmon.analysisnorth.com/api/v1/readings/kake_temp/?averaging=1D

Request Parameters
~~~~~~~~~~~~~~~~~~

Below are options request query parameters that can be used to filter or
transform the returned sensor readings.

``timezone``, optional, string, a timezone name
    If specified, the timestamps of the sensor readings returned are
    expressed in this timezone.  Also, time filter query parameters,
    discussed below, are interpreted to be in this timezone.  The timezone
    name must be one of the ones found in `this timezone database
    list <https://en.wikipedia.org/wiki/List_of_tz_database_time_zones>`_.
    If this parameter is not provided, the timezone of the first building
    associated with this sensor is used; if that timezone is not available
    or invalid, the UTC timezone is used in the response.

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

``end_ts``, optional, a Date/Time string, such as ``2017-03-01 18:45``
    Sensor readings on or before this date/time will be returned.  If no
    time component is given, the start of the day, 00:00:00, is used.
    If ``end_ts`` is not provided, all readings on or after
    ``start_ts`` will be returned. ``end_ts`` is interpreted to be in
    the response timezone, as discussed in the ``timezone`` parameter above.
    The format of the date/time string can be any format that is
    interpretable by the ``parse`` method of the Python package
    ``dateutil.parser``.

``averaging``, optional, a Python Pandas Offset Alias string
    If this parameter is given, time averaging is applied to the sensor
    readings before being returned.
    The `Pandas Offset Alias <https://pandas.pydata.org/pandas-docs/stable/timeseries.html#offset-aliases>`_
    is a string such as ``2D`` (two days) or ``1H30min`` (one hour and 30 minutes)
    that determines the size of the averaging interval used.

``label_offset``, optional, a Python Pandas Offset Alias string
    If time averaging is being requested through use of the ``averaging``
    parameter, a ``label_offset`` can also be specified, and this
    parameter affects where the timestamp for the averaged reading is placed
    within the averaging interval.  The default, if no ``label_offset`` is
    provided is to use the start of the averaging interval as the location
    of the returned timestamp.  If a ``label_offset`` is provided, it
    specifies the time distance from the start of the averaging interval to
    the location of the timestamp.  For example, a value of ``30min`` would
    place the timestamp 30 minutes past the start of the interval.


Response Fields
~~~~~~~~~~~~~~~

Don't forget Status code discussion

Errors
~~~~~~

Example Usage
~~~~~~~~~~~~~


