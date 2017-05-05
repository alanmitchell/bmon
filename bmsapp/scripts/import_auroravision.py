"""
This script takes an established sensor id and an optional start time to poplulate the database with historic data from the relavent auroravision PV system. To start from the time the system became operational do not include a start time arguement.
The corresponding system_id must be contained in the sensor parameters.

It should be run using the django-extensions runscript facility:
 
    manage.py runscript import_auroravision --script-args=desired_sensor_id

    or

    manage.py runscript import_auroravision --script-args=desired_sensor_id start_time

arguments are the sensor_id and optionally the desired starting unix timestamp
output is some kind of success message or something probably
"""

import sys 
import logging
import yaml
import time
import calendar
import dateutil.parser
from datetime import datetime
import pytz
import sqlite3
from bmsapp.readingdb import bmsdata
from bmsapp.calcs import calcreadings, calcfuncs01, auroravision
import bmsapp.models

from selenium.common.exceptions import ElementNotVisibleException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import TimeoutException


#from selenium.webdriver.common.by import By
#from selenium.webdriver.support.ui import WebDriverWait
#import selenium.webdriver.support.expected_conditions as EC


wait_time = 4.5
default_tz = 'US/Alaska'

URL_SYSTEM = 'https://easyview.auroravision.net/easyview/index.html?entityId=%s'


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

    br = auroravision.open_browser()

    try:
        br.implicitly_wait(30)      # don't timeout for at least 30 seconds

        # make sure window size is large enough.  Some apps display differently
        # for small window sizes, so make sure this is desktop size.
        br.set_window_size(1920, 1200)

        # go to the base page for the this plant
        br.get(URL_SYSTEM % system_params['plant_id'])
        print URL_SYSTEM % system_params['plant_id']
        time.sleep(wait_time)

        #check if timezone plant_tz is in system_params
        if 'plant_tz' in system_params:
            plant_tz = system_params['plant_tz']
        else:
            #if it is not then use defualt
            plant_tz = default_tz

        tz = pytz.timezone(plant_tz)

        #The time the enphase system came online is obtained if start_time isn't passed.
        #The summary request has the relevant info under 'operational_at' in unix time
        if start_time == None:
            start_time_str = auroravision.install_date(br)
            dt = dateutil.parser.parse(start_time_str)
            dt_aware = tz.localize(dt)

            start_time = calendar.timegm(dt_aware.utctimetuple())
        else:
            start_time = int(start_time)

        #print start_time
        # Get the initial slider position when it is to the far right
        time.sleep(wait_time)
        try:
            print 'try'
            sliding_pointer = br.find_element_by_class_name('pointer')
            print sliding_pointer.get_attribute('style')
            slide_end = int(sliding_pointer.get_attribute('style').split()[1].split('px;')[0])
        # if it doesn't work one time, then wait and try again
        except IndexError:
            print 'try again'
            time.sleep(wait_time)
            sliding_pointer = br.find_element_by_class_name('pointer')
            print sliding_pointer.get_attribute('style')
            slide_end = int(sliding_pointer.get_attribute('style').split()[1].split('px;')[0])

        #todays unix time (most recent midnight in timezone tz defined above)
        today_str = time.strftime('%Y-%m-%d')
        dt = dateutil.parser.parse(today_str)
        dt_aware = tz.localize(dt)
        today = calendar.timegm(dt_aware.utctimetuple())

        yesterday = today - 60*60*24
        #print type(yesterday)
        #print type(start_time)
 
        # go back to starting day
        start_str = datetime.fromtimestamp(float(start_time)).strftime('%Y-%m-%d')
        auroravision.go_back_to_date(br, start_str)
        time.sleep(wait_time)

        #cycle through all days from when the cycle became operational to yesterday
        #stop once start_time >= yesterday 
        #if today is used insteady it might be confused when it refreshes to today
        while start_time < yesterday:

            #query the currently selected day
            print "scraping data"
            try:
                t_array, v_array = auroravision.get_one_day(br, plant_tz, slide_end)
            except (StaleElementReferenceException, TimeoutException):
                #go back to the day it started on
                start_str = datetime.fromtimestamp(start_time).strftime('%Y-%m-%d')
                print "Stale element/Timeout - go back again"
                time.sleep(wait_time)
                try:
                    auroravision.go_back_to_date(br, start_str)
                except IndexError:
                    print "refreshing page"
                    br.get(URL_SYSTEM % system_params['plant_id'])
                    time.sleep(wait_time)
                    auroravision.go_back_to_date(br, start_str)
                continue
            except ElementNotVisibleException:
                print "an element is not visisble - trying again"
                continue
            except IndexError:
                print "Index error - trying again"
                continue

            # if the t_array is empty
            if not t_array:
                # go to next day and continue to next iteration
                print "empty day"

                # no time stamps to update start_time, so get date from date element
                try:
                    empty_date = br.find_element_by_class_name('range').text.split(' - ')[0]
                except (IndexError, StaleElementReferenceException):
                    print "no date found - refresh and go back to old start_str"
                    br.get(URL_SYSTEM % system_params['plant_id'])
                    time.sleep(wait_time)
                    auroravision.go_back_to_date(br, start_str)
                    continue
               
                dt = dateutil.parser.parse(empty_date)
                dt_aware = tz.localize(dt)

                if today == calendar.timegm(dt_aware.utctimetuple()):
                    print"Date range from today - go back again"
                    time.sleep(wait_time)
                    auroravision.go_back_to_date(br, start_str)
                else:
                    start_time = calendar.timegm(dt_aware.utctimetuple()) + 24*60*60
                    br.find_element_by_class_name('next').click()
                continue

            elif t_array[-1] > today:
                #go back to the day it started on
                start_str = datetime.fromtimestamp(start_time).strftime('%Y-%m-%d')
                print "Timestamp from today - go back again"
                time.sleep(wait_time)
                auroravision.go_back_to_date(br, start_str)
                continue

            else:
                #otherwise update the start_time to midnight of current day
                start_time = t_array[0] + 24*60*60

            #zip values and timestamps into list of tuples
            recs = zip(t_array, len(t_array)*[calc_sensor[0].sensor_id], v_array)

            #cycle through values in recs and insert into database
            print "loading data"
            for ts, id, val in recs:
                reading_db.insert_reading(int(ts), str(id), float(val))

            ##if the last timestamp occured today
            #if t_array[-1] > today:
            #    #go back to the day it started on
            #    start_str = datetime.fromtimestamp(start_time).strftime('%Y-%m-%d')
            #    print "go back again"
            #    auroravision.go_back_to_date(br, start_str)
            #else:
            #    #otherwise go to next day 
            print "go forward one day"
            br.find_element_by_class_name('next').click()

    finally:
        print "quitting"
        br.quit()

        reading_db.close()
