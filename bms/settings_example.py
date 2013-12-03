###################################################
# Django settings for Remote Montitoring project. #
###################################################

#----------------- Settings Specific to the Monitoring App ----------------------

# The key needed to store sensor readings into the database.  
# Sensor reading URL is stored with URL 'stB[this store key]'.  This is a REQUIRED
# setting.  In the future, if this settings file is kept in public version control,
# use an Environment variable to store this key.
BMSAPP_STORE_KEY = 'PutStorageKeyHere'        # can use bmsapp.views.make_store_key() to create one.

# Store key used with old URL pattern
# BMSAPP_STORE_KEY_OLD = ''

# Text only title of this application.  Used as part of the HTML page title.
BMSAPP_TITLE_TEXT = 'ANTHC Remote Monitoring'

# Header that appears at the top of every page.  Can include HTML
# and is placed inside a <div> tag with an CSS ID of 'header'.
BMSAPP_HEADER = 'ANTHC Remote Monitoring'

# Footer that appears at the bottom of every page.  Can include HTML
BMSAPP_FOOTER = '''<img src="http://rm.anthc.webfactional.com/static/bmsapp/images/ahfc_logo.png" 
width="75" height="58" border="0" alt="AHFC Logo" style="vertical-align:middle">
&nbsp;&nbsp;Thanks to the Alaska Housing Finance Corporation for providing most
of the source code for this website.'''

# Information about the Navigation links that appear at the top of each web page.
#     First item in tuple is Text that will be shown for the link.
#     Second item is the name of the template that will be rendered to produce the page.
#          'reports' is a special name that will cause the main reports/charts page to be
#          rendered.  For other names in this position, there must be a corresponding 
#          [template name].html file present in the templates/bmsapp directory.  The custom
#          template cannot match any of the URLs listed in urls.py.
#     The third item (optional) is True if this item should be the default index page for
#         the application.
BMSAPP_NAV_LINKS = ( ('Map', 'map'),
                     ('Data Charts and Reports', 'reports', True),
                     ('Training Videos and Project Reports', 'training_anthc'),
                   )


#-------------- End of Settings Specific to the Monitoring App -------------------

# Name of this Django project.  Note that if you change this from bms, you will also
# have to change values in the manage.py, wsgi.py, and appache2/conf/httpd.conf files.
PROJ_NAME = 'bms'     

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ['.anthc.webfactional.com']

ADMINS = (
    ('Alan Mitchell', 'tabb99@gmail.com'),
)

# This is the name you gave to the Static application created to serve static Django media
STATIC_APP_NAME = 'django_static'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'xxxxxxxxxxxxxxxyyyyyyyyyyyyyyyyyzzzzzzzzzzaaabbbcc'

# ----------- Generally shouldn't need to change anything beyond here ------------

from os.path import dirname, join, realpath

PROJ_PATH = realpath(join(dirname(__file__), '..'))    # probably don't need the "realpath" function

DEBUG = True
TEMPLATE_DEBUG = DEBUG

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': join(PROJ_PATH, '%s.sqlite' % PROJ_NAME),                   # Or path to database file if using sqlite3.
        # The following settings are not used with sqlite3:
        'USER': '',
        'PASSWORD': '',
        'HOST': '',                      # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT': '',                      # Set to empty string for default.
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/Anchorage'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = join(PROJ_PATH, '..', '..', STATIC_APP_NAME)

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    join(PROJ_PATH, 'static'),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = '%s.urls' % PROJ_NAME

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = '%s.wsgi.application' % PROJ_NAME

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    join(PROJ_PATH, 'templates'),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    # 'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    'django.contrib.admindocs',
    'bmsapp',
)

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}
