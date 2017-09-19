.. _using-csv-transfer:

Using CSV Transfer
==================

This document provides basic instructions on installing and using the `CSV-Transfer Utility <https://github.com/alanmitchell/csv-transfer />`_ to import data files into BMON. 
The instructions provided are written based on having performed a `local BMON installation <how-to-install-BMON-locally />`_ but should work similarly if you have installed
BMON on a Webfaction server based on `these instructions <how-to-install-BMON-on-a-web-server />`_.

The skills needed for installation are primarily:

*  Linux command line skills - it is assumed you are familiar so explanations of basic linux command line operations are not included in this documentation.

Installing Dropbox
------------------

.. note:: The steps in this section are patterned after the general instructions from Digital Ocean's `How To Install Dropbox Client as a Service on Ubuntu 14.04 <https://www.digitalocean.com/community/tutorials/how-to-install-dropbox-client-as-a-service-on-ubuntu-14-04/>`_


| Determine your bit version of Linux by running 
| ``uname -a``
	
x86_64 means 64 bit, x86 means 32 bit, this is important when installing dropbox, the wrong version won't work

| for 64 bit run
| ``curl -Lo dropbox-linux-x86_64.tar.gz https://www.dropbox.com/download?plat=lnx.x86_64``

| for 32 bit run 
| ``curl -Lo dropbox-linux-x86.tar.gz https://www.dropbox.com/download?plat=lnx.x86``

| Next do the following
| ``sudo mkdir -p /opt/dropbox``
| ``sudo tar xzfv dropbox-linux-x86_64.tar.gz --strip 1 -C /opt/dropbox``

| Start dropbox by entering	
| ``/opt/dropbox/dropboxd``
	
| Link your dropbox account by copying the URL the dropbox client prints and visiting it in a web browser, it keeps printing until you link your account or kill the process
| example: \https://www.dropbox.com/cli_link_nonce?nonce=21dd10ebd693c7865787c4168fd452b3
	
Wait for the message *This computer is now linked to Dropbox. Welcome USERNAME* to appear on your bmon server

Kill the process by pressing ``Ctrl-C``

| Set up a service script

| ``sudo curl -o /etc/init.d/dropbox https://gist.githubusercontent.com/thisismitch/d0133d91452585ae2adc/raw/699e7909bdae922201b8069fde3011bbf2062048/dropbox``
| ``sudo chmod +x /etc/init.d/dropbox``

| Create a Default Users File
| ``sudo nano /etc/default/dropbox``

*example file*

----------------------

DROPBOX_USERS="USERNAME" 

----------------------

where USERNAME is your linux username (not to be confused with your Dropbox username)

| Reload the Daemon and Start Dropbox
| ``sudo systemctl daemon-reload``
| ``sudo systemctl start dropbox``
| ``sudo update-rc.d dropbox defaults``

Installing Required Packages
----------------------------

| Start in your home directory
| ``cd $home``

**Install the Required Packages**

.. note:: If you followed the instructions from :ref:`how-to-install-BMON-locally` you may have already installed these packages. However, they were installed in the virtual environment which is encapsulated in its own entity. You will need to install these packages again to the non-virtual environment so the csv transfer tool can access them.

| ``sudo pip install pyyaml``
| ``sudo pip install requests``
| ``sudo pip install pytz``

Installing CSV Transfer
-----------------------

| Start in your home directory
| ``cd $home``

| 
| ``sudo git clone https://github.com/alanmitchell/csv-transfer.git``

| Go to the CSV Transfer Folder
| ``cd csv-transfer``

| Create a config.yaml file
| ``sudo cp sample_config.yaml config.yaml``

The README file provided with csv-transfer includes more thorough documentation on explaining all of the parameters in the config file, see it for more information before proceeding either via ``sudo nano README`` or by visiting the `csv-transfer github repository <https://github.com/alanmitchell/csv-transfer />`_ online. Some basic tips are provided below to aid in properly configuring and running csv transfer successfully.

You will need to edit the ``config.yaml`` file to instruct it where and how to read your files, do this by running ``sudo nano config.yaml``

An example from a test config.yaml file: 

| csv_files:
|   - file_glob: "/home/cchrc/Dropbox/Foundation/BAfoundation.csv"
|     file_type: generic
|     chunk_size: 10
|     header_rows: 4
|     name_row: 2
|     field_map: "lambda nm: '_'.join(nm.split('_')[:2])"
|     ts_tz: America/Anchorage
|     exclude_fields: [RECORD]
| 
| # List of consumers of the CSV records
| consumers:
|   - type: bmon
|     poster_id:  cc-bmon-01              # unique ID for this posting object
|     bmon_store_url: \http://172.20.127.167/readingdb/reading/store/
|     bmon_store_key: BiGFfNPnBCxH
| 

| **Things to know**
| To add a second, third, fourth file etc. you would insert a new block starting with csv_files: and including all the relevant information, entering between earlier csv_files statements and # List of consumers (which you do not need to duplicate)
| ``file_glob:`` indicates the path where your files are stored in your Dropbox folder, wild-cards (*.csv) are accepted if all of your files are in the same directory and will upload all files meeting that criteria
| ``header_rows:`` the number of rows in the beginning of your file to be considered header or which do not contain data you wish to upload (see csv example below)
| ``name_row:`` indication of which row (within the header count) contains the column names of your data, a 2 here means that of the 4 header rows, the second row contains column names (see csv example below)	
| ``ts_tz:`` enter the appropriate timezone for your area and/or the area the data is being generated	
| ``exclude_fields:` if you have arbitrary fields, like record numbers, you can enter them here to have them omitted from the import
| ``poster_id:`` enter a unique id
| ``bmon_store_url:`` is the full URL to the storage function of the BMON server, this will include \http://SERVER IP OR URL/readingdb/reading/store, the only information to be changed is the portion immediately following \http://  
| ``bmon_store_key:`` each BMON server has a unique and secret storage key string; providing this string is required for storing data on the BMON server, copy this from your bmon settings.py file

| Run CSV Transfer and upload your data
| ``sudo ./csv-transfer.py config.yaml``


Incorporating Your Imported Data Into BMON
------------------------------------------
Follow the :ref:`adding-sensors` instructions to add sensors to BMON if you haven't done so already. The data structure within the SQLite database that BMON runs on is simple. The data from each sensor occupies its own table. The name of the table is the ``Sensor ID`` in our case it's the column name from our csv file - with a caveat that the import doesn't import more than one underscore of the column name so, based on the example below SOLAR_TundertankONEFOOT_F_Avg would become SOLAR_TundertankONEFOOT

An example .csv file

| "TOA5","Southlab","CR1000","2354","CR1000.Std.12","CPU:southlabfound_withsoiltemps_June2015.CR1","35898","SOLAR_TankSoilT_Day"
| "TIMESTAMP","RECORD","SOLAR_TundertankBOTTOM_F_Avg","SOLAR_TundertankONEFOOT_F_Avg","SOLAR_TundertankTWOFEET_F_Avg","SOLAR_TundertankTHREEFEET_F_Avg"
| "TS","RN","","","",""
| "","","Avg","Avg","Avg","Avg"
| "2015-06-18 00:00:00",0,32.39,85.7,33.68,34.91
| "2015-06-19 00:00:00",1,32.41,86.7,33.77,34.97
| "2015-06-20 00:00:00",2,32.47,87.4,33.87,35.07
| "2015-06-21 00:00:00",3,32.52,86.8,34.01,35.17
| "2015-06-22 00:00:00",4,32.58,83.2,34.17,35.3
| "2015-06-23 00:00:00",5,32.63,71.38,34.31,35.41
| "2015-06-24 00:00:00",6,32.69,70.2,34.39,35.53
| "2015-06-25 00:00:00",7,32.75,70.33,34.48,35.65
| 

Troubleshooting
---------------

If you run the csv transfer tool and receive InsecurePlatformWarning or InsecureRequestWarning messages, do the following:

| ``sudo nano /csv-transfer/consumers/httpPoster2.py``

comment out the following lines by adding a # character at the beginning of each line

| ``from requests.packages.urllib3.exceptions import InsecureRequestWarning, InsecurePlatformWarning``
| ``requests.packages.urllib3.disable_warnings(InsecureRequestWarning)``
| ``requests.packages.urllib3.disable_warnings(InsecurePlatformWarning)``

to

| ``#from requests.packages.urllib3.exceptions import InsecureRequestWarning, InsecurePlatformWarning``
| ``#requests.packages.urllib3.disable_warnings(InsecureRequestWarning)``
| ``#requests.packages.urllib3.disable_warnings(InsecurePlatformWarning)``














