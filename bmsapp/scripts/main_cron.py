'''This file is run by a CRON job every 5 minutes and dispatches the various
cron tasks.  It should be run using the django-extensions runscript facility:

    manage.py runscript main_cron

'''

from datetime import datetime
import time
import calc_readings
import daily_status
import backup_django_db
import backup_readingdb
import check_alerts
import run_periodic_scripts


def suppress_errors(func):
    '''Runs the function 'func' and suppresses all errors.
    '''
    try:
        return func()
    except:
        return None


def run():
    '''The function executed by runscript.
    '''

    # wait a few seconds so we are sure that we are inside the 5 minute
    # interval
    time.sleep(3)

    # current time
    now = datetime.now()

    # determine some time values that are needed for determining which
    # cron jobs to run.
    # day of the year, 1-366
    yr_day = now.timetuple().tm_yday
    # hour of the day, 0-23
    hr = now.hour
    # which 5 minute period within in the hour, 0-11
    hr_div = int(now.minute / 5)

    # run periodic scripts.  They all run on some multiple of five minutes.
    suppress_errors(run_periodic_scripts.run)

    # at 15 and 45 minute marks in hour (roughly), run the calculate readings
    # script
    if hr_div in (3, 9):
        suppress_errors(calc_readings.run)

    # Alert checking occurs on every pass.  Run it after the calculated readings
    # so fresh readings are available.
    suppress_errors(check_alerts.run)

    # run the daily status script 5 minutes after midnight each day
    if hr == 0 and hr_div == 1:
        suppress_errors(daily_status.run)

    # run the Django DB backup every day
    if hr == 2 and hr_div == 6:
        suppress_errors(backup_django_db.run)

    # run the sensor reading database backup every 3 days
    if (yr_day % 3) == 0 and hr == 2 and hr_div == 6:
        suppress_errors(backup_readingdb.run)
