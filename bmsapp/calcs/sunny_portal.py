'''Module to read PV power production values from the Sunny Portal, the web site
storing and presenting PV production from Sunny Boy inverters.
'''

import os
import time
import calendar

import pandas as pd   # only used to parse out data from HTML table

import dateutil.parser
import pytz

# Imports from the selenium package
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import selenium.webdriver.support.expected_conditions as EC

# Constants relevant to the Sunny Portal

# This is the URL for the main page for a particular plant. The %s interpolation
# slot is where the Plant ID is inserted.
URL_SYSTEM = 'https://www.sunnyportal.com/Templates/PublicPageOverview.aspx?plant=%s&splang=en-US'

# This is the Xpath needed to find the "Energy and Power" menu item in the
# left Navigation bar
POWER_MENU_ITEM = "//a[contains(@id, 'NavigationLeftMenuControl') and contains(@title, '%s')]"

# Xpath templates for finding images and inputs by ID substring
IMG_XPATH = "//img[contains(@id, '%s')]"
INPUT_XPATH = "//input[contains(@id, '%s')]"


def get_data(plant_id,
             plant_tz='US/Alaska',
             menu_text='Energy and Power',
             fill_NA=False,
             graph_num=None):
    '''Retrieves detailed time-resolution power production data from a Sunny
    Portal plant.

    Parameters
    ----------
    'plant_id': the Sunny Portal ID of the plant to retrieve.
    'plant_tz': the Olson timezone database string identifying the timezone
        that is used for the plant on the Sunny Portal.
    'menu_text': text that occurs in the title attribute of the menu item in
        the left navigation bar; this menu item should bring up the desired
        Power graph.
    'fill_NA': If fill_NA is False (the default), Power values that are blank
        are not posted, because these are time slots that have not occurred yet.
        But, for some systems, the Power value is left blank when the power
        production is 0.  Setting fill_NA to True will cause these blank power
        values to be changed to 0 and posted.
    'graph_num': On the page containing the desired Power graph, sometimes multiple
        graphs will appear.  If so, this parameter needs to be set to 0 to use
        the first graph on the page, 1 for the second, etc.  If there is only one
        graph on the page, this parameter must be set to None.

    Return Value
    ------------
    Data from the current day and the day prior are returned.  The return
    value from this function is a two-tuple: a list of Unix Epoch
    timestamps and a list of Power Production values in kW.
    '''
    # Start the PhantomJS driver.  Assume the PhantomJS executable is in the same
    # folder as this file.
    #br = webdriver.Firefox()
    br = webdriver.PhantomJS(executable_path=os.path.join(os.path.dirname(__file__), "phantomjs.exe"))

    try:
        br.implicitly_wait(30)      # don't timeout for at least 30 seconds

        # make sure window size is large enough.  Some apps display differently
        # for small window sizes, so make sure this is desktop size.
        br.set_window_size(1920, 1200)

        # go to the base page for the this plant
        br.get(URL_SYSTEM % plant_id)

        # get data for current day
        ts_cur, val_cur = get_one_day(br, plant_tz, menu_text,
                                      fill_NA, graph_num, go_back_one_day=False)

        # get data for previous data
        ts_prior, val_prior = get_one_day(br, plant_tz, menu_text,
                                          fill_NA, graph_num, go_back_one_day=True)

    finally:
        # close the browser
        br.quit()

    return ts_prior + ts_cur, val_prior + val_cur


def get_one_day(browser, plant_tz, menu_text, fill_NA, graph_num, go_back_one_day=False):
    '''This function retrieves high-resolution data for the current day
    or the pevious day depending the 'go_back_one_day' parameter.

    Parameters
    ----------
    For documentation of most parameters, see documentation of the "get_data"
    function.

    'broswer' is the Selenium web browser object; it is assumed that the browswer object
        just loaded the main page for the target PV plant.
    'go_back_one_day': If True, the prior days readings are returned instead of the
        current day's readings.

    Return Value
    ------------
    The return value from this function is a two-tuple: a list of Unix Epoch
    timestamps and a list of Power Production values in kW.
    '''

    # Find and Click the proper menu item
    browser.switch_to_window(browser.window_handles[0])
    browser.find_element_by_xpath(POWER_MENU_ITEM % menu_text).click()

    # Make control ID substrings to search for, depending on whether there are
    # multiple graphs on the page
    if graph_num is not None:
        day_prior_id = 'UserControl%s_btn_prev' % graph_num
        date_id = 'UserControl%s__datePicker' % graph_num
        cog_id = 'UserControl%s_OpenButtonsDivImg' % graph_num
        detail_id = 'UserControl%s_ImageButtonValues' % graph_num
    else:
        day_prior_id = 'btn_prev'
        date_id = 'datePicker'
        cog_id = 'OpenButtonsDivImg'
        detail_id = 'ImageButtonValues'

    if go_back_one_day:
        browser.find_element_by_xpath(INPUT_XPATH % day_prior_id).click()
        # need a delay here, otherwise the next find element statement will find
        # the *old* datePicker text box.
        time.sleep(5)

    # Read out the day the data applies to
    the_day = browser.find_element_by_xpath(INPUT_XPATH % date_id).get_attribute("value")

    # Hover over the cog icon in the lower right of the graph
    element = browser.find_element_by_xpath(IMG_XPATH % cog_id)
    hov = ActionChains(browser).move_to_element(element)
    hov.perform()

    # Need to wait for the "Details" icon to show before clicking it.
    detail_object = WebDriverWait(browser, 7).until(EC.element_to_be_clickable((By.XPATH, INPUT_XPATH % detail_id)))
    detail_object.click()

    # Switch to the Details window that popped up and get the HTML
    # from it.
    browser.switch_to_window(browser.window_handles[1])
    WebDriverWait(browser, 30).until(EC.presence_of_element_located((By.XPATH, "//table[contains(@id, 'Table1')]")))
    result_html = browser.page_source
    browser.close()

    # Have Pandas read the HTML and extract the data from the table within
    # it.  The first (and only) table contains the data we want.
    df = pd.read_html(result_html)[0]
    df.columns = ['Time', 'Power']

    # Convert Power values to numeric.  Handle rows that don't have power
    # values according to the fill_NA parameter.
    # that aren't present yet.
    df.Power = pd.to_numeric(df.Power, errors='coerce')
    if fill_NA:
        # drop first row as it contains no data
        df = df.drop(0)
        # fills NA Power values with 0.0
        df = df.fillna(0.0)
    else:
        # drops all rows with no kW data and the first garbage row.
        df = df.dropna()

    # get the time strings and create full date/time timestamps in a
    # numpy array.  Also create an array of kW values
    ts_strings = (the_day + ' ' + df.Time).values
    vals = df.Power.values

    # convert the timestamps to Unix Epoch values.
    tz = pytz.timezone(plant_tz)
    ts_unix = []
    for ts in ts_strings:
        dt = dateutil.parser.parse(ts)
        dt_aware = tz.localize(dt)
        ts_unix.append(calendar.timegm(dt_aware.utctimetuple()))

    # With the Sunny Portal, a Midnight value is reported at the end of the
    # day, but really should have a date for the next day.  Look for this
    # problem and correct it.
    if len(ts_unix) > 1:
        if ts_unix[-1] < ts_unix[-2]:
            ts_unix[-1] += 3600 * 24     # add a day to the point mislabeled

    # eliminate any entries past the current time.  This may happen if 'fill_NA'
    # is set to True.
    cur_ts = time.time()
    for i in range(len(ts_unix)):
        if ts_unix[i] >= cur_ts:
            ts_unix = ts_unix[:i]
            vals = vals[:i]
            break

    return list(ts_unix), list(vals)

if __name__ == '__main__':

    print 'Nortech'
    print get_data('d0c174be-ad46-4a43-bf72-af15d0cb93e6')

    print 'Anchorage Solar Building'
    print get_data('e89960d9-e25e-4cd0-90a0-8698de3e286b', fill_NA=True)

    print 'Alaska Aviation Museum'
    # Note that the menu text is case sensitive; default is "Power" and this system
    # has "power" in the menu item.
    print get_data('548529bf-aa2a-4eba-96c5-77aa2badb84c', menu_text='Energy and power', fill_NA=True, graph_num=0)
