﻿##################################################
# Django settings file template for BMON project #
##################################################
# This template is used by the Github bmon-install project to create a 
# settings.py file for BMON. See: https://github.com/alanmitchell/bmon-install.

import logging

# ----------------- Settings Specific to the Monitoring App ----------------------

# The key needed to store sensor readings into the database.
# This is a REQUIRED setting.  You can have multiple valid storage keys
# by listing them in a tuple or list:  ('key1', 'key2') or ['key1', 'key2'].
# You can load https://bms.ahfc.us/make-store-key/ in a browser to generate
# a suitable random store key.  Any sensors that post data to this site will
# need to include thise Store Key when they post the data.
# See bmsapp/views.storereading() and bmsapp/views.storereadings() for details
# of how the Store Key is included in a reading post.
BMSAPP_STORE_KEY = '{{ store_key.stdout }}'

# Store key used with old URL pattern.
# *** NOT USED WITH NEW INSTALLS.  LEAVE COMMENTED OUT ***
# BMSAPP_STORE_KEY_OLD = ''

# Text only title of this application.  Used as part of the HTML page title.
BMSAPP_TITLE_TEXT = '{{ bmon_site_title }}'

# Header that appears at the top of every page.  Can include HTML
# and is placed inside a <div> tag with an CSS ID of 'header'.
BMSAPP_HEADER = '{{ bmon_site_title }}'

# The following email settings need to be filled out for sending out email alerts from
# the BMON app.
# For an article on using Gmail settings:   https://data-flair.training/blogs/django-send-email/
# For general Django documentation on these settings, see:
# https://docs.djangoproject.com/en/2.2/ref/settings/#std:setting-EMAIL_HOST

# the SMTP server used to send mail, 'smtp.webfaction.com' or the Webfaction hosting service
EMAIL_USE_TLS = True
EMAIL_HOST = '{{ email_smtp_host }}'
EMAIL_PORT = 587
EMAIL_HOST_USER = '{{ email_username }}'
EMAIL_HOST_PASSWORD = '{{ email_password }}'
# this will be the FROM for alert messages
DEFAULT_FROM_EMAIL = '{{ email_username }}'
# this is the FROM for error messages
SERVER_EMAIL = '{{ email_username }}'

# A Twilio Account with a Messaging Service must be set up to allow for SMS Text
# Alerts to be sent by BMON. Below is the needed information from the account:
TWILIO_ACCOUNT_SID = '{{ twilio_account_sid }}'
TWILIO_AUTH_TOKEN = '{{ twilio_auth_token }}'
TWILIO_MSG_SERVICE_SID = '{{ twilio_msg_service_sid }}'   

# The following fields are used to populate the Privacy Policy and Terms & Conditions page.
TERMS_COMPANY_NAME = '{{ terms_company_name }}'
TERMS_ADDRESS_1 = '{{ terms_address_1 }}'
TERMS_ADDRESS_2 = '{{ terms_address_2 }}'
TERMS_ADDRESS_3 = '{{ terms_address_3 }}'
TERMS_EMAIL = '{{ terms_email }}'
TERMS_BMON_URL = '{{ terms_bmon_url }}'
TERMS_LEGAL_JURISDICTION = '{{ terms_legal_jurisdiction }}'

# Information about the Navigation links that appear at the top of each web page.
#     First item in tuple is Text that will be shown for the link.
#     Second item is the name of the template that will be rendered to produce the page.
#          'reports' is a special name that will cause the main reports/charts page to be
#          rendered. 'custom-reports' is also special and will cause a page showing the
#          available custom reports. For other names in this position, there must be a corresponding
#          [template name].html file present in the templates/bmsapp directory.  The custom
#          template cannot match any of the URLs listed in urls.py.
#     The third item (optional) is True if this item should be the default index page for
#         the application.
BMSAPP_NAV_LINKS = (('Map', 'map'),
                    ('Graphs', 'reports', True),
                    ('Energy Reports', 'energy-reports'),
                    ('Custom Reports', 'custom-reports'),
                    ('Training', 'training-ahfc'),
                    ('Sys Admin', 'admin-reports'),
                    )

# The number of hours before a sensor is considered to be inactive (not posting data).
BMSAPP_SENSOR_INACTIVITY = 2.0   # Hours

# This is the base URL where BMON Essential Energy Reports are located.
# If Energy Reports are not being geneerated for this system, assign  None
# to this variable.
# ENERGY_REPORTS_URL = 'https://bmonreporter-data.energytools.com/reports/bms.ahfc.us/'
ENERGY_REPORTS_URL = None

# If you are using the Pushover notification service for alerts generated by the BMON
# application, you need to register an Application with Pushover and enter the API
# Token/Key below.  It is a 30 character string.  See 'https://pushover.net'.
# Use of Pushover notifications is not required, as both email and SMS text message
# notification options are available as well.
BMSAPP_PUSHOVER_APP_TOKEN = '123456789012345678901234567890'

# This controls what messages will actually get logged
# Levels in order from least to greatest severity are:  DEBUG, INFO, WARNING, ERROR, CRITICAL
BMSAPP_LOG_LEVEL = logging.INFO

# Put a Mesonet API Token here, if you are acquiring temperature or wind data
# using the Mesonet API (getAllMesonetTemperature, getAllMesonetWindSpeed).
# See https://developers.synopticdata.com/signup to obtain a token.
BMSAPP_MESONET_API_TOKEN = ''

# Weather Underground API is no longer supported due to changes in their service
# See http://www.wunderground.com/weather/api for details
# BMSAPP_WU_API_KEY = ''

# Enter URL, Username and Password for the ARIS api here if you are using the
# getUsageFromARIS calculation function to import building energy usage info
BMSAPP_ARIS_URL = 'https://arisapi.ahfc.us'
BMSAPP_ARIS_USERNAME = 'buildingmonitoringapp'
BMSAPP_ARIS_PASSWORD = ''

# If you are using the "ecobee" periodic script to gather data from Ecobee thermostats
# you need to supply an Ecobee API Key, available from the Ecobee Developer site.
BMSAPP_ECOBEE_API_KEY = '32 Character API Key goes here'

# The settings in the following section need to be filled out. These
# are settings required for the general Django software.

# Hosts/domain names that are valid for this site; required if DEBUG is False.
# More documentation at: https://docs.djangoproject.com/en/1.7/ref/settings/#allowed-hosts
ALLOWED_HOSTS = [
    '{{ bmon_domain }}',
    'www.{{ bmon_domain }}',
    '{{ server_ip.stdout }}',
    'localhost',
]

# This is the Django Secret Key, needed for security purposes.
# Make this unique, and don't share it with anybody.
# See documentation at https://docs.djangoproject.com/en/1.7/ref/settings/#std:setting-SECRET_KEY
SECRET_KEY = '{{ django_secret_key.stdout }}'

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/Anchorage'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

# The Names and Emails of people who should be emailed in the case of an
# application exception.  Everyone appearing in the list will be notified; add
# additional tuples for each Admin.  Unlike the sample below, remove the # symbol
# in front of each tuple.
# See documentation at https://docs.djangoproject.com/en/1.7/ref/settings/#std:setting-ADMINS
# NOTE:  You can also view the error log for the BMON application by browsing to the page:
#     <application URL>/show-log
ADMINS = (
    ('{{ admin_email_name }}', '{{ admin_email_address }}'),
)

# If DEBUG=True, a detailed error traceback is displayed in the browser when an error
# occurs.  This setting should be False for production use for security reasons, but if
# errors are occurring with use of the application, setting to True provides valuable
# debug information.
DEBUG = False

# Import settings that are generally common to all installs of BMON.
from .settings_common import *

# ----- If you need to override any of the settings in the 'settings_common.py' file
# ----- do so below this point in this file.
