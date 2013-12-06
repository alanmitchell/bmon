'''
Module used to store incoming sensor readings in the database.
'''

import dateutil.parser, calendar, re, time
import bmsdata, models, global_vars
from calcs import transforms

def store(reading_id, request_data):
    '''
    Stores a reading into the Reading database.
    'reading_id' is the ID of the sensor or calculated reading to store.
    'request_data' is a dictionary containing the rest of the information related to the reading:
        The 'val' key holds the value to store.  See code below for various formats that 'val' can take.
        The optional 'ts' key holds a date/time string in UTC for the timestamp of the reading. If
            not present, the current time is used.
    '''

    # open the database 
    db = bmsdata.BMSdata(global_vars.DATA_DB_FILENAME)
    
    # get the Sensor object, if available, to see if there is a transform function
    sensors = models.Sensor.objects.filter( sensor_id=reading_id )
    if len(sensors)>0:
        # Take first sensor in list ( should be only one ) and get transform function & parameters
        transform_func = sensors[0].tran_calc_function
        transform_params = sensors[0].function_parameters
    else:
        # no sensor with the requested ID was found.  Therefore, no transform function and parameters.
        transform_func = ''
        transform_params = ''

    # parse the date into a datetime object and then into Unix seconds. Convert to
    # integer.
    if 'ts' in request_data:
        ts = int( calendar.timegm(dateutil.parser.parse(request_data['ts']).timetuple()) )
    else:
        # no timestamp in query parameters, so assume the timestamp is now.
        ts = int(time.time())

    # Determine the final value to store
    val = request_data['val']
    if ('True' in val) or ('Closed' in val) or (val.startswith('Motion') or (val.startswith('Light')) or (val.startswith('Voltage'))):
        val = 1.0
    elif  ('False' in val) or ('Open' in val) or (val.startswith('No')):
        val = 0.0
    else:
        # convert to float the first decimal number
        parts = re.match(r'(-?\d+)\.?(\d+)?', val).groups('0')
        val = float( parts[0] + '.' + parts[1] )

    # if there is a transform function passed, use it to convert the reading values
    if len(transform_func.strip()):
        trans = transforms.Transformer(db)
        ts, reading_id, val = trans.transform_value(ts, reading_id, val, transform_func, transform_params)

    db.insert_reading(ts, reading_id, val)
    
    db.close()
