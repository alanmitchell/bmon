"""Module for decoding the Payload from Elsys LoRaWAN sensors.
See Javascript Elsys decoder at:  https://www.elsys.se/en/elsys-payload/
"""
from typing import Dict, Any
from .decode_utils import bin16dec, bin8dec

def decode(data: bytes) -> Dict[str, Any]:
    """Returns a dictionary of enginerring values decoded from an Elsys Uplink Payload.
    The payload 'data' is a byte array.
    Works with all Elsys LoRaWAN sensors.
    Converts temperatures to Fahrenheit instead of Celsius like the original Elsys decoder.
    All millivolt Voltage values are now in Volts instead of the original millivolts from Elsys.
    (the uVolt sensor type was left in microvolts).
    Changes some of the names of the results keys from the original Elsys names:
    shortens "external" to "ext", "internal" to "int".
    Also, made two channel naming more consistent: first channel name does *not* input a "1"
    at the end, but the second channel of name includes a "2".  This also keeps name consistent
    with sensors that don't have a second channel, like the ELT Lite and the LHT65.
    """

    # holds the dictionary of results
    res = {}

    def int16(ix: int) -> int:
        """Returns a 16-bit integer from the 2 bytes starting at index 'ix' in data byte array.
        """
        return (data[ix] << 8) | (data[ix + 1])

    # Each of the functions below decodes one sensor type.  The function access the 'data' byte
    # array parameter from the enclosing 'decode' function.  The following functions also add
    # key/value elements to the 'res' results dictionary.  Each function takes an index parameter,
    # which is the index the 'data' array where the sensor data starts; although, the i position
    # contains the sensor type indicator, so the actual data really starts at the i+1 position.
    # Each of the functions returns the number of bytes consumed by the actual sensor data (not
    # counting the 1 byte consumed by the sensor type identifier.)

    def temp(i: int) -> int:
        # converts to Fahrenheit.
        temp = int16(i+1)
        temp = bin16dec(temp) / 10
        res['temperature'] = temp * 1.8 + 32.0
        return 2

    def rh(i: int) -> int:
        res['humidity'] = data[i + 1]
        return 1

    def acc(i: int) -> int:
        res['x'] = bin8dec(data[i + 1]) / 63.0      # converts to Gs
        res['y'] = bin8dec(data[i + 2]) / 63.0
        res['z'] = bin8dec(data[i + 3]) / 63.0
        return 3

    def light(i: int) -> int:
        res['light'] = int16(i+1)
        return 2

    def motion(i: int) -> int:
        res['motion'] = (data[i + 1])
        return 1

    def co2(i: int) -> int:
        res['co2'] = int16(i+1)
        return 2

    def vdd(i: int) -> int:
        # changed from Elsys, result is in Volts not millivolts
        res['vdd'] = int16(i+1) / 1000.
        return 2

    def analog1(i: int) -> int:
        # changed from Elsys, result is in Volts not millivolts
        res['analog'] = int16(i+1) / 1000.
        return 2

    def gps(i: int) -> int:
        res['lat'] = (data[i + 1] | data[i + 2] << 8 | data[i + 3] << 16 | (0xFF << 24 if data[i + 3] & 0x80 else 0)) / 10000
        res['long'] = (data[i + 4] | data[i + 5] << 8 | data[i + 6] << 16 | (0xFF << 24 if data[i + 6] & 0x80 else 0)) / 10000
        return 6

    def pulse1(i: int) -> int:
        res['pulse'] = int16(i+1)
        return 2

    def pulse1_abs(i: int) -> int:
        res['pulseAbs'] = (data[i + 1] << 24) | (data[i + 2] << 16) | (data[i + 3] << 8) | (data[i + 4])
        return 4

    def ext_temp1(i: int) -> int:
        temp = int16(i+1)
        temp = bin16dec(temp) / 10
        res['extTemperature'] = temp * 1.8 + 32.0
        return 2

    def ext_digital(i: int) -> int:
        res['digital'] = data[i + 1]
        return 1

    def ext_distance(i: int) -> int:
        res['distance'] = int16(i+1)
        return 2

    def acc_motion(i: int) -> int:
        res['accMotion'] = data[i + 1]
        return 1

    def ir_temp(i: int) -> int:
        iTemp = int16(i+1)
        iTemp = bin16dec(iTemp)
        eTemp = int16(i + 3)
        eTemp = bin16dec(eTemp)
        res['irIntTemperature'] = iTemp / 10 * 1.8 + 32.0
        res['irExtTemperature'] = eTemp / 10 * 1.8 + 32.0
        return 4

    def occupancy(i: int) -> int:
        res['occupancy'] = data[i + 1]
        return 1

    def waterleak(i: int) -> int:
        res['waterleak'] = data[i + 1]
        return 1

    def grideye(i: int) -> int:
        ref = data[i+1]
        res['grideye'] = [ref + data[i + 2 + j] / 10.0 for j in range(64)]
        return 64

    def pressure(i: int) -> int:
        press = (data[i + 1] << 24) | (data[i + 2] << 16) | (data[i + 3] << 8) | (data[i + 4])
        res['pressure'] = press / 1000
        return 4

    def sound(i: int) -> int:
        res['soundPeak'] = data[i + 1]
        res['soundAvg'] = data[i + 2]
        return 2

    def pulse2(i: int) -> int:
        res['pulse2'] = int16(i+1)
        return 2

    def pulse2_abs(i: int) -> int:
        res['pulseAbs2'] = (data[i + 1] << 24) | (data[i + 2] << 16) | (data[i + 3] << 8) | (data[i + 4])
        return 4

    def analog2(i: int) -> int:
        # changed from Elsys, result is in Volts not millivolts
        res['analog2'] = int16(i+1) / 1000.
        return 2

    def ext_temp2(i: int) -> int:
        temp = int16(i+1)
        temp = bin16dec(temp) / 10 * 1.8 + 32.0
        try:
            exist_rd =  res['extTemperature2']
            # there already is a Temperature 2 reading, 
            if type(exist_rd) == list:
                # the existing value is already a list of readings.  Append to it.
                res['extTemperature2'].append(temp)
            else:
                # one existing reading. make a list.
                res['extTemperature2'] = [exist_rd, temp]
        except:
            # this is the first External Temperature 2 reading.
            res['extTemperature2'] = temp
        
        return 2

    def ext_digital2(i: int) -> int:
        res['digital2'] = data[i + 1]
        return 1

    def ext_analog_uv(i: int) -> int:
        res['analogUv'] = (data[i + 1] << 24) | (data[i + 2] << 16) | (data[i + 3] << 8) | (data[i + 4])
        return 4

    # list of deconding functions, in their type indicator order.
    decode_funcs = [temp, rh, acc, light, motion, co2,
        vdd, analog1, gps, pulse1, pulse1_abs, ext_temp1,
        ext_digital, ext_distance, acc_motion, ir_temp,
        occupancy, waterleak, grideye, pressure, sound,
        pulse2, pulse2_abs, analog2, ext_temp2, ext_digital2,
        ext_analog_uv]

    # make a dictionary that maps a sensor data type code to a decoding function
    decode_func_map = dict(zip(range(1, len(decode_funcs) + 1), decode_funcs))

    # index into payload byte array
    i = 0
    while i < len(data):
        # retrieve the correct decoding function for a sensor of this type
        cur_decode_func = decode_func_map[data[i]]
        # the decoder function adds decoded values to the results dictionary, and it
        # returns the number of bytes consumed by the decoded value.  Add 1 to account for the
        # byte consumed the sensor type identifier.
        i += cur_decode_func(i) + 1

    return res

def test():
    results = decode(bytes.fromhex('0100e202290400270506060308070d6219000119FFFF'))
    print(results)
    assert results == {'temperature': 72.68, 'humidity': 41, 'light': 39, 'motion': 6, 'co2': 776, 'vdd': 3.426, 'extTemperature2': [32.18, 31.82]}

if __name__ == "__main__":
    # To run this without import error, need to run "python -m decoder.decode_elsys" from the top level directory.
    test()
