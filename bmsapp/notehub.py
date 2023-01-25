'''Extracts sensor readings from a Blues Wireless Notehub Routing message.
'''
import base64
import bz2
import ast
import random

def extract_readings(req_data):
    """Returns a list of sensor readings (ts, sensor_id, val) from a Notehub Route
    request.
    'req_data' is a dictionary converted from the JSON post data of the Notehub request.
    """

    # first determine the format of the Notehub message.
    if 'reading_type' in req_data:
        reading_type = req_data['reading_type']
    elif 'pv_monitoring' in req_data['product']:
        reading_type = 'fields_in_body'
    elif 'tempmonitor' in req_data['product']:
        reading_type = 'standalone'
    else:
        raise ValueError(f"Unknown Blues Notehub reading type, device: {req_data['best_id']}")

    # the list that will hold the extracted readings
    readings = []

    if reading_type == 'fields_in_body':
        # this was the format used for Tyler's solar monitoring in Kenny Lake.
        # multiple field values are stored in the body of the request.

        # extract timestamp and device serial number
        ts = req_data['when']
        dev_id = req_data['device'].split(':')[1]

        # loop through data fields
        for fld, val in req_data['body'].items():
            readings.append([ts, f'{dev_id}_{fld}', val])

    elif reading_type == 'ts_id_val_bz2':

        # readings are the compressed and base64 representation of the string 
        # representationo of a readings list.
        data_compressed = base64.b64decode(req_data['readings'])
        data = bz2.decompress(data_compressed)
        readings = ast.literal_eval(data.decode('utf-8'))
    
    elif reading_type == 'standalone':
        # Notecard is operating stand-alone without microprocessor.
        ts = req_data['when']
        dev_id = req_data['best_id']
        fields = []
        if 'temp' in req_data:
            fields.append(('temperature', req_data['temp'] * 1.8 + 32.0))
        if 'voltage' in req_data and random.random() < 0.2:
            # add voltage voltage for 1/5 of the readings to save database space.
            fields.append(('vdd', req_data['voltage']))

        readings = []
        for fld, val in fields:
            readings.append([ts, f'{dev_id}_{fld}', val])

    else:
        raise ValueError(f'Unrecognized Notehub reading type: {reading_type}')

    return readings
