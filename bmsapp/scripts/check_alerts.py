'''Checks all alert conditions and notifies recipients as needed.  Should
be run with the django-extensions runscript facility:

    manage.py runscript check_alerts
'''
import logging
import time
from bmsapp.models import AlertCondition
from bmsapp.readingdb.bmsdata import BMSdata


def run():
    '''Checks all Alert conditions and notifies Alert recipients for those
    conditions that are true.
    Returns the number alerts where the alert condition is true.
    '''

    # make a logger object
    logger = logging.getLogger('bms.check_alerts')

    # get a sensor reading database object
    reading_db = BMSdata()

    total_true_alerts = 0
    
    for condx in AlertCondition.objects.all():

        try:
            subject_msg = condx.check_condition(reading_db)
            if subject_msg:
                total_true_alerts += 1
                subject, msg = subject_msg
                msg_count = 0  # tracks # of successful messages sent
                for recip in condx.recipients.all():
                    try:
                        msg_count += recip.notify(subject, msg, condx.priority)
                    except:
                        logger.exception('Error notifying recipient %s of an alert.' % recip)
                if msg_count:
                    # at least one message was sent so update the field tracking the timestamp
                    # of the last notification for this condition.
                    condx.last_notified = time.time()

        except:
            logger.exception('Error processing alert %s')

    return total_true_alerts
