'''
Module used to store incoming sensor readings in the database.
'''

import dateutil.parser, calendar, re, time

import models, global_vars
from readingdb import bmsdata
from calcs import transforms

def convert_val(ts, reading_id, val, db):
    """Takes a raw reading values 'ts', 'reading_id', and 'val' and converts them
    to a form suitable for storage in the reading database.  If a transform 
    function applies to the reading_id, it is applied.  Also, non-numerical 
    string 'val's are converted to numeric values suitable for storage as a float.
    'db' is a bmsdata.BMSdata reading database object.
    Returned is the tuple (ts, reading_id, val) as any of these could be
    transformed by the transform function.
    """

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

    # If val is a string, decode it into a float value
    if type(val) in (str, unicode):
        if ('True' in val) or ('Closed' in val) or ('On' in val) or (val.startswith('Motion') or (val.startswith('Light')) or (val.startswith('Voltage'))):
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

    return ts, reading_id, val

def store(reading_id, request_data):
    """Stores a reading into the Reading database.
    'reading_id' is the ID of the sensor or calculated reading to store.
    'request_data' is a dictionary containing the rest of the information related to the reading:
        The 'val' key holds the value to store.  See code in convert_val() method
            for various formats that 'val' can take.
        The optional 'ts' key holds a date/time string in UTC for the timestamp 
            of the reading. If not present, the current time is used.
    Returns the message returned by the database insert method.
    """

    # open the database 
    db = bmsdata.BMSdata(global_vars.DATA_DB_FILENAME)
    
    # parse the date into a datetime object and then into Unix seconds. Convert to
    # integer.
    if 'ts' in request_data:
        ts = int( calendar.timegm(dateutil.parser.parse(request_data['ts']).timetuple()) )
    else:
        # no timestamp in query parameters, so assume the timestamp is now.
        ts = int(time.time())

    # Get the value from the request
    val = request_data['val']

    # Convert/transform the fields for storage.
    ts, reading_id, val = convert_val(ts, reading_id, val, db)
    
    # The transformed value could be None, but the database insert method
    # will ignore it.
    msg = db.insert_reading(ts, reading_id, val)
    db.close()
    return msg

def store_many(readings):
    """Stores a list of readings into the database.
    'readings' is a list of 3-element tuples. The three elements of the tuple
    are:
        1:  Unix timestamp of the reading. 
            If None, the current time is substituted.
        2:  The reading id.
        3:  The reading value.  convert_val() is used to convert/transform
            the value before storage.
    Returns the message returned by the database insert method.
    """

    # open the reading database 
    db = bmsdata.BMSdata(global_vars.DATA_DB_FILENAME)
    
    ts_lst = []
    reading_id_lst = []
    val_lst = []
    
    for ts, reading_id, val in readings:
        ts = int(ts) if ts is not None else int(time.time())

        # Convert/transform the fields for storage.
        ts, reading_id, val = convert_val(ts, reading_id, val, db)
        ts_lst.append(ts)
        reading_id_lst.append(reading_id)
        val_lst.append(val)  # could be None, but insert_reading() will ignore it
                                    
    msg = db.insert_reading(ts_lst, reading_id_lst, val_lst)
    db.close()
    return msg
