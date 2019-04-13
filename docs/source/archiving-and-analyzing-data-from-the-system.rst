.. _archiving-and-analyzing-data-from-the-system:

Backing Up and Analyzing Data from the System
=============================================

Data Files and Local Backups
----------------------------

All of the sensor reading data in the Building Monitoring System is stored in a
`SQLite <http://www.sqlite.org/>`_ database file. The Sensor Reading SQLite database
file is stored as:

::

    <project root>/bmsapp/readingdb/data/bms_data.sqlite

In addition to the Sensor Reading data, the metadata that adds information about
sensors, buidlings, organizations etc. is available in the Django database supporting
the BMON application.  This is also a SQLite database and is located at:

::

    <project root>/bmon.sqlite

These two databases are automatically backed up locally by the BMON application.
The Sensor Reading database is backed
up every 3 days and stored in the directory ``<project root>/bmsapp/readingdb/data/bak``.
The backup is performed by calling the `backup script
backup_readingdb.py <https://github.com/alanmitchell/bmon/blob/master/bmsapp/scripts/backup_readingdb.py>`_.
The data file is gzipped and stored with a file name indicating when it
was backed up.  Backup files older than 21 days are deleted.

The Django database is backed up daily into the local directory
``<project root>/bak``. It is also compressed with gzip and stored
with a filename indicating the
date of backup.

It is advisable to also store these backup files off-server, and the last section
on this page suggests a method to do that.

Web-based Administration of the Sensor Reading Database
-------------------------------------------------------

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


Analyzing the Sensor Reading Data
---------------------------------

Any ad hoc analysis of the sensor reading data can be done by simply copying the SQLite
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

*  ``ts`` The time the sensor reading occurred as an integer UNIX
   timestamp (seconds past Midnight Jan 1, 1970 UTC).
*  ``val`` The value of the sensor reading in the final engineering
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

Off-Server Backup of Data Files
-------------------------------

It is advisable to back up the two database files to a location off of
the BMON server.  One approach to this is to use the
`Amazon Web Services (AWS) S3 Storage Service <https://aws.amazon.com/s3/>`_
as the destination of those backups.  To use the service, there are a
number of requirements:

- An AWS Account.
- Installation of the AWS Command Line Interface on the BMON server as `described here <https://aws.amazon.com/cli/>`_.
- Installation of AWS credentials on the BMON server as `described here <https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html>`_.
- Creation of an S3 Bucket to copy the data files into.  This can be done
  through the online AWS console.
- Adding lines to the BMON server crontab file to periodically copy backup files to the S3 bucket.

Here is an example of the crontab jobs used to backup both the sensor reading
and Django database files:

.. code:: bash

    18 11,23 * * * ~/bin/aws s3 sync ~/webapps/django/bmon/bak s3://bmon.xyz.com/ahfc/django
    25 11,23 * * * ~/bin/aws s3 sync ~/webapps/django/bmon/bmsapp/readingdb/data/bak s3://bmon.xyz.com/ahfc/data --storage-class ONEZONE_IA

These crontab jobs copy any new files from the two BMON backup directories
to the S3 bucket.  Both jobs run twice a day.  The large sensor reading database file
uses the S3 storage class of ONEZONE_IA (One Zone Infrequent Access) to reduce
storage costs.

A `Lifecycle Rule <https://docs.aws.amazon.com/AmazonS3/latest/dev/object-lifecycle-mgmt.html>`_
was established on the S3 storage bucket to delete backup files that are
older than 90 days.

For Alaska-owned BMON Servers, an expense-free S3 bucket with associated
credentials is available to backup BMON data files.  Contact Alan Mitchell
at alan@analysisnorth.com.
