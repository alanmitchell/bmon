"""
This script takes an established sensor id and an optional start time to poplulate the database with historic data from the relavent enphase PV system. To start from the time the system became operational do not include a start time arguement.
The corresponding system_id and user_id must be contained in the sensor parameters.

It should be run using the django-extensions runscript facility:
 
    manage.py runscript import_enphase --script-args=desired_sensor_id

    or

    manage.py runscript import_enphase --script-args=desired_sensor_id start_time

arguments are the sensor_id and optionally the desired starting unix timestamp
output is some kind of success message or something probably
"""

import sys 
import logging
import yaml
import time
import sqlite3
from bmsapp.readingdb import bmsdata
from bmsapp.calcs import calcreadings, calcfuncs01, enphase
import bmsapp.models

wait_time = 7

def run(desired_sensor_id, start_time=None):
    
    #open database for insert commands
    while True:
        try:
            reading_db = bmsdata.BMSdata()
            break
        except sqlite3.OperationalError:
            time.sleep(wait_time)

    #get the appropriate sensor from a dictionary of all sensors using desired id 
    calc_sensor = bmsapp.models.Sensor.objects.filter(sensor_id=desired_sensor_id)
    
    #get the sensor parameters (for Enphase systems, the system id and user id)
    #the parameters should be yaml format
    try:
        system_params = yaml.load(calc_sensor[0].function_parameters)
    except IndexError:
        #if calc_sensor is empty then the input sensor id is invalid
        raise IndexError("Sensor ID not found")

    #get the unit id to determine what is being measured (energy(kWh) or power(kW))
    meas_unit_id = calc_sensor[0].unit_id
    #get the measurement associated with the unit id (This could vary depending on bmon installation)
    meas_type = bmsapp.models.Unit.objects.filter(id=meas_unit_id)[0].measure_type

    #the keywords in the enphase API response are "powr" (W) and "enwh" (Wh)
    #other measurements will cause the script to end
    if meas_type == 'power':
        enph_meas_type = 'powr'
    elif meas_type == 'energy':
        enph_meas_type = 'enwh'
    else:
        print "This sensor is measuring %s." % meas_type
        print "Enphase only reports measurements of energy or power."
        sys.exit()

    #The time the enphase system came online is obtained if start_time isn't passed.
    #The summary request has the relevant info under 'operational_at' in unix time
    if start_time == None:
        summary = enphase.System(**system_params).summary()
        start_time = summary['operational_at']
    

    #current unix time
    now = int(time.time())

    #cycle through all days from when the cycle became operational to now
    while start_time < now:
        #query the day starting at start_time
        obs = enphase.System(**system_params).stats(start_time)

        #select the relevent values and convert from W or Wh to kW or kWh
        #power values are the average power during each interval
        #energy values are the cumulative energy produced during each interval
        val_array = [ float(item[enph_meas_type])/1000 for item in obs['intervals']]
        #Time stamp represents the end of the measurement interval
        time_array = [ item['end_at'] for item in obs['intervals']]

        #zip values and timestamps into list of tuples
        recs = zip(time_array, len(time_array)*[calc_sensor[0].sensor_id], val_array)

        #cycle through values in recs and insert into database
        for ts, id, val in recs:
            reading_db.insert_reading(int(ts), str(id), float(val))

        #increment start_time by 86400 seconds (24 hours)
        start_time += 60*60*24

        #wait between each query to remain well below 10 hits per min
        time.sleep(wait_time)

    reading_db.close()
