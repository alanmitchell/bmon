"""This module contains a function 'process_mail' that will process attached
files to an email that was routed to the calling script via 
Webfaction's mail2script.  The processing extracts sensor data
from the attachments and stores it in the BMON sensor reading
database.
"""
import os
import sys
import email
from io import BytesIO
import re
import logging
import django

# need to add the directory two above this to the Python path
# so the bmsapp package can be found
this_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.abspath(os.path.join(this_dir, '../../'))
sys.path.insert(0, app_dir)

# prep the Django environment because we need access to the module
# that manipulates the Reading database.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bmon.settings")
django.setup()

# Now import the BMON Reading database module
from bmsapp.readingdb.bmsdata import BMSdata

# Make a logger for this module.  I'm doing this after the
# above import because logging is set up when the bmsapp
# package is accessed.  These logger messages will now appear
# in the standard BMON log file.
_logger = logging.getLogger('bms.' + os.path.basename(__file__))

def process_email(file_pattern, read_function, tz='US/Alaska'):
    """Reads an email present on sys.stdin and processes all email 
    attachments that have a file name matching the 
    regex pattern 'file_pattern' (case insensitve).  'tz' is the name 
    of an Olson database timezone and indicates the timezone of the 
    data found in the attached files.
    'read_function' is a function that extracts sensor data from 
    the file.  'read_function' must accept the following parameters 
    in this order:

        file_object: a BytesIO file-like object that contains 
            the file contents.
        filename: the name of the file as a string
        tz: the name of an Olson database timezone, that tells 
            the function the timezone that dates in the file are 
            associated with.
    """

    # access the Reading database
    db = BMSdata()

    try:

        # the email comes from stdin; read it into a Message object
        msg = email.message_from_file(sys.stdin)

        # Find all the attachments that match the file pattern.
        for part in msg.walk():
            fname = part.get_filename()
            if (fname is not None) and (re.match(file_pattern, fname, re.I) is not None):
                try:
                    attachment = part.get_payload(decode=True)
                    stamps, ids, vals = read_function(BytesIO(attachment), fname, tz)

                    insert_msg = db.insert_reading(stamps, ids, vals)
                    _logger.info('Data processed from %s:\n    %s' % (fname, insert_msg))

                except Exception as e:
                    _logger.exception('Error processing data from file %s with %s.' % (fname, read_function.__name__))

    except Exception as e:
        _logger.exception('Error processing data with %s.' % read_function.__name__)

    finally:
        db.close()
