# ----- Settings for Lockdown  
# To use the Lockdown feature, include the following line at the end of the
# 'settings.py' file (without the beginning # character):
# from .settings_lockdown import *

from .settings_common import INSTALLED_APPS, MIDDLEWARE

INSTALLED_APPS += ('lockdown', ) 
MIDDLEWARE += ('lockdown.middleware.LockdownMiddleware',)

# Has the log-in form accept the standar User credentials for determining
# who has access
LOCKDOWN_FORM = 'lockdown.forms.AuthForm'

# Allows users who do not have Staff privileges (ability to add Sensors, Buildings,
# etc.) to view the site if this setting is set to False.
LOCKDOWN_AUTHFORM_STAFF_ONLY = False

# An alternative authorization method: user only has to enter one of
# passwords in the following tuple.  To use this, uncomment line below and
# comment out the "LOCKDOWN_FORM" line.
# LOCKDOWN_PASSWORDS = ('letmein', 'beta')

LOCKDOWN_URL_EXCEPTIONS = ( r'^/readingdb/reading/(\w+)/store/$',  # URL to store one reading into database
							r'^/readingdb/reading/store/$',        # URL to store multiple readings into database
							r'^/readingdb/reading/store-things/$', # URL to store readings from Things Network
							r'^/readingdb/reading/store-rb/$',     # Store Radio Bridge sensors
							r'^st8(\w+)/',                         # Old URL pattern for storing
						)
