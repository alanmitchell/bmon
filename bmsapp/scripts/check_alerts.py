'''Checks all alert conditions and notifies recipients as needed.  Should
be run with the django-extensions runscript facility:

    manage.py runscript check_alerts
'''
import logging
from django.conf import settings
from django.core.mail import send_mail
import requests

# Get the Pushover API key out of the settings file, setting it to None
# if it is not present in the file.
PUSHOVER_API_KEY = getattr(settings, 'BMSAPP_PUSHOVER_APP_TOKEN', None)

# The FROM email address
FROM_EMAIL = getattr(settings, 'DEFAULT_FROM_EMAIL', '')

def run():

    # make a logger object
    logger = logging.getLogger('bms.check_alerts')
    
    if False:

        # We need to protect against errors stopping alert processing.  If an 
        # error occurs, we need to log it and go on processing alerts.
        try:
            pass
        except:
            logger.exception('Logged Error Message goes here')

        # example for sending mail.  For one given alert, I think it is OK
        # to list all recipients for that alert in one email (including
        # email-to-SMS addresses).  That will allow recipients to see who is
        # getting notified.
        send_mail('Subject here', 'Here is the message.', FROM_EMAIL,
            ['to@example.com'])

        # example for sending alert to the Pushover service
        # see https://pushover.net/api
        url = 'https://api.pushover.net/1/messages.json'
        payload = {'token': 'an53xsLPX5GaV78Pv54UyaZ4bj9xB6',
            'user': 'u2o9nvQL5h6wG2ESyLvRqotUXuzB5o',
            'priority': '0',
            'title': 'Abnormal Sensor Reading',
            'message': 'Message goes here.'}
        r = requests.post(url, data=payload)

        # get the response, which is a JSON string looking like this typically:
        # u'{"status":1,"request":"8f8e4f0f8b68b129097346a2d9d68294"}'
        # log an error if the status is not good.
        resp = r.text
