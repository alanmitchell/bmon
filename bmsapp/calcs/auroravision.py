'''Module to read PV power production values from the auroravision, the web site
storing and presenting PV production from ABB inverters.
'''

import os
import time
import calendar

import dateutil.parser
import pytz

# Imports from the selenium package
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import selenium.webdriver.support.expected_conditions as EC

# Constants relevant to the Aurora Vision

# This is the URL for the main page for a particular plant. The %s interpolation
# slot is where the Plant ID is inserted.
URL_SYSTEM = 'https://easyview.auroravision.net/easyview/index.html?entityId=%s'

# This is the Xpath needed to find the play button which displays the data for 
# one day
PLAY_BUTTON_ITEM = "//div[contains(@class, 'playButton')]"

# Xpath needed to find the currently displayed date range
DATE_RANGE_ITEM = "//div[contains(@class, 'range')]"
ONE_DAY_ITEM = "//li[contains(@title, '1 Day')]"

# Xpath of balloon which contains timestamp and value
TIME_VALUE_ITEM = "//g[contains(@id, 'balloons')]"
#TIME_VALUE_ITEM = "//g[contains(text(), 'Generate Power')]"
#balloons

# Xpath of button to navigate to previous or next day
PREVIOUS_DAY_ITEM = "//a[contains(@class, 'prev')]"
NEXT_DAY_ITEM = "//a[contains(@class, 'next')]"



def get_data(plant_id,
             plant_tz='US/Alaska'):
    '''Retrieves detailed time-resolution power production data from a ABB Aurora Vision site.

    Parameters
    ----------
    'plant_id': the Aurora Vision ID of the plant to retrieve.
    'plant_tz': the Olson timezone database string identifying the timezone
        that is used for the plant on the Sunny Portal.

    Return Value
    ------------
    Data from the current day and the day prior are returned.  The return
    value from this function is a two-tuple: a list of Unix Epoch
    timestamps and a list of Power Production values in kW.
    '''
    # Start the PhantomJS driver.  Assume the PhantomJS executable is in the same
    # folder as this file.
    # Name of Linux executable.
    phantom_path = os.path.join(os.path.dirname(__file__), "phantomjs")
    #phantom_path = "/usr/lib/phantomjs"
    if not os.path.exists(phantom_path):
      # Windows executable ends in '.exe'
      phantom_path = os.path.join(os.path.dirname(__file__), "phantomjs.exe")
    br = webdriver.PhantomJS(executable_path=phantom_path)
    #br = webdriver.Firefox()
    
    try:
        br.implicitly_wait(30)      # don't timeout for at least 30 seconds

        # make sure window size is large enough.  Some apps display differently
        # for small window sizes, so make sure this is desktop size.
        br.set_window_size(1920, 1200)

        # go to the base page for the this plant
        br.get(URL_SYSTEM % plant_id)

        # when the page first loads the pointer is on the right
        WebDriverWait(br, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, 'pointer')))
        sliding_pointer = br.find_element_by_class_name('pointer')
        slide_end = int(sliding_pointer.get_attribute('style').split()[1].split('px;')[0])

        # get data for current day
        #print 'today'
        ts_cur, val_cur = get_one_day(br, plant_tz, slide_end)


        # go back one day and get data 
        #print 'yesterday'
        br.find_element_by_xpath(PREVIOUS_DAY_ITEM).click()
        ts_prior, val_prior = get_one_day(br, plant_tz, slide_end)

    finally:
        # close the browser
        br.quit()

    return ts_prior + ts_cur, val_prior + val_cur


def get_one_day(br, plant_tz, slide_end):
    '''This function retrieves data for the currently selected day.

    Parameters
    ----------
    For documentation of most parameters, see documentation of the "get_data"
    function.

    'broswer' is the Selenium web browser object; it is assumed that the browswer object just loaded the main page for the target PV plant.
    'slide_end' is the pixel value where the slider is expected to end.

    Return Value
    ------------
    The return value from this function is a two-tuple: a list of Unix Epoch
    timestamps and a list of Power Production values in kW.
    '''

    # Make sure appropriate window is selected
    br.switch_to_window(br.window_handles[0])
    WebDriverWait(br, 5).until(EC.element_to_be_clickable((By.CLASS_NAME, 'pointer')))
    
    # Get current date
    current_date = br.find_element_by_class_name('range').text
    
    # if the date string is over multiple days
    if current_date.split(' - ')[0] != current_date.split(' - ')[1]:
        # select the single day display and wait
        br.find_element_by_xpath(ONE_DAY_ITEM).click()
        WebDriverWait(br, 5).until(EC.element_to_be_clickable((By.XPATH, PLAY_BUTTON_ITEM)))
        WebDriverWait(br, 5).until(EC.element_to_be_clickable((By.CLASS_NAME, 'pointer')))

    # Parse date
    current_date = br.find_element_by_class_name('range').text.split(' - ')[0]
    #print current_date

    WebDriverWait(br, 5).until(EC.element_to_be_clickable((By.XPATH, PLAY_BUTTON_ITEM)))

    # get pointer element
    sliding_pointer = br.find_element_by_class_name('pointer')
    #print sliding_pointer.get_attribute('style')

    # move slider to ensure balloon element is active
    ActionChains(br).drag_and_drop_by_offset(sliding_pointer, slide_end, 0).perform()
    time.sleep(1)
    sliding_pointer.get_attribute('style')
    #WebDriverWait(br, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, 'pointer')))

    ActionChains(br).drag_and_drop_by_offset(sliding_pointer, -slide_end, 0).perform()
    #WebDriverWait(br, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, 'pointer')))
    time.sleep(1)
    #print sliding_pointer.get_attribute('style')

    # get balloon element
    balloon = br.find_element_by_id('balloons')
    #print balloon.text.split('\n')[0]
    #print balloon.text.split('\n')[1].split()[-2]

    #initialize timestamp and value variables
    timestamp = []
    value = []

    # start cycling through measurements for current day by pressing play button
    br.find_element_by_xpath(PLAY_BUTTON_ITEM).click()

    # while the slider has not reached the end
    while int(sliding_pointer.get_attribute('style').split()[1].split('px;')[0]) < slide_end:
        # get text from ballon
        balloon_text = balloon.text
        #print balloon.text.split('\n')[0]

        # parse into time and value text strings
        timestamp.append(balloon_text.split('\n')[0])
        value.append(balloon_text.split('\n')[1].split()[-2])

        # wait in 0.1 s increments until balloon text changes or 10 s
        WebDriverWait(br, 10, 0.1).until_not(EC.text_to_be_present_in_element((By.ID, 'balloons'), balloon_text))

    # get text from ballon for final point
    balloon_text = balloon.text
    #print balloon.text.split('\n')[0]

    # parse final point into time and value text strings
    timestamp.append(balloon_text.split('\n')[0])
    value.append(balloon_text.split('\n')[1].split()[-2])

    # convert the timestamps to Unix Epoch values.
    tz = pytz.timezone(plant_tz)
    timestamp = [current_date + ' ' + ts for ts in timestamp]
    timestamp_unix = []
    for ts in timestamp:
        dt = dateutil.parser.parse(ts)
        dt_aware = tz.localize(dt)
        timestamp_unix.append(calendar.timegm(dt_aware.utctimetuple()))

    # remove commas from value and convert to float
    value = [float(val.replace(',',''))/1000 for val in value]

    return timestamp_unix, value

if __name__ == '__main__':

    print 'Kobuk Water Plant'
    print get_data('1896045')

    print 'Deering Water Plant'
    print get_data('1896044')

    print 'Noatak'
    print get_data('1896043')
