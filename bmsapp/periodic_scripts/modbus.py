"""Script to import data from a device that supports MODBUS TCP.
Multiple registers can be read and returned as new BMON sensor readings.
"""

from __future__ import division   # needed for transform functions
import time
from math import *       # make available for transform functions
import traceback
import pandas as pd
import modbus_tk.defines as cst
from modbus_tk import modbus_tcp

def run(site_id='', host='', device_id=1, sensors=[], **kwargs):
    """This function is called by the Periodic Script controller. The
    parameters are:
        'site_id': (required) The string to prepend to each sensor name to create
            a BMON Sensor ID.
        'host': (required) The IP address or host name of the MODBUS host.
        'device_id': (optional, defaults to 1) The MODBUS device or unit ID.
        'sensors': A list of sensors to read and return from the MODBUS device.
            Each sensor description is in turn a list, using the following format:
                [port # on host to access the required MODBUS register,
                 MODBUS address,
                 name to give this sensor (prepended by the site_id to make a sensor ID),
                 optional transform function, such as:  'val / 10' or 'val * 0.01'
                ]
            The 'MODBUS Address' can be a list of addresses.  If so, the values from those
            addresses are combined to create one value; the individual values are
            interpreted as 16-bit "digits" in a multi-digit number.  The first address in
            the list is assumed to hold the most-significant digit.
    """
    errors = ''  # start tracking errors

    try:
        # sort the sensor list and put into DataFrame
        sensors_sorted = sorted(sensors)
        df = pd.DataFrame(data=sensors_sorted)
        if len(df.columns)==3:
            df.columns = ['port', 'address', 'sensor_name']
            # add the transform column, albeit empty
            df['transform'] = None
        else:
            df.columns = ['port', 'address', 'sensor_name', 'transform']

        # loop through each port and read sensor values

        ts = time.time()     # use common timestamp for all readings.
        readings = []        # accumulate readings here

        groups = df.groupby('port')
        for port, dfg in groups:
            try:
                # find range of addresses to read
                start_address = dfg.address.min()
                end_address = dfg.address.max()
                addr_count = end_address - start_address + 1

                # read the range of addresses from this port
                master = modbus_tcp.TcpMaster(host=host, port=port, timeout_in_sec=5.0)
                res = master.execute(device_id, cst.READ_HOLDING_REGISTERS, start_address, addr_count)
                master.close()

                # process each sensor
                for ix, row in dfg.iterrows():
                    try:
                        val = res[row['address'] - start_address]
                        if row['transform']:
                            val = eval(row['transform'])
                        sensor_id = '%s_%s' % (site_id, row['sensor_name'])
                        readings.append((ts, sensor_id, val))

                    except Exception as e:
                        errors += '\nError processing %s: %s' % (row['sensor_name'], str(e))
                        continue   # to next sensor

            except:
                errors += '\n' + traceback.format_exc()
                continue   # to next port

    except:
        # Store information about the error that occurred
        errors += '\n' + traceback.format_exc()

    results = {'readings': readings,
               'script_errors': errors}

    return results
