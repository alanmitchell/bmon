.. _system-administrator-introduction:

System Administrator Introduction
=================================

This documentation explains how to install and
configure the system for your particular buildings and sensors. These
activities should be the task of one or two system administrators who
have more experience with BMON than the general Users who are simply 
interested in viewing and analyzing the data.

The separate system administrator topics are summarized below, and the
associated documents are available through the sidebar on the left or
by clicking on the section headings below.

:ref:`BMON Installation <how-to-install-BMON-on-a-web-server>`
--------------------------------------------------------------

This document gives instructions for installing BMON on a web server.
Linux skills and preferably some experience with Python and Django are necessary
to perform this task.

:ref:`Adding Buildings and Sensors <adding-buildings-and-sensors>`
------------------------------------------------------------------

After installing BMON, you will need to configure your Buildings and
Sensors in the system. This document shows how to do that using the
web-based Admin interface of the BMON system.

:ref:`Setting Up Sensors to Post to BMON <setting-up-sensors-to-post-to-BMON>`
------------------------------------------------------------------------------

A few different sensor types have been set up to work with BMON (e.g.
`Monnit Wireless Sensors <http://www.monnit.com/>`_). Other sensors that
have access to the Internet can be configured to work with BMON. This
document gives details on how to set up sensors in the system.

:ref:`Multi-Building Charts <multi-building-charts>`
----------------------------------------------------

BMON can produce some reports and graphs that compare data across
buildings. These multi-building charts need to be configured through the
web-based Admin interface. Single building reports and charts work
out-of-the-box without additional configuration.

:ref:`Sensor Alerts <sensor-alerts>`
------------------------------------

You can have BMON send you a text message or email if important sensor
conditions occur, such as Domestic Hot Water temperatures that are too low.
This document details how to configure this feature.

:ref:`Creating A Dashboard <creating-a-dashboard>`
--------------------------------------------------

A summary "Dashboard" can be created for any of the buildings in the
BMON system. Here is an example:

.. image:: /_static/sample_dashboard.png

This document describes how Dashboards are created.

:ref:`Custom Reports <custom-reports>`
--------------------------------------

This document explains how to create Custom Reports.
A Custom Report allows you to combine any number of graphs, dashboards,
or current value reports onto one page. The various elements can
even come from different buildings. 

:ref:`Transform Expressions <transform-expressions>`
----------------------------------------------------

Some sensors do not send data in a displayable format, some sensors have small errors that need correction.
"Transform" expressions allow you to convert units or transform values
before storage and display in BMON. This document explains how to set up transform values for your sensors.

:ref:`Calculated Fields <calculated-fields>`
--------------------------------------------

This document explains how to work with calculated fields. Occasionally, you may want to calculate a value from multiple different sensors or
have one sensor display its value in two different ways. "Calculated
Fields" serve this need. Also, Calculated Fields can be used to acquire
data from Internet weather services instead of installing your own
meteorological sensors.

:ref:`Periodic Scripts <periodic-scripts>`
------------------------------------------

Sometimes a process needs to occur repeatedly on a periodic basis. Often
this is used to acquire data from a piece of equipment or a server
connected to the Internet. It also could be used to create and send a
report or perform a maintenance operation. The *Periodic Script* feature
of BMON can be used for this purpose. There are some periodic scripts
that are already available in BMON (such as to acquire data from Ecobee
thermostats), and it is possible for a developer to create new scripts
that will be periodically run by BMON, this document explains the basics of 
Periodic Scripts while a later document details writing custom scripts.

:ref:`Archiving Data <archiving-and-analyzing-data-from-the-system>`
--------------------------------------------------------------------

This document explains how sensor data is stored in BMON and how it can
be archived or exported from the system for analysis elsewhere (basic
knowledge of database systems is required). The document is also useful
if you need to clean-up or remove data from the system.

:ref:`Mini Monitor <mini-monitor>`
----------------------------------

The "Mini-Monitor" is an inexpensive data acquisition device built using
the `Raspberry Pi <https://www.raspberrypi.org/>`_ computer. It was
designed and deployed as part of the BMON project, and it is described
further in this document.

:ref:`System Capacity <system-performance-with-high-loading>`
-------------------------------------------------------------

A stress test was done on the BMON system using high rates of sensor
reading posts and chart/report requests. Also, large amounts of
historical data were present in the test. This document describes the
results of that testing.
