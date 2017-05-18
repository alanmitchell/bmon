.. _archiving-and-analyzing-data-from-the-system:

Archiving and Analyzing Data from the System
============================================

All of the data in the Building Monitoring System is stored in a
`SQLite <http://www.sqlite.org/>`_ database file. The SQLite database
file is stored as:

::

    <project root>/bmsapp/readingdb/data/bms_data.sqlite

A cron job entry is set up to periodically back that file up into the
directory ``<project root>/bmsapp/readingdb/data/bak`` (the cron job
calls the `backup script
backup_readingdb.py <https://github.com/alanmitchell/bmon/blob/master/bmsapp/scripts/backup_readingdb.py>`_.
The data file is gzipped and stored with a file name indicating when it
was backed up.

Any ad hoc analysis of the data can be done by simply copying the SQLite
data file or one of the backed up versions of the data file onto a
separate system for analysis. A number of client applications are
available to display and query SQLite database data. Most programming
and scripting languages have drivers for accessing SQLite data. So,
there are many tools available to analyze the data.

The data structure within the SQLite database is simple. The data from
each sensor occupies its own table. The name of the table is the
``Sensor ID`` that is entered in the Admin interface for the Building
Monitoring System. For example, for Monnit Wireless Sensors, the sensor
ID is the Monnit ID, e.g. ``27613``. (When using SQL statements to query
the data, table names that are numeric, such as ``27613`` should be
enclosed in square brackets, e.g. ``[27613]``, in order for proper
execution of the SQL statement.)

Each sensor table has two fields:

*  ``ts``: The time the sensor reading occurred as an integer UNIX
   timestamp (seconds past Midnight Jan 1, 1970 UTC).
*  ``val``: The value of the sensor reading in the final engineering
   units. Those units can be found in the Sensors table in the Admin
   interface.

If it is necessary to remove older data from the active SQLite database,
normal SQL commands can be used to select and delete data prior to a
particular timestamp. The easiest approach is probably to write a Python
script to perform the deletion. Note that code similar to the following
can be used to iterate across each sensor table present in the database:

.. code:: python

    import sqlite3
    conn = sqlite3.connect(fname)

    # use the SQLite Row row_factory for all Select queries
    conn.row_factory = sqlite3.Row

    # now create a cursor object
    cursor = conn.cursor()

    # iterate across the sensor tables        
    for rec in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall():
        print rec['name']    # Prints the table name, which is the Sensor ID

Note that there are two special tables in the database that are *not*
sensor tables. Those are the ``_last_raw`` table, which holds the last
reading posted from certain tables, and the ``_junk`` table, which is
used to lock the database when a backup is occurring.

In some cases, it may be useful to install a web-based database
administration tool onto the server where BMON is hosted. This will
facilitate archiving, exporting, and data cleaning operations. One such
tool is `phpLiteAdmin <https://code.google.com/p/phpliteadmin/>`_,
which can provide a web-based interface to the sensor reading database.
The tool allows viewing the sensor data, executing SQL statements, and
exporting sensor reading tables. Installation of the tool is
straight-forward and documented on the web page link above. When using
the Webfaction hosting service, installation of the ``Static/CGI/PHP``
application is required to run the phpLiteAdmin tool, as this tool is a
PHP web application.
