#!/usr/bin/env python
'''Adds a number of sensors to the system using sensor attributes stored in
a text file.  This can be less time consuming than using the Admin interface
to add the sensors.

The sensor information must be stored in an Excel file and the path of that
file is passed as a command line argument to this script.
The file must have the format shown in the add_sensors_sample.xlsx spreadsheet
stored in the 'files' subdirectory.

All SensorGroup and Unit objects must be present before running this script.
Building objects will be created as needed.  If a sensor with the same
sensor_id is present in the database, it will be used with all of its existing
properties instead of creating a new one.

Run the script with:
    add_sensors.py excel_file_name.xlsx
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

from bmsapp.models import SensorGroup, Unit, Sensor, Building, BldgToSensor

# Read the Excel file into a DataFrame and delete blank lines
df = pd.read_excel(sys.argv[1]).dropna(how='all')

for ix, sens in df.iterrows():
    try:

        # Get the building or make one if not there
        bldgs = Building.objects.filter(title=sens.Building)
        if len(bldgs):
            bldg = bldgs[0]
        else:
            bldg = Building(title=sens.Building)
            bldg.save()

        # make the Sensor object if it doesn't exist already
        sensors = Sensor.objects.filter(sensor_id=sens['Sensor ID'])
        if len(sensors):
            sensor = sensors[0]
        else:
            sensor = Sensor(sensor_id=sens['Sensor ID'], title=sens.Title)
            sen_unit = Unit.objects.filter(label=sens['Unit Label'])[0]
            sensor.unit = sen_unit
            if type(sens['Calc or Transform Function'])==unicode:
                sensor.is_calculated = True if sens['Is Calc Field']==1.0 else False
                sensor.tran_calc_function = sens['Calc or Transform Function'].strip()
                try:
                    sensor.function_parameters = sens['Function Parameters'].strip()
                except:
                    # if blank, strip() throws error
                    sensor.function_parameters = ''
            sensor.save()

        # now the object that links sensors to buildings
        grp = SensorGroup.objects.filter(title=sens['Sensor Group'])[0]
        link = BldgToSensor(building=bldg, sensor=sensor, sensor_group=grp, sort_order=int(sens['Sort Order']))
        link.save()

    except:
        print 'Error processing: %s' % sens
        traceback.print_exc()
