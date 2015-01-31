'''
This file sets up logging.
'''
from os.path import dirname, join, realpath
import logging, logging.handlers

APP_PATH = realpath(dirname(__file__))

# Log file for the application
LOG_FILE = join(APP_PATH, 'logs', 'bms.log')

# *** This controls what messages will actually get logged
# Levels in order from least to greatest severity are:  DEBUG, INFO, WARNING, ERROR, CRITICAL
# Methods to call that automatically set appropriate level are: debug(), info(), warning(), error(),
# exception(), and critical().  If 'exception()' is called, an exception traceback is automatically
# added to the log message (only call from within an exception handler).
LOG_LEVEL = logging.INFO

# ----

# create base logger for the application.  Any other loggers named 'bms.XXXX'
# will inherit these settings.
logger = logging.getLogger('bms')

# set the log level
logger.setLevel(LOG_LEVEL)

# create a rotating file handler
fh = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes=200000, backupCount=5)

# create formatter and add it to the handler
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)

# add the handler to the logger
logger.addHandler(fh)
