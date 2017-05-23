.. _calculated-fields:

Calculated Fields
=================

Calculated Fields are used for two purposes:

*  to calculate new sensor readings from other readings that are in the
   sensor database.
*  to add sensor readings gathered from the Internet. The current
   implementation allows for acquisition of temperature and wind speed
   data from Internet weather services.

A Calculated Field uses the same editing form in BMON as a standard
Sensor does. So, to add a Calculated Field, you follow the normal
procedure for adding a Sensor, as described in :ref:`adding-buildings-and-sensors`. 
The important configuration differences
relative to a standard sensor are:

*  For a Calculated Field, you need to create your own Sensor ID for the
   calculated field. The Sensor ID must be unique across the entire BMON
   set of Sensors. The Sensor ID needs to be 30 characters or less,
   using numbers and letters but no spaces.
*  In the Sensor editing form, you need to make sure that the
   ``Calculated Field`` box is checked.

The BMON system processes Calculated Fields every one-half hour. If the
calculated fields involve sensors that report more frequently than every
half hour, multiple calculated sensor readings will be generated at each
half-hour processing interval to match up with the frequency of the
source sensors.

We will start by explaining the second use of Calculated Fields, i.e.
gathering data from Internet Weather Services.

Acquiring Weather Data from the Internet
----------------------------------------

BMON can currently access outdoor dry-bulb temperature, wind speed, and
relative humidity data from the National Weather Service and dry-bulb
temperature and wind speed from the Weather Underground service. Here is
an example of the needed configuration for the National Weather Service:

.. image:: /_static/calc_ex1.png

In the first box, a Sensor ID has been created, in this example:
``elmendorf_temp``. ``Title`` and ``Unit`` entries are filled out as
they are for standard sensors. The ``Calculated Field`` box must be
checked. For gathering outdoor dry-bulb temperature, the
``Transform or Calculated Field Function Name`` must contain the value
``getInternetTemp`` (correct capitalization is critical and must be as
shown). Finally, the ``Function Parameters in YAML form`` box must have
an entry of ``stnCode:`` plus a 4 character `National Weather Service
station code <http://www.weather.gov/>`_, in this example (there must be
a space after the colon):

::

    stnCode: PAED

The only changes necessary to acquire a wind speed value in miles per
hour is to enter ``getInternetWindSpeed`` into the
``Transform or Calculated Field Function Name`` box, change the ``Unit``
to ``velocity: mph``, and enter an appropriate Sensor ID and Title.
Acquiring relative humidity data in % RH requires entering
``getInternetRH`` into
the\ ``Transform or Calculated Field Function Name`` box, and making
appropriate unit and title changes elsewhere.

--------------

The Weather Underground service has a broader variety of weather
stations, including personal weather stations. To gather temperature or
wind data from this service, you must first acquire a `Weather
Underground API Key <http://www.wunderground.com/weather/api/>`_ and enter
that key into the :ref:`BMON Settings File <how-to-install-BMON-on-a-web-server>` 
as the ``BMSAPP_WU_API_KEY`` setting (restarting the Django web
application after changing a setting is necessary).

Here is an example configuration for acquiring temperature data from the
service:

.. image:: /_static/calc_ex2.png

The key differences from the National Weather Service configuration are:

*  ``getWUtemperature`` must be entered into the
   ``Transform or Calculated Field Function Name`` box. If you are
   acquiring wind speed data, then the correct entry is
   ``getWUwindSpeed``. Capitalization must be as shown.
*  The ``Function Parameters`` box must contain a ``stn`` entry for the
   main weather station you want data from and an optional ``stn2`` code
   for a weather station to use as a backup in case the primary station
   is not available. An example entry is:

::

        stn: pws:KAKANCHO124
        stn2: pws:MD0691

For information on how to form station codes, see the `Weather Underground API
documentation <http://www.wunderground.com/weather/api/d/docs?d=data/index>`_
for the ``query`` parameter. In this example, two personal weather
stations are being used with station IDs of ``KAKANCH0124`` and
``MD0691``.

Acquiring Building Energy Usage Information from ARIS
-----------------------------------------------------

BMON can import building energy usage information from AHFC's Alaska
Retrofit Information System (ARIS). Configuring a sensor for the
imported data is very similar to the process for acquiring weather data
from the internet described above.

Using the administration interface, create a new Sensor ID. ``Title``
and ``Unit`` entries are filled out as they are for standard sensors.
The ``Calculated Field`` box must be checked. The
``Transform or Calculated Field Function Name`` must contain the value
``getUsageFromARIS`` (correct capitalization is critical and must be as
shown). Finally, the ``Function Parameters in YAML form`` box must have
an entry of ``building_id:`` (there must be a space after the colon)
with a valid building id number from the ARIS database, and an entry of
``energy_type_id:`` with a valid energy type value as described below.

Required Function Parameters in YAML form:

::

    building_id: 1
    energy_type_id: 1

Additional Optional Function Parameters in YAML form:

::

    energy_parameter: 'EnergyQuantity'
    energy_multiplier: 1
    expected_period_months: 1

**``building_id`` Parameter**

The easiest way to find a building_id value is to look on the
'Commercial REAL Form' in the ARIS user interface. When you select a
building the building_id should show up in the upper left corner of the
form.

**``energy_type_id`` Parameter**

Possible values for the energy_type_id parameter: 

* 1 Electric 
* 2 Natural Gas 
* 3 Propane
* 6 Coal 
* 7 Demand - Electric 
* 8 Demand - Nat Gas 
* 10 Steam District Ht 
* 11 Hot Wtr District Ht
* 12 Spruce Wood 
* 13 Birch Wood  
* 14 #1 Fuel Oil 
* 15 #2 Fuel Oil

**``energy_parameter`` Optional Parameter**

The energy_parameter specifies which value will be read from the ARIS
database: 

* EnergyQuantity: The amount of energy used 
* DollarCost: The cost of energy for the given month  
* DemandUse: The amount of energy demand 
* DemandCost: The cost of energy demand for the given month, in dollars

A value of 'EnergyQuantity' will be used by default if you don't include
this parameter.

**``energy_multiplier`` Optional Parameter**

The energy_multiplier is a multiplier that is used to scale the value
that is read from the ARIS database. If you don't include the parameter,
a value of 1.0 will be used by default. The value that is stored is
calculated as:

*  For EnergyQuantity:
   ``[stored value] = [value from ARIS] * energy_multiplier / [total hours in the read period]``
*  For Costs:
   ``[stored value] = [value from ARIS] * energy_multiplier / [standard length months in the read period]``
*  For DemandUse:
   ``[stored value] = [value from ARIS] * energy_multiplier``

**``expected_period_months`` Optional Parameter**

In rare cases where the normal read period for the energy usage is something other
than one month, you can enter a different number of months using this
parameter. This value is used for estimating the previous read date when
the date wasn't set for the previous entry in ARIS, and for detecting
missing data when the previous read date is more than 1.75 * [expected
period months] earlier than the current read date.

Additional Required Settings
----------------------------

To use the BMON ARIS functionality you need to enter the URL, Username
and Password in your installation's settings.py file. The required
settings parameters are:

-  ``BMSAPP_ARIS_URL``
-  ``BMSAPP_ARIS_USERNAME``
-  ``BMSAPP_ARIS_PASSWORD``

Converting On/Off Events into Runtime Fraction
----------------------------------------------

Some sensors record the precise time of On and Off events. An example of
such a sensor is a Monnit Dry Contact sensor. This sensor posts a
reading every time its two contacts are closed or are opened, and the
sensor is often used to record when a device turns on and turns off. In
addition to seeing the exact times a device turned on and turned off,
it is often useful to record the *percentage of time* that the device
was on during evenly spaced intervals.

To provide this additional information, a special Calculated Field
function is provided in BMON. The function will create a separate
"sensor" in the BMON system that shows the fraction of time that a
device was On for every half-hour interval (or other user-configurable
interval). This function is called ``runtimeFromOnOff``, and here is an
example of its use:

.. image:: /_static/calc_ex3.png

The ``Unit`` entry generally should be ``runtime: Runtime Fraction`` or
``fraction: Occupied Fraction``. ``runtimeFromOnOff`` must be entered as
the ``Transform or Calculated Field Function Name``. Finally, you need
to provide the Sensor ID of the sensor that records the precise On and
Off times (that sensor needs to report a value of 1 when the device
turns on and a value of 0 when the device turns off). That Sensor ID is
entered as the ``onOffID`` parameter in the ``Function Parameters`` box:

::

    onOffID: 29631

In this example, the Sensor ID is ``29631``, an ID of a Monnit Dry
Contact sensor. By default, this function will calculate the runtime
fraction for every half-hour interval. If you would like to use a
different interval, add a second line to the ``Function Parameters``
box. For the above example, the following would be the entry for
calculating 15 minute runtime fractions:

::

    onOffID: 29631
    runtimeInterval: 15

This special runtime function is also useful with Motion or Occupancy
Sensors and 1-wire Motor Sensors used with the :ref:`mini-monitor`.

Estimating Pellet Consumption and Heat Output of an Okofen Pellet Boiler
------------------------------------------------------------------------

A `Periodic
Script <https://github.com/alanmitchell/bmon/wiki/Periodic-Scripts#collect-data-from-okofen-wood-pellet-boilers>`_
is available to collect data from Okofen Wood Pellet Boilers. One of the
Sensors indicates the Status of the boiler (the P241 sensor).
If the Boiler Status is in state 5 or 6, then the boiler is firing,
consuming pellets, and producing heat. A special calculated field has
been created, ``OkoValueFromStatus``, that allows you to create a new
field showing the pellet consumption rate or the heat output rate of the
boiler for every 5 minute interval. Here is an example of the function
in use:

.. image:: /_static/oko_value_func.png

There are the two critical parameters that should be provided for the
function, shown here with example values:

::

    statusID: HainesSrCtr_P241
    value: 127.17

The ``statusID`` parameter gives the Sensor ID of the boiler's Status
sensor. For the example, the Sensor ID is ``HainesSrCtr_P241``. When
this sensor reads a value of 5 or 6, the Okofen boiler is firing.

The ``value`` parameter is the pellet consumption rate or heat output
rate that occurs when the boiler is firing. For this example, that rate
is 127.17 pounds per day of pellets (the units were specified in the
``Unit`` entry of the sensor).

The calculated field will generate pellet consumption rates or heat
output rates for each 5 minute interval spanning the available Status
data set. It is often useful to the use the ``Data Averaging`` feature
of the ``Plot Sensor Values over Time`` graph to see the average rates
across day, week, or monthly periods.

Mathematical Calculated Fields
------------------------------

Unlike :ref:`transform-expressions`, there is unfortunately no general
method for creating calculated fields through use of math expressions.
Instead, there are a number of predetermined functions available for
creating calculated fields from existing sensor values. The table below
shows the functions available and use of the functions is explained in
the section following the table.

+------------------+----------------------------------------------------------------+
| Function Name    | Expression Performed                                           |
+==================+================================================================+
| linear           | | ``slope * val + offset``                                     |
|                  | |                                                              |
|                  | | ``slope``  default is 1.0                                    |
|                  | | ``offset`` default is 0.0                                    |
+------------------+----------------------------------------------------------------+
| AminusB          | | ``A - B``                                                    |
+------------------+----------------------------------------------------------------+
| AplusBplusCplusD | | ``A + B + C + D``                                            |
|                  | |                                                              |
|                  | | ``C`` default is 0.0                                         |
|                  | | ``D`` default is 0.0                                         |
+------------------+----------------------------------------------------------------+
| fluidHeatFlow    | | ``flow * (Thot - Tcold  * multiplier * (1.0-heat_recovery)`` |
|                  | |                                                              |
|                  | | ``heat_recovery`` default is 0.0                             |
+------------------+----------------------------------------------------------------+


Each one of these functions can create a Calculated Field based by
applying a mathematical expression to a number of variables. The
mathematical expression that is used is shown in the
``Expression Performed`` column of the table above. Each expression has
a number of variables. Each variable can either be a number or Sensor ID
(at least *one* of the variables *must* be a Sensor ID). Variables may
have default values, as indicated in the table above. If a variable has
a default value, it does not need to appear in the
``Function Parameters`` configuration box. Here is an example for the
``linear`` function:

.. image:: /_static/calc_ex5.png

In this example, there already is a sensor that reports the firing rate
of a boiler as a percentage value varying from 0 to 100. We now want to
create a Calculated Field that displays the rate of natural gas use of
the boiler, expressed in Btu/hour. Because the gas use and the firing
rate of the boiler are linearly related, we can use the ``linear``
Calculated Field function to create this gas usage field. Multiplying
the firing rate by 1500 will give the gas usage in Btu/hour since the
maximum gas usage of the boiler is 150,000 Btu/hour; a 100 firing rate
times 1500 gives a gas usage of 150,000.

The ``linear`` function has three variables: ``val``, ``slope``, and
``offset``. For our example, our conversion multiplier of 1500 is the
``slope`` variable, and you can see its entry in the
``Function Parameters`` in the above screenshot. The ``offset`` variable
is not needed in this application; BMON has a default value of 0.0 for
this variable, which is correct for our application, so therefore we
need not provide the variable in the ``Function Parameters`` box.
Finally, the ``val`` variable will be used for the Firing Rate sensor
values that we are using to calculate gas usage. Since this variable
needs to be filled in with sensor values, *we need to preface the
variable with ``id_``* to indicate that this variable is a set of sensor
values. Then, the value provided for the variable in the
``Function Parameters`` box is a Sensor ID:

::

    id_val: Burt158_firing_rate

The ``id_`` prefix on the variable ``val`` indicates that the variable
will be taken from an existing sensor. ``Burt158_firing_rate`` is the
Sensor ID of the firing rate sensor.

So, every 30 minutes BMON will gather up all of the
``Burth158_firing_rate`` sensor readings that have not already been used
previously in this calculation, and BMON will multiply the by 1500 to
create additional sensor readings for the ``Burt158_boiler_gas`` sensor.

Here is a more complicated example that creates a Calculated Field that
estimates the natural gas usage of a sidewalk snowmelt system based on
measuring supply and return temperatures and the runtime of a
circulating pump:

.. image:: /_static/calc_ex6.png

The Calculated Function being used here is the ``fluidHeatFlow``
function, as described in the table above. You can see in the
``Function Parameters`` box that the ``heat_recovery`` variable is *not*
provided in the configuration of this Calculated Field. Therefore, the
``heat_recovery`` variable will assume its default value of 0.0. Three
of the variables in the math expression for the ``fluidHeatFlow``
function come from existing sensor values: ``flow``, ``Thot``, and
``Tcold``. In the ``Function Parameter`` box, these variable names are
prefaced by the ``id_`` prefix, indicating the values provided are
Sensor IDs. The ``multiplier`` variable is not a sensor value but
instead the constant 14960.0.

Finally, you can see that the ``flow`` variable appears in the
``Function Parameter`` box as ``id_flow_sync``. As explained before, the
``id_`` prefix indicates that the variable comes from a Sensor. The
``_sync`` suffix indicates that the final calculated values for the new
sensor (``manor_snw1_gas``) should be synchronized on the timestamps of
this sensor. The other input sensor values (``Thot`` and ``Tcold``) will
be interpolated to these timestamp values when the calculation occurs.
If you have multiple sensor values entering into a Calculated Field, you
can add the suffix ``_sync`` to the variable whose timestamp values
should be used for the resulting calculated values. If you do not append
``_sync`` to one of the variable names, one of the inputs sensors will
be used for synchronization, but it will not be easy to determine which
one.
