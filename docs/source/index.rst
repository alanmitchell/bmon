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
electricity usage of the AHFC Headquarters building (the green bands
indicate the building’s occupied periods):


.. image:: /_static/sample_screen.png

Note that a major upgrade to Python 3.7 occurred on May 1, 2019.
Upgrade of existing systems running the Python 2.7 version will
require assistance from the developer, Alan Mitchell, alan@analysisnorth.com.
Please contact him before attempting an upgrade.

The documentation for the BMON software is divided into
three main sections, described below.

:ref:`System Administrator Introduction <system-administrator-introduction>`
----------------------------------------------------------------------------

This section describes how to install the BMON application on a web
server, which will require some basic skills with Linux system
administration. This section also describes how to setup and configure
the specific buildings and sensors for your system. The setup of sensors
and buildings does *not* require any sophisticated IT skills; it is
accomplished through a web interface after logging on to the system as
an administrator.

:ref:`Developer Introduction <developer-introduction>`
------------------------------------------------------

This section provides documentation for developers who want to modify
the code of the BMON system. The source code of the project is
internally documented with comments, but the documentation in this section
explains the overall structure of the application. The GitHub repository
holding the source code is `located here <https://github.com/alanmitchell/bmon>`_

:ref:`Contact Information <contact-info>`
-----------------------------------------

Contact information for key BMON personnel and developers is available
here.

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: System Administrators   
   
   system-administrator-introduction
   how-to-install-BMON-on-a-web-server
   how-to-install-BMON-locally
   adding-buildings-and-sensors
   multiple-organizations
   setting-up-sensors-to-post-to-bmon
   multi-building-charts
   sensor-alerts
   creating-a-dashboard
   transform-expressions
   calculated-fields
   periodic-scripts
   custom-jupyter-notebook-reports
   custom-reports
   archiving-and-analyzing-data-from-the-system
   system-performance-with-high-loading
   using-csv-transfer
   
.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: Developers
   
   developer-introduction
   bmon-architecture
   writing-periodic-scripts
   api-data-access
   
.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: Contact Info
   
   contact-info
 
 