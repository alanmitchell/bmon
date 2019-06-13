#!/usr/local/bin/python3.7
'''Upgrades the Alert Condition objects from the Python 2.7
version to BMON to the Python 3.7 version (which uses Bootstrap 4).
The upgrade relates to a change in the name of the drop-down control
that selects mutliple sensors.
'''
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bmon.settings")
django.setup()

from bmsapp.models import AlertCondition

ct = 0
for cx in AlertCondition.objects.all():
    msg = cx.alert_message
    if 'select_chart=2' in msg:
        msg_new = msg.replace('select_sensor=', 'select_sensor_multi=')
        cx.alert_message = msg_new
        cx.save()
        print(cx.alert_message)
        ct += 1

print(ct)
