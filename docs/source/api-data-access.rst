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

GET /api/v1/readings/<sensor ID>/?<parameters>

where ``<sensor ID>`` is the BMON Sensor ID for the desired sensor.
``<parameters>`` are optional query parameters that can filter and transform
the returned readings; these described in the next section.

The BMON Sensor ID for a sensor can be obtained in at least two ways:

- If you use BMON to display a Current Values report that contains the sensor,
  you can hover your mouse over the Sensor Name to reveal pop-up sensor notes.
  At the bottom of the sensor notes the Sensor ID will be shown.
- The ``/api/v1/sensors/`` API call, described next, returns a list of all
  the sensors in the database.  For each sensor returned, the Sensor ID is
  shown.

Here is a sample method call for a BMON site located at
``https://bmon.analysisnorth.com``::

    https://bmon.analysisnorth.com/api/v1/readings/kake_temp/?averaging=1D

Request Parameters
~~~~~~~~~~~~~~~~~~

Response Fields
~~~~~~~~~~~~~~~

Don't forget Status code discussion

Errors
~~~~~~

Example Usage
~~~~~~~~~~~~~


