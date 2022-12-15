'''Extracts sensor readings from a Blues Wireless Notehub Routing message.
'''
import base64
import bz2
import ast

def extract_readings(req_data):
    """Returns a list of sensor readings (ts, sensor_id, val) from a Notehub Route
    request.
    'req_data' is a dictionary converted from the JSON post data of the Notehub request.
    """

    # first determine the format of the Notehub message.
    if 'reading_type' in req_data:
        reading_type = req_data['reading_type']
    else:
        reading_type = 'one_reading_set'

    # the list that will hold the extracted readings
    readings = []

    if reading_type == 'one_reading_set':
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

    else:
        raise ValueError(f'Unrecognized Notehub reading type: {reading_type}')

    return readings
