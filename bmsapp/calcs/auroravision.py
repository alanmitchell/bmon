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
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import WebDriverException
from selenium.common.exceptions import TimeoutException

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
WEEK_ITEM = "//li[contains(@title, '7 Days')]"
MONTH_ITEM = "//li[contains(@title, '30 Days')]"
YEAR_ITEM = "//li[contains(@title, '12 Months')]"

# Xpath of balloon which contains timestamp and value
TIME_VALUE_ITEM = "//g[contains(@id, 'balloons')]"
#TIME_VALUE_ITEM = "//g[contains(text(), 'Generate Power')]"
#balloons

# Xpath of button to navigate to previous or next day
PREVIOUS_DURATION_ITEM = "//a[contains(@class, 'prev')]"
NEXT_DURATION_ITEM = "//a[contains(@class, 'next')]"

wait_time = 5

class textContent_to_be_present_in_element(object):
    """
    EC can only check element.text and element.get_attribute("value")
    This custum exception checks element.get_attribute("textContent)
    An expectation for checking if the given text is present in the element's
    locator, textContent
    """
    def __init__(self, locator, text_):
        self.locator = locator
        self.text = text_

    def __call__(self, driver):
        try:
            element_text = _find_element(driver,
                                         self.locator).get_attribute("textContent")
            if element_text:
                return self.text in element_text
            else:
                return False
        except StaleElementReferenceException:
                return False

def go_back_to_date(browser, date_str):
    '''
	Specify the browser to go back to date_str.
	Due auroravision.net automatically refreshing regularly, this script currently can only only go back about 10-11 years. It's likely you can go further back by messing with the delay functions (time.sleep()/WebDriverWait) 
    '''
    print browser.find_element_by_class_name('range').text
    #current_date = date

    #daterange_el = br.find_elements_by_class_name('enabled')
    #selected_dur = [el.get_attribute('duration') for el in daterange_el 
    #               if "selectedDuration" in el.get_attribute('class')]
    browser.find_element_by_xpath(YEAR_ITEM).click()
    time.sleep(3)
    range_min = browser.find_element_by_class_name('range').text.split(' - ')[0]
    range_max = browser.find_element_by_class_name('range').text.split(' - ')[1]

    if dateutil.parser.parse(date_str) < dateutil.parser.parse(range_min):
        date_range = back(browser, date_str)
        range_min = date_range.split(' - ')[0]
        range_max = date_range.split(' - ')[1]

    #else:
    if dateutil.parser.parse(range_min) <= dateutil.parser.parse(date_str):
        browser.find_element_by_xpath(MONTH_ITEM).click()
        time.sleep(3)
        date_range = back(browser, date_str)
        range_min = date_range.split(' - ')[0]
        range_max = date_range.split(' - ')[1]

    if dateutil.parser.parse(range_min) <= dateutil.parser.parse(date_str) < dateutil.parser.parse(range_max):
        browser.find_element_by_xpath(WEEK_ITEM).click()
        time.sleep(3)
        date_range = back(browser, date_str)
        range_min = date_range.split(' - ')[0]
        range_max = date_range.split(' - ')[1]

    if dateutil.parser.parse(range_min) <= dateutil.parser.parse(date_str) < dateutil.parser.parse(range_max):
        browser.find_element_by_xpath(ONE_DAY_ITEM).click()
        time.sleep(3)
        date_range = back(browser, date_str)
        range_min = date_range.split(' - ')[0]
        range_max = date_range.split(' - ')[1]


    if dateutil.parser.parse(range_max) == dateutil.parser.parse(date_str):
        browser.find_element_by_xpath(ONE_DAY_ITEM).click()
    else:
        print "Some thing fish is going on here..."
        #browser.find_element_by_xpath(ONE_DAY_ITEM).click()
        browser.refresh()
        time.sleep(3)
        go_back_to_date(browser, date_str)

    time.sleep(3)
    return browser.find_element_by_class_name('range').text

def back(browser, date_str):
    '''
	Keeps moving the date range in the specified broswer back until date_str is within the date range. 
	The date_str must be in the appropriate formate (e.g. Jan 01, 3015)
    '''
    # get the oldest/smallest date in the date range box
    range_min_max = browser.find_element_by_class_name('range').text
    range_min = range_min_max.split(' - ')[0]

    # while date_str is older/smaller 
    #while time.strptime(date_str, '%b %d, %Y') < time.strptime(range_min, '%b %d, %Y'):
    while dateutil.parser.parse(date_str) < dateutil.parser.parse(range_min):
        # Go back one duration
        browser.find_element_by_xpath(PREVIOUS_DURATION_ITEM).click()
        # Wait a moment
        time.sleep(3)
        # get the new oldest/smallest date in the date range box
        range_min_max = browser.find_element_by_class_name('range').text
        range_min = range_min_max.split(' - ')[0]
        print range_min_max

    return range_min_max

def install_date(browser):
    '''
	Returns the install date string for the auroravision plant in the browser.
	The install date in contained in an element with a class=v, however there are several elements with such a class. The desired element is a sibling element to the only element with a class="lbl". The code find the "lbl" element by class name, then finds the parent element by xpath ('..'), then the desired "v" element by class name. 
    '''
   
    el = browser.find_element_by_class_name('lbl').find_element_by_xpath('..').find_element_by_class_name('v')
    #print 'got item elements'

    return el.text

def open_browser():
    '''This function open a phantom js browser and returns the browser element
    '''
    # Start the PhantomJS driver.  Assume the PhantomJS executable is in the same
    # folder as this file.
    # Name of Linux executable.
    phantom_path = os.path.join(os.path.dirname(__file__), "phantomjs")
    #phantom_path = "/usr/lib/phantomjs"
    if not os.path.exists(phantom_path):
      # Windows executable ends in '.exe'
      phantom_path = os.path.join(os.path.dirname(__file__), "phantomjs.exe")

    serv_args = ['--ignore-ssl-errors=true', '--ssl-protocol=TLSv1']

    return webdriver.PhantomJS(executable_path=phantom_path, service_args=serv_args)
    #return webdriver.Firefox()
    
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
#    # Start the PhantomJS driver.  Assume the PhantomJS executable is in the same
#    # folder as this file.
#    # Name of Linux executable.
#    phantom_path = os.path.join(os.path.dirname(__file__), "phantomjs")
#    #phantom_path = "/usr/lib/phantomjs"
#    if not os.path.exists(phantom_path):
#      # Windows executable ends in '.exe'
#      phantom_path = os.path.join(os.path.dirname(__file__), "phantomjs.exe")
#    serv_args = ['--ignore-ssl-errors=true', '--ssl-protocol=TLSv1']

    br = open_browser()
    #br = webdriver.Firefox()
    
    try:
        br.implicitly_wait(30)      # don't timeout for at least 30 seconds

        # make sure window size is large enough.  Some apps display differently
        # for small window sizes, so make sure this is desktop size.
        br.set_window_size(1920, 1200)

        # go to the base page for the this plant
        br.get(URL_SYSTEM % plant_id)
        time.sleep(5)

        # when the page first loads the pointer is on the right
        WebDriverWait(br, wait_time).until(EC.element_to_be_clickable((By.CLASS_NAME, 'pointer')))
        sliding_pointer = br.find_element_by_class_name('pointer')
        slide_end = int(sliding_pointer.get_attribute('style').split()[1].split('px;')[0])

        # get data for current day
        #print 'today'
        try:
            ts_cur, val_cur = get_one_day(br, plant_tz, slide_end)
        except IndexError as e:
            print e
            ts_cur = []
            val_cur = []

        # go back one day and get data 
        #print 'yesterday'
        br.find_element_by_xpath(PREVIOUS_DURATION_ITEM).click()
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
    try:
      WebDriverWait(br, wait_time).until(EC.element_to_be_clickable((By.CLASS_NAME, 'pointer')))
    except TimeoutException as e:
      print e
      return [],[]

    # Get current date
    current_date = br.find_element_by_class_name('range').text
    
    # if the date string is over multiple days
    if current_date.split(' - ')[0] != current_date.split(' - ')[1]:
        # select the single day display and wait
        br.find_element_by_xpath(ONE_DAY_ITEM).click()
        WebDriverWait(br, wait_time).until(EC.element_to_be_clickable((By.XPATH, PLAY_BUTTON_ITEM)))
        WebDriverWait(br, wait_time).until(EC.element_to_be_clickable((By.CLASS_NAME, 'pointer')))

    # Parse date
    current_date = br.find_element_by_class_name('range').text.split(' - ')[0]
    print current_date

    WebDriverWait(br, wait_time).until(EC.element_to_be_clickable((By.XPATH, PLAY_BUTTON_ITEM)))

#    br.save_screenshot(os.path.join(os.path.dirname(__file__), "auroraA.png")

    # get pointer element
    sliding_pointer = br.find_element_by_class_name('pointer')
    #print sliding_pointer.get_attribute('style')

    # move slider to ensure balloon element is active
    ActionChains(br).drag_and_drop_by_offset(sliding_pointer, slide_end, 0).perform()
    time.sleep(1)
    sliding_pointer.get_attribute('style')
    #WebDriverWait(br, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, 'pointer')))

#    br.save_screenshot(os.path.join(os.path.dirname(__file__), "auroraB.png")
    ActionChains(br).drag_and_drop_by_offset(sliding_pointer, -slide_end, 0).perform()
    #WebDriverWait(br, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, 'pointer')))
    time.sleep(1)
    #print sliding_pointer.get_attribute('style')
    #time.sleep(1)

#    br.save_screenshot(os.path.join(os.path.dirname(__file__), "auroraC.png")
    # get balloon element
    try:
        balloon = br.find_element_by_id('balloons')
    except NoSuchElementException:
      print "no balloon" 
      return [],[]
    #print balloon.text
    #print balloon.get_attribute('textContent')
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
        balloon_text = balloon.get_attribute('textContent')
        #print balloon_text

        # parse into time and value text strings
        try:
            timestamp.append(balloon_text.split()[-4])
            value.append(balloon_text.split()[-2])
        except IndexError:
            pass

        # wait in 0.1 s increments until balloon text changes or 10 s
        WebDriverWait(br, wait_time, 0.1).until_not(textContent_to_be_present_in_element((By.ID, 'balloons'), balloon_text))

    # get text from ballon for final point
    balloon_text = balloon.get_attribute('textContent')
    #balloon_text = balloon.text
    #print balloon.text.split('\n')[0]

    # parse final point into time and value text strings
    try:
        timestamp.append(balloon_text.split()[-4])
        value.append(balloon_text.split()[-2])
    except IndexError:
        pass

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

def _find_element(driver, by):
    """Looks up an element. Logs and re-raises ``WebDriverException``
    if thrown."""
    try :
        return driver.find_element(*by)
    except NoSuchElementException as e:
        raise e
    except WebDriverException as e:
        raise e

if __name__ == '__main__':

    print 'Kobuk Water Plant'
    print get_data('1896045')

    print 'Deering Water Plant'
    print get_data('1896044')

    print 'Noatak'
    print get_data('1896043')
