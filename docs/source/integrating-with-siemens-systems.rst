.. _integrating-with-siemens-systems:

Integrating with Siemens Building Management Systems
=====================================================
This document describes how to create data files (CSV) in the Siemens Building Management System for integration into the BMON system. The specific steps shown here are specific to 
the `Siemens Insight APOGEE Building Automation Software Program <http://w3.usa.siemens.com/buildingtechnologies/us/en/building-automation-and-energy-management/apogee/pages/apogee.aspx>`_ version 3.7.0 (2005). 
The general goals of each step of the report building process are described here to assist in integrating your Siemens Buiding Data with BMON. 

\* A few notes on Siemens-specific terminolgy used in this document.
``Point`` refers to a sensor or data point.
``Trend`` refers to a collection of points and their values over time. 


Configure Sampling Rate for Each Sensor
---------------------------------------

The first step to automatically exporting data from a Siemens system to BMON’s web-based monitoring tool is to choose the sensors that you would like to export 
and configure them to the correct time interval and ensure that they are available for PC collection.


Open the ``Trend Definition Editor``, select open, use the object selector to find the data sensor (referred to as points) you want to monitor. Use “*” to have the object selector to list all the potential points in the system.  

 .. image:: /_static/trend_definition_editor.jpg

You can choose multiple points using the ctrl or shift button, each point opens a new window. 
 
 Click add.
 
Select Interval and click ok
Select a sampling interval, make sure to enable PC collection.
 
Get Data from Siemens Field Panel
---------------------------------


In order to build a report, first data must be imported from the field panel to the server.  This is done by creating a “Trend Collection Report.  
Open Report Builder

 

Select Definition >> New
 

Create a Trend Collection Report
 
Save this report. And run a test report by selecting “Definition -> Run Report”.

Build CSV Trend Report
----------------------


Once the system has been configured to obtain data from the field panel using the Trend Collection Report, the data can be summarized and saved as a CSV Trend Report.
Create a Trend Interval Report by going to “Definition -> New” and then choosing “Trend Interval Report” from the drop-down menu.
 


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

Finally, the system needs to be set up to automatically collect the data from the field panel by scheduling a regular “Trend Collection Report” and then saving the data in a CSV file for export by scheduling a regular Report.  
Select Scheduler
 
 

Schedule>>New>>Trend Collection
Use the object selector to find the trend collection you just created. Set up the program to run daily, weekly, …., If you want reports more often you’ll need to set up a separate run for each time you want to collect a report.
 

Schedule>>New>>Report
Use the object selector to find the report you just created. Set up the program to run daily, weekly, …., If you want reports more often you’ll need to set up a separate run for each time you want to collect a report.


