#!/usr/bin/env python3
'''Adds buildings, sensors, and Dashboard items associated with a number of
LT22222-L boat sensors.  The Dev EUI values are passed in one per line
in a text file, the path of which is the command line parameter of this script.

All SensorGroup and Unit objects must be present before running this script.
Building objects will be created.  

Run the script with:
    ./add_boats.py sensor_euis.txt
'''

import os
import sys
import traceback
import django
import pandas as pd

# need to add the directory two above this to the Python path
# so the bmsapp package can be found
this_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.abspath(os.path.join(this_dir, '../../'))
sys.path.insert(0, app_dir)

# prep the Django environment because we need access to the module
# that manipulates the Reading database.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bmon.settings")
django.setup()

from bmsapp.models import DashboardItem, SensorGroup, Unit, Sensor, Building, BldgToSensor

# get the needed Sensor Unit objects
unit_on_off = Unit.objects.filter(label='1=On 0=Off')[0]
unit_volts = Unit.objects.filter(label='Volts')[0]
unit_deg_f = Unit.objects.filter(label='deg F')[0]
unit_db = Unit.objects.filter(label='dB')[0]

# Sensors to create with info
SENSORS = (
    ('highWater', 'High Bilge Water', unit_on_off, ('LED', 1, 1, 0, 0, None, None)),
    ('shorePower', 'Shore Power', unit_on_off, ('LED', 1, 2, 1, 1, None, None)),
    ('bilgePump', 'Bilge Pump', unit_on_off, ('graph', 1, 3, 0, 1, 0, 1)),
    ('batteryV', 'Battery Voltage', unit_volts, ('gauge', 2, 1, 12.0, 14.7, None, None)),
    ('temperature', 'Interior Temperature', unit_deg_f, ('graph', 2, 2, 35, 85, 10, 80)),
    ('snr', 'Boat Sensor Signal', unit_db, ('graph', 2, 3, -7, 15, -15, 15)),
)

# Get needed Sensor Group objects
grp_boat_mon = SensorGroup.objects.filter(title='Boat Monitoring')[0]
grp_weather = SensorGroup.objects.filter(title='Weather')[0]

# Get the two Seward weather sensors
sensor_wx_temp = Sensor.objects.filter(sensor_id='PAWD_temp')[0]
sensor_wx_wind = Sensor.objects.filter(sensor_id='PAWD_wind')[0]

# Read the EUIs from the file and capitalize.
euis = [eui.strip().upper() for eui in open(sys.argv[1]).readlines() if len(eui.strip())]

for eui in euis:
    try:
        # make a building
        bldg_title = f'Boat {eui[-4:]}'
        bldg = Building(
            title=bldg_title,
            latitude=60.118170,
            longitude=-149.436431,
            )
        bldg.save()

        # make the sensors for this boat
        sort_order = 10
        for s_suffix, s_title, s_unit, s_dash in SENSORS:
            sensor = Sensor(sensor_id=f'{eui}_{s_suffix}', title=s_title, unit=s_unit)
            sensor.save()

            # now the object that links the sensor to a building
            link = BldgToSensor(building=bldg, sensor=sensor, sensor_group=grp_boat_mon, sort_order=sort_order)
            link.save()
            sort_order += 10

            # Add a dashboard item
            d_type, d_row, d_col, d_min_norm, d_max_norm, d_min_ax, d_max_ax = s_dash
            if len(d_type):
                DashboardItem(
                    building=bldg,
                    widget_type=d_type,
                    row_number=d_row,
                    column_number=d_col,
                    sensor=link,
                    minimum_normal_value=d_min_norm,
                    maximum_normal_value=d_max_norm,
                    minimum_axis_value=d_min_ax,
                    maximum_axis_value=d_max_ax,
                ).save()

        # Add the two Seward Weather items
        link = BldgToSensor(building=bldg, sensor=sensor_wx_temp, sensor_group=grp_weather, sort_order=10)
        link.save()
        DashboardItem(
            building=bldg,
            widget_type='graph',
            row_number=3,
            column_number=1,
            sensor=link,
            minimum_normal_value=20,
            maximum_normal_value=60,
        ).save()

        link = BldgToSensor(building=bldg, sensor=sensor_wx_wind, sensor_group=grp_weather, sort_order=20)
        link.save()
        DashboardItem(
            building=bldg,
            widget_type='graph',
            row_number=3,
            column_number=2,
            sensor=link,
            minimum_normal_value=0,
            maximum_normal_value=25,
        ).save()

    except:
        print(f'Error processing: {eui}')
        traceback.print_exc()
