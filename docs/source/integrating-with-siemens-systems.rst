.. _integrating-with-siemens-systems:

Integrating with Siemens Building Management Systems
=====================================================
This document describes how to create data files (CSV) in the Siemens Building Management System 
for integration into the BMON system. The specific steps shown here are specific to the 
`Siemens Insight APOGEE Building Automation Software Program <http://w3.usa.siemens.com/buildingtechnologies/us/en/building-automation-and-energy-management/apogee/pages/apogee.aspx>`_ 
version 3.7.0 (2005). The general goals of each step of the report building process are described here 
to assist in integrating your Siemens Buiding Data with BMON. 
See :ref:`General Method for Gathering Data from Building Automation Systems`
for one approach to pushing this data into BMON.

\* A few notes on Siemens-specific terminolgy used in this document.
``Point`` refers to a sensor or data point.
``Trend`` refers to a collection of points and their values over time. 


Configure Sampling Rate for Each Sensor
---------------------------------------

The first step to automatically exporting data from a Siemens system to BMON�s web-based monitoring 
tool is to select the sensors you would like to export, configure them to the correct time interval, 
and ensure that they are available for collection.


On the computer running the Siemens program open the ``Trend Definition Editor`` 

.. image:: /_static/trend_definition_editor.jpg

From the Trend menu, select ``Open`` and use the object selector to find the data sensor (referred to as points) you 
want to monitor. Use the asterisk wildcard \* to have the object selector list all potential points in the system.  
If you already know the names of the points you would like to add you can also use the wildcard to narrow down your 
results. For instance, to locate all points with "boiler" in their name use the following format: \*boiler\*
note that the wildcard should be added on both sides of the term unless you know the name starts with the term (format term\*)
or ends with the term (\*term) otherwise your search will yeild no results.

.. image:: /_static/tde_object_selector.jpg
 
Select a point by double clicking on it and define your parameters - depending on the sensor you will have a number of options 
which may include COV (change of value), Interval (time-based sample), and wizard (user assistance tool). For the purposes of
integrating with BMON systems, we will focus on the Interval option. 

.. image:: /_static/tde_point_trend_defs.jpg

Click add.
Select Interval and click ok

.. image:: /_static/trend_type.jpg

Select a sampling interval, and make sure ``Enable PC Collection`` is checked.

.. image:: /_static/trend_interval_definition.jpg
 
While not specified above, ``Panel Samples Desired`` and  ``PC Buffer Size`` may need to be adjusted based on the interval you select. 
``Panel Samples Desired`` refers to the number of samples taken **per** interval, while ``PC Buffer Size`` indicates the number of days 
worth of space the computer is available to hold. If adjusting these variables, take note of the ``Maximum Samples available at Panel`` 
as this indicates the maximum number of samples that can be collected per interval.
 
 
Get Data from Siemens Field Panel
---------------------------------


In order to build a report, first data must be imported from the field panel to the server.  This is done by creating a �Trend Collection Report.  
Open Report Builder

 

Select Definition >> New
 

Create a Trend Collection Report
 
Save this report. And run a test report by selecting �Definition -> Run Report�.

Build CSV Trend Report
----------------------


Once the system has been configured to obtain data from the field panel using the Trend Collection Report, the data can be summarized and saved as a CSV Trend Report.
Create a Trend Interval Report by going to �Definition -> New� and then choosing �Trend Interval Report� from the drop-down menu.
 


Configure Trend Points

 

Click Add
 

If you click find now, the object selector will auto-populate a list of all potential trend points.
 
Select the points you want to trend. You can select multiple points at a time by holding down the ctrl key. Then click ok.
 

The points will be added to the trend points list. Click OK
 





Configure the reporting interval, you have a few options. Then configure the output.






 

Check file and browse for the location for you file. Name the file. Make sure overwrite system date and time is checked. The click file format. Make sure Delimit Text and Comma are checked. Click OK until you are back to the Trend Interval Report screen. Check that the time format is 24 hours.
  


You can run the report to see if it is working. Go back to Definition and click save as. This will save your report program. 

 

Schedule Automatic Reports
--------------------------

Finally, the system needs to be set up to automatically collect the data from the field panel by scheduling a regular �Trend Collection Report� and then saving the data in a CSV file for export by scheduling a regular Report.  
Select Scheduler
 
 

Schedule>>New>>Trend Collection
Use the object selector to find the trend collection you just created. Set up the program to run daily, weekly, �., If you want reports more often you�ll need to set up a separate run for each time you want to collect a report.
 

Schedule>>New>>Report
Use the object selector to find the report you just created. Set up the program to run daily, weekly, �., If you want reports more often you�ll need to set up a separate run for each time you want to collect a report.


