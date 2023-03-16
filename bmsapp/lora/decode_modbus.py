"""Module for decoding MODBUS payloads from Dragino RS485 sensors.
"""

import struct
from typing import Dict, Any

def decode(data: bytes) -> Dict[str, Any]:
    # the first byte is the Payload version and indicates what type of MODBUS
    # device is connected to the Dragino converter.
    if data[0] == 1:
        # Spire T-Mag BTU meter
        return decode_tmag(data[1:])

    elif data[0] == 9:
        # PZEM Power Sensor
        return decode_pzem(data[1:])

def float_inverse(byte_data: bytes) -> float:
    # Returns a float value from a 4-byte array 'byte_data', which is formatted
    # in the MODBUS float inverse format.
    reversed_words = byte_data[2:4] + byte_data[:2]
    return struct.unpack('>f', reversed_words)[0]

def long_inverse(byte_data: bytes) -> int:
    # Returns a 32-bit integer from the 4-byte array 'byte_data', which is
    # formatted in the MODBUS long inverse format.
    reversed_words = byte_data[2:4] + byte_data[:2]
    return struct.unpack('>l', reversed_words)[0]


def decode_tmag(data: bytes) -> Dict[str, Any]:
    """Decodes Spire T-Mag MODBUS payload with following structure:
    bytes 0:3 -   flow rate m3/hr, float inverse, return gallons/minute
    bytes 4:7 -   heat rate in kW, float inverse, return BTU/hour
    bytes 8:11 -  total heat in kWh, long inverse, combine with next and return MMBTU
    bytes 12:15 - total heat, decimal portion, float inverse, kWh, combined with above
    bytes 16:17 - temperature A in deg-C, unsigned 16-bit int, returned in deg-F
    bytes 18:19 - temperature B in deg-C, unsigned 16-bit int, returned in deg-F
    """
    # holds the dictionary of results
    res = {}
    int16 = lambda ix: data[ix] << 8 | data[ix + 1]

    res['flow'] = float_inverse(data[:4]) * 4.403     # converts m3/hr to gpm
    res['heat_rate'] = float_inverse(data[4:8]) * 3413.   # from kW to BTU/hr
    heat_total = long_inverse(data[8:12]) + float_inverse(data[12:16])
    res['heat_total'] = heat_total * 0.003413    # in MMBTU

    res['temperatureA'] = int16(16) * 1.8 + 32.0
    res['temperatureB'] = int16(18) * 1.8 + 32.0

    return res


def decode_pzem(data: bytes) -> Dict[str, Any]:
    """Decodes Peacefair PZEM MODBUS power sensors.
    """
    res = {}
    int16 = lambda ix: data[ix] << 8 | data[ix + 1]
    int32 = lambda ix: int16(ix) + int16(ix + 2) * 65536

    res['voltage'] = int16(0) * 0.1            # Volts
    # res['current'] = int32(2) * 0.001        # Amps
    res['power'] = int32(6) * 0.1    # Watts
    res['energy'] = int32(10)        # Watt-hours
    res['frequency'] = int16(14) * 0.1     # Hz
    res['power_factor'] = int16(16) * 0.01

    return res


if __name__ == "__main__":
    from pprint import pprint
    # should give flow = 21.50, heat rate = 27,357.3, total heat = 237.655
    # tempA = 59.0, tempB = 62.6
    hexstr = '01 4000409C 40004100 10000001 FF003F11 000F 0011'
    pprint(decode(bytes.fromhex(hexstr)))

    # should give voltage = 121.9, current = 0.163, power = 19.9, energy = 50
    # frequency = 59.9, power factor = 1.00
    hexstr = '09 04C3 00A30000 00C70000 00320000 0257 0064'
    pprint(decode(bytes.fromhex(hexstr)))

