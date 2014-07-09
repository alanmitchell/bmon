'''Adds a number of sensors to the system using sensor attributes stored in
a text file.

The sensor information must be stored in a text file with the name
'new_sensors.txt' stored in the same directory as this script.  The first line
of that file is a header line.  The file must have the format shown in the
New_Sensors.xlsx spreadsheet stored in this directory.

All SensorGroup and Unit objects must be present before running this script.
Building objects will be created as needed.  If a sensor with the same
sensor_id is present in the database, it will be used with all of its existing
properties instead of creating a new one.

Run this script by using the "runscript" command from the django_extensions
application.  This application must be listed in the INSTALLED_APPS setting in
the django settings.py file.  
See http://django-extensions.readthedocs.org/en/latest/runscript.html for 
documentation.

Run the script with:
    ./manage.py runscript add_sensors   # note that there is no '.py' added
'''

from bmsapp.models import SensorGroup, Unit, Sensor, Building, BldgToSensor
import os, traceback

def run():
    '''This method is called by the 'runscript' command.
    '''
    
    # walk through the lines in the input file, each one being a sensor
    in_file = os.path.join(os.path.dirname(__file__), 'new_sensors.txt')
    for lin in open(in_file).readlines()[1:]: # skip the header line
        try:
            flds = lin.split('\t')
            
            # Get the building or make one if not there
            bldgs = Building.objects.filter(title=flds[0])
            if len(bldgs):
                bldg = bldgs[0]
            else:
                bldg = Building(title=flds[0])
                bldg.save()
    
            # make the Sensor object if it doesn't exist already
            sensors = Sensor.objects.filter(sensor_id=flds[1])
            if len(sensors):
                sensor = sensors[0]
            else:
                sensor = Sensor(sensor_id=flds[1], title=flds[2])
                sen_unit = Unit.objects.filter(label=flds[3])[0]
                sensor.unit = sen_unit
                if len(flds[6].strip()):
                    sensor.is_calculated = True
                    sensor.tran_calc_function = flds[6].strip()
                    sensor.function_parameters = flds[7].strip()
                sensor.save()
                
            # now the object that links sensors to buildings
            grp = SensorGroup.objects.filter(title=flds[4])[0]
            link = BldgToSensor(building=bldg, sensor=sensor, sensor_group=grp, sort_order=int(flds[5]))
            link.save()
            
        except:
            print 'Error processing: %s' % lin
            traceback.print_exc()