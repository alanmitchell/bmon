BMON: Building Monitoring and Analysis Web Application
======================================================

Copyright (c) 2014, Alaska Housing Finance Corporation. All Rights Reserved.

.. _intro:

BMON is a web-based software application that stores and analyzes sensor
data coming from buildings or other facilities. The application was
developed by the Alaska Housing Finance Corporation (AHFC) to find ways
to reduce the energy use and improve the maintenance of their buildings.
The application presents a simple user interface for viewing data, but
includes informative charts such as Histograms and Hourly Profile charts
for analyzing the data. Alerts can be set up to text or email
individuals if sensor values move outside normal ranges.

Here is a link to the `AHFC BMON Web Site <https://bms.ahfc.us/>`_

Here is a screenshot of the application being used to look at the
electricicty usage of the AHFC Headquarters building (the green bands
indicate the building’s occupied periods):


.. image:: /_static/sample_screen.png

This Wiki holds the documentation for the software. The documentation is
divided into three main sections, described below and available on the
sidebar menu on the righthand side of this screen.

:ref:`User Introduction <user-introduction>`
--------------------------------------------

This section contains documentation for users who are viewing and
analyzing the data in the system. This documentation does not address
any issues related to installing and configuring the system.

:ref:`System Administrator Introduction <system-administrator-introduction>`
----------------------------------------------------------------------------

This section describes how to install the BMON application on a web
server, which will require some basic skills with Linux system
administration. This section also describes how to setup and configure
the specific buildings and sensors for your system. The setup of sensors
and buildings does *not* require any sophisticated IT skills; it is
accomplished through a web interface after logging on to the system as
an adminstrator.

:ref:`Developer Introduction <developer-introduction>`
------------------------------------------------------

This section provides documentation for developers who want to modify
the code of the BMON system. The source code of the project is
internally documented with comments, but the documentation in this Wiki
explains the overall structure of the application. The GitHub repository
holding the source code is `located here <https://github.com/alanmitchell/bmon>`_

:ref:`Contact Information <contact-info>`
-----------------------------------------

Contact information for key BMON personnel and developers is available
here.



Contents
^^^^^^^^
.. toctree::
   :maxdepth: 1
   
   user-introduction
   system-administrator-introduction
   how-to-install-BMON-on-a-web-server
   adding-buildings-and-sensors
   setting-up-sensors-to-post-to-bmon
   multi-building-charts
   sensor-alerts
   creating-a-dashboard
   custom-reports
   transform-expressions
   calculated-fields
   periodic-scripts
   archiving-and-analyzing-data-from-the-system
   mini-monitor
   system-performance-with-high-loading
   developer-introduction
   bmon-architecture
   writing-periodic-scripts
   contact-info
 
 



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`