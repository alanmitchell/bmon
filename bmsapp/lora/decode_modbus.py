"""Module for decoding MODBUS payloads from Dragino RS485 sensors.
"""

import struct
from typing import Dict, Any

def decode(data: bytes, payload_fields: Dict[str, Any]) -> Dict[str, Any]:
    # the first byte is the Payload version and indicates what type of MODBUS
    # device is connected to the Dragino converter.

    # The high bit of the payload_version indicates whether the Activate button was
    # pressed on the RS485-LN. Remove it to determine the payload version.
    payload_version = data[0] & 0x7F

    if payload_version == 1:
        # Spire T-Mag BTU meter
        return decode_tmag(data[1:])
    
    elif payload_version == 2:
        # Spire EF40 BTU Meter
        return decode_ef40(data[1:])

    elif payload_version == 9:
        # PZEM Power Sensor
        return decode_pzem(data[1:])
    
    elif payload_version == 99:
        # already decoded payload
        return payload_fields

def float_inverse(byte_data: bytes) -> float:
    # Returns a float value from a 4-byte array 'byte_data', which is formatted
    # in the MODBUS float inverse format.
    reversed_words = byte_data[2:4] + byte_data[:2]
    return struct.unpack('>f', reversed_words)[0]

def float_std(byte_data: bytes) -> float:
    # Returns a float value from a 4-byte array 'byte_data', which is formatted
    # in regular-order float format, not inverse.
    return struct.unpack('>f', byte_data)[0]

def long_inverse(byte_data: bytes) -> int:
    # Returns a 32-bit integer from the 4-byte array 'byte_data', which is
    # formatted in the MODBUS long inverse format.
    reversed_words = byte_data[2:4] + byte_data[:2]
    return struct.unpack('>l', reversed_words)[0]

def long(byte_data: bytes) -> int:
    # Returns a 32-bit integer from the 4-byte array 'byte_data', which is
    # formatted in the long format.
    return struct.unpack('>l', byte_data)[0]

def long_inverse_unsigned(byte_data: bytes) -> int:
    # Returns a 32-bit integer from the 4-byte array 'byte_data', which is
    # formatted in the MODBUS long inverse format.
    reversed_words = byte_data[2:4] + byte_data[:2]
    return struct.unpack('>L', reversed_words)[0]

def long_unsigned(byte_data: bytes) -> int:
    # Returns a 32-bit integer from the 4-byte array 'byte_data', which is
    # formatted in the long format.
    return struct.unpack('>L', byte_data)[0]

def decode_tmag(data: bytes) -> Dict[str, Any]:
    """Decodes Spire T-Mag MODBUS payload with following structure:
    bytes 0:3 -   flow rate gpm (manual says m3/hr), float standard order (despite manual), return gpm
    bytes 4:7 -   heat rate in kBTU/hr, float standard order (despite manual), return kBTU/hour
    bytes 8:11 -  total heat in kBTU, long (not inverse, despite manual), combine with next
                     and return MMBTU
    bytes 12:15 - total heat, decimal portion, float standard (despite manual), kBTU, ignore, not needed
    bytes 16:17 - temperature A in tenths deg-C, unsigned 16-bit int, returned in deg-F
    bytes 18:19 - temperature B in tenths deg-C, unsigned 16-bit int, returned in deg-F
    """
    # holds the dictionary of results
    res = {}
    int16 = lambda ix: data[ix] << 8 | data[ix + 1]

    if data != b'\xFF' * len(data):    # if error or no response, data will be all 0xFF bytes
        res['flow'] = float_std(data[:4])     
        res['heat_rate'] = float_std(data[4:8])
        
        res['heat_total'] = long_unsigned(data[8:12]) / 1000.0    # in MMBTU

        res['temperatureA'] = int16(16) * 0.18 + 32.0
        res['temperatureB'] = int16(18) * 0.18 + 32.0

    return res

def decode_ef40(data: bytes) -> Dict[str, Any]:
    """Decodes Spire EF40 MODBUS payload with the following structure:
    bytes 0:3 -    flow rate in m3/hr, return GPM
    bytes 4:7      heat rate in GJ/hr, return kBTU/hour
    bytes 8:11     total heat, integer portion in BTU (if EF40 set to BTU), return MMBTU
    bytes 12:15    total heat, fraction portion in BTU (if EF40 set to BTU)
    bytes 16:19    Supply temperature in deg C, return deg F
    bytes 20:23    Return temperature in deg C, return deg F

    Convert m3/hr to GPM and GJ/hr to BTU/hr
    """
    # holds the dictionary of results
    res = {}

    if data[0:8] != b'\xFF' * 8:    # if error or no response, data will be all 0xFF bytes
        res['flow'] = float_inverse(data[0:4]) * 4.4029
        res['heat_rate'] = float_inverse(data[4:8]) * 947.817

    if data[8:16] != b'\xFF' * 8:
        res['heat_total'] = long_inverse_unsigned(data[8:12])
        res['heat_total'] += float_inverse(data[12:16])
        res['heat_total'] /= 1e6       # for MMBTU

    if data[16:24] != b'\xFF' * 8:
        res['temperatureA'] = float_inverse(data[16:20]) * 1.8 + 32.0
        res['temperatureB'] = float_inverse(data[20:24]) * 1.8 + 32.0

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

    # Should give:
    """
    {'flow': 15.710000038146973,
    'heat_rate': 12.430000305175781,
    'heat_total': 21.088,
    'temperatureA': 172.94,
    'temperatureB': 171.32}
    """
    hexstr = '01417B5C294146E1480000526000000000030F0306'
    pprint(decode(bytes.fromhex(hexstr)))

    # should give voltage = 121.9, current = 0.163, power = 19.9, energy = 50
    # frequency = 59.9, power factor = 1.00
    hexstr = '09 04C3 00A30000 00C70000 00320000 0257 0064'
    pprint(decode(bytes.fromhex(hexstr)))

    # should give flow, heat_rate and heat_total equal to 0, temperatureA = 146.88
    # and temperatureB = 27.45
    hexstr = '02 00000000 00000000 00000000 00000000 4B6B427F C200C021'
    pprint(decode(bytes.fromhex(hexstr)))

    # Same as above but no flow and heat rate.
    hexstr = '02 FFFFFFFF FFFFFFFF 00000000 00000000 4B6B427F C200C021'
    pprint(decode(bytes.fromhex(hexstr)))

    # No heat total.
    hexstr = '02 00000000 00000000 FFFFFFFF FFFFFFFF 4B6B427F C200C021'
    pprint(decode(bytes.fromhex(hexstr)))

    # No temps
    hexstr = '02 00000000 00000000 00000000 00000000 FFFFFFFF FFFFFFFF'
    pprint(decode(bytes.fromhex(hexstr)))
    
    # Should give:
    """
    {'flow': 2.5837399858772754,
    'heat_rate': 146.30395523929596,
    'heat_total': 0.012017806526184081,
    'temperatureA': 147.03284988403323,
    'temperatureB': 27.591248321533204}
    """
    hexstr = '023A493F1610403E1E2EF1000078803F4EA0E9427FC170C01C'
    pprint(decode(bytes.fromhex(hexstr)))
