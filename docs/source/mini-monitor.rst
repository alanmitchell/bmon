.. _mini-monitor:

Mini Monitor
============

The "Mini-Monitor" is an inexpensive data acquisition device built using
the `Raspberry Pi <https://www.raspberrypi.org/>`_ computer. It was
designed and deployed as part of the BMON project primarily as means of
collecting data from boiler systems serving small 3 - 8 plex residential
buildings. Through use of an RS-485 serial interface to the Raspberry
Pi, the Mini-Monitor was programmed to read sensor and status
information directly from Burnham Alpine boilers that utilize the Sage
controller. The Mini-Monitor also has the ability to read `1-Wire
Temperature <http://en.wikipedia.org/wiki/1-Wire>`_ and Motor Sensors in
the boiler room. The data from all of these sources is posted directly
to the BMON system.

The Mini-Monitor was also programmed to read data directly from the
AERCO BMS II Boiler Management System, which is a large commercial
boiler controller.

Documentation for the Mini-Monitor project is provided in a `separate
Wiki <../../mini-monitor/wiki>`_.
