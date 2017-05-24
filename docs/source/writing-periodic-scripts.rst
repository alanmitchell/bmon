.. _writing-periodic-scripts:

Writing Periodic Scripts
========================

Periodic Scripts are useful for running tasks that need to occur on
a repeated basis. Possible uses include collecting data from external sources,
running reports, or performing maintenance tasks. Check out the :ref:`Periodic Scripts <periodic-scripts>`
page for more detail on their uses and configuration in BMON. The intent of
this page is to provide some guidance to Developers wishing to write a custom
Periodic Script that can be run by BMON.

When writing a custom Periodic Script, it is helpful to look at an example
script. The ``bmon/bmsapp/periodic_scripts/okofen.py`` is one such example. A somewhat more complicated example is
``bmon/bmsapp/periodic_scripts/ecobee.py``.

Basic Requirements of a Custom Periodic Script
----------------------------------------------

There are a few requirements for a custom Periodic Script:

* The script must reside in a Python file located in the ``bmon/bmsapp/periodic_scripts/`` directory.
* That Python file must have a ``run()`` function that, at a minimum, accepts arbitrary keyword arguments; i.e. it must have a ``**kwargs`` parameter.
* The return value from the ``run()`` function must be a Python dictionary, although it can be an empty dictionary if there is no need for a return value.

More details on these requirements are presented below.

Arguments Passed to the ``run()`` Function
------------------------------------------

The Periodic Script resides in a Python file located in the
``bmon/bmsapp/periodic_scripts/`` directory. The name of the Python file,
excluding the ".py" extension is the File Name that is entered in the
Periodic Script configuration inputs. The ``run()`` function in that
file is called at the periodic interval specified when the BMON System
Administrator configures the script.

Here is the minimum signature of the ``run()`` function, which must allow for arbitrary keyword arguments:

.. code:: python

    def run(**kwargs):
        # Script code goes here

The ``run()`` function can also include specific keyword parameters with default values, such as:

.. code:: python

    def run(account_num='', units='metric', **kwargs):
        # Script code goes here

When the ``run()`` function is called, it is passed a number of keyword
arguments, and the arguments are generated from these sources:

1. The ``Script Parameters in YAML form`` input from the Periodic
   Script configuration inputs. As an example, if the Script Parameters input
   is:

   .. code:: yaml

    account_num: 1845236
    include_occupancy: True

   the ``run()`` function will be called with these arguments:

.. code:: python

    run(account_num=1845236, include_occupancy=True)

2. The Results returned from the prior run of the Script. As discussed in more detail below, the Periodic Script returns a Python dictionary.
   Each one of the key/value pairs in that dictionary are converted to
   keyword arguments and passed to the next run of the script. Continuing
   the example above, if the Script returned the following Python dictionary:

   .. code:: python

    {'last_record': 2389, 'last_run_ts': 143234423}

   the next call to the ``run()`` function of the Periodic Script will
   look like this:

   .. code:: python

    run(account_num=1845236, include_occupancy=True, last_record=2389, last_run_ts=143234423)

   This example shows the arguments combined from the two sources mentioned so far.
    
3. There is special treatment of return values that are in the ``hidden`` key of the return dictionary. The purpose of the ``hidden`` key is
   discussed in more detail below, but the return values in that key are processed differently than other keys. The ``hidden`` key should contain another dictionary of key/value pairs, and those key/value pairs are
   extracted from the ``hidden`` value and passed to the ``run()`` function as separate arguments. Continuing the above example, if ``run()`` returns the following dictionary:

   .. code:: python

    {'last_record': 2389, 'last_run_ts': 143234423, 'hidden': {'auth_key': 'x4ab72i'}}

   the next call to the ``run()`` function of the Periodic Script will look like this:

   .. code:: python

    run(account_num=1845236, 
        include_occupancy=True, 
        last_record=2389, 
        last_run_ts=143234423,
        auth_key='x4ab72i')

If the same keyword argument appears in more than one of the above sources, the highest priority is ``Script Parameters in YAML form``, then visible results from the prior run of the script, and finally hidden results from the prior run of the script.


The Return Value from the ``run()`` Function
--------------------------------------------

There are a few different purposes for the Python dictionary that is returned from the ``run()`` function:

*  As stated before, values in that dictionary are passed as arguments
   to the next call to the ``run()`` function. This can be useful for tracking
   things like the time or ID of the last record extracted from a data source, so
   that future calls only extract newer data. (Note that storing the same sensor
   reading multiple times in BMON does *not* cause an error.)
*  The values returned by ``run()`` are displayed in the Django Admin
   interface, so are useful for debugging script problems or displaying status
   messages. The values appear in the ``Script results in YAML form`` field on the form used
   to configure the Periodic Script. The exception to this are the values that appear
   in the special ``hidden`` key in the return dictionary; they are not displayed in
   the configuration form, but are passed to the next call to the ``run()`` function. This
   feature is useful for storing authorization keys that should not be readily viewed by
   the System Administrator. The feature is also useful if some of the return
   values from the script would be confusing or not useful if viewed in the System Admin interface.
*  Sensor readings acquired by the Periodic Script can be returned in
   the special ``readings`` key in the return dictionary, and these readings will be
   automatically stored in the BMON sensor reading database (more detail later).
*  A list of Script Parameter names can be returned in the special
   ``delete_params`` key, and these parameters will automatically be deleted from the
   ``Script Parameters in YAML form`` input on the Periodic Script configuration form. This can useful for
   deleting out authorization keys that are no longer valid or should be hidden from
   the System Administrator. An example use of the ``delete_params`` key in a return dictionary
   is: ``{'last_record': 2389, 'delete_params': ['access_token', 'refresh_token']}``. After this dictionary is returned, the script parameters ``access_token``
   and ``refresh_token`` will be deleted from the ``Script Parameters in YAML form`` input, if
   they exist there. Also, this ``delete_params`` key/value pair will *not* be
   passed to the next call of the ``run()`` function and will not be displayed in the
   Script Results field in the Admin interface.

A common use of a Periodic Script is to collect sensor readings from an external source. A
special feature has been built into the Periodic Script framework to allow for easy
storage of those collected readings. If the Script returns the sensor readings as a list
of 3-element-tuples, and that list is stored in the ``readings`` key of the return dictionary,
the readings will automatically be stored in BMON's sensor reading database. Here is an example
return dictionary that contains three sensor readings that will be stored by BMON:

.. code:: python

    { 'readings': [(1479769950, '311015614158_temp', 70.1),
                   (1479769950, '311015614158_heat_setpoint', 69.0),
                   (1479769950, '311015614158_rh', 23)]
    }

Each reading is formatted in a 3-element tuple:

::

    (Unix Timestamp of reading, Sensor ID, Reading Value)

These reading values are not displayed in the ``Script Results`` field of the configuration
screen, but the storage message returned by the BMON sensor reading database is
displayed. Here is an example:

.. image:: /_static/script_results.png

The ``reading_insert_message`` indicates that on the last run of this Periodic Script,
15 readings were collected and stored in the BMON sensor reading database.

The Script Results example above also shows some other data that is added to
the Script Results for display to the System Admin. The time when the script ran
last is shown, and the amount of time required to run the script is shown. Had an
error been raised by the script, the traceback from that error would be shown here
as well.

Note that the Periodic Script can collect sensor readings and have them stored in
the BMON sensor reading database.  However, those readings will not be displayed in
charts and reports without configuring each Sensor ID in the `Sensors` table using
the Admin interface. This process is described in the "Adding Sensors" section 
of the :ref:`adding-buildings-and-sensors` document.



