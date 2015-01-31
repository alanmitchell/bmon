'''
This file sets up logging.
'''
from os.path import dirname, join, realpath
import logging, logging.handlers
from django.conf import settings

APP_PATH = realpath(dirname(__file__))

# Log file for the application
LOG_FILE = join(APP_PATH, 'logs', 'bms.log')

# create base logger for the application.  Any other loggers named 'bms.XXXX'
# will inherit these settings.
logger = logging.getLogger('bms')

# set the log level
logger.setLevel(getattr(settings, 'LOG_LEVEL', logging.INFO))

# create a rotating file handler
fh = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes=200000, backupCount=5)

# create formatter and add it to the handler
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)

# add the handler to the logger
logger.addHandler(fh)
