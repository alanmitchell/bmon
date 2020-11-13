"""Module for decoding the Payload from Dragino LHT65 sensors.
See Javascript LHT65 decoder at:  http://www.dragino.com/downloads/index.php?dir=LHT65/payload_decode/
"""
from typing import Dict, Any
from .decode_utils import bin16dec

def decode_lht65(data: bytes) -> Dict[str, Any]:
    """Returns a dictionary of enginerring values decoded from a Dragino LHT65 Uplink Payload.
    The payload 'data' is a byte array.
    Converts temperatures to Fahrenheit instead of Celsius like the original Dragino decoder.
    Kept naming of results elements consistent with the Elsys decoder.
    """

    # holds the dictionary of results
    res = {}

    def int16(ix: int) -> int:
        """Returns a 16-bit integer from the 2 bytes starting at index 'ix' in data byte array.
        """
        return (data[ix] << 8) | (data[ix + 1])

    # Each of the functions below decodes one sensor type.  The function access the 'data' byte
    # array parameter from the enclosing 'decode' function.  The following functions also add
    # key/value elements to the 'res' results dictionary.
    
    def temp_int():
        temp = int16(2)
        temp = bin16dec(temp) / 100
        res['temperature'] = temp * 1.8 + 32.0

    def humidity():
        res['humidity'] = int16(4) / 10

    def vdd():
        res['vdd'] = (int16(0) & 0x3FFF) / 1000

    def temp_ext():
        temp = int16(7)
        # if there is no external temperature sensor connected, the above will return 0x7FFF.
        # Don't set an output in this case.
        if temp == 0x7FFF:
            return
        temp = bin16dec(temp) / 100
        res['extTemperature'] = temp * 1.8 + 32.0

    def digital():
        res['digital'] = data[7]
        # indicates if transmission was due to an interrupt on the external digital input.
        res['interrupt'] = data[8]

    def light():
        res['light'] = int16(7)

    def analog():
        res['analog'] = int16(7) / 1000

    def pulse():
        res['pulse'] = int16(7)

    # Always decode the internal sensors
    temp_int()
    humidity()
    vdd()

    # Get the type of external sensor
    # The MSBit indicates whether the cable is OK:  0 = cable OK, 1 = not connected
    # We're masking it here and not transmitting it.
    ext_sensor = data[6] & 0x7F    

    if ext_sensor == 0:
        # no external sensor
        pass
    elif ext_sensor == 1:
        temp_ext()
    elif ext_sensor == 4:
        digital()
    elif ext_sensor == 5:
        light()
    elif ext_sensor == 6:
        analog()
    elif ext_sensor == 7:
        pulse()

    return res

def test():
    cases = (
        ('CBF60B0D0376010ADD7FFF', {'temperature': 82.922, 'humidity': 88.6, 'vdd': 3.062, 'extTemperature': 82.05799999999999}),
        ('CB040B55025A0401007FFF', {'temperature': 84.218, 'humidity': 60.2, 'vdd': 2.82, 'digital': 1, 'interrupt': 0}),
        ('CB060B5B02770400017FFF', {'temperature': 84.326, 'humidity': 63.1, 'vdd': 2.822, 'digital': 0, 'interrupt': 1}),
        ('CB030B2D027C0501917FFF', {'temperature': 83.49799999999999, 'humidity': 63.6, 'vdd': 2.819, 'light': 401}),
        ('CB0B0B640272060B067FFF', {'temperature': 84.488, 'humidity': 62.6, 'vdd': 2.827, 'analog': 2.822}),
        ('CBD50B0502E60700067FFF', {'temperature': 82.778, 'humidity': 74.2, 'vdd': 3.029, 'pulse': 6}),
    )
    for dta, result in cases:
        res = decode_lht65(bytes.fromhex(dta))
        print(res)
        assert res == result

if __name__ == '__main__':
    # To run this without import error, need to run "python -m decoder.decode_lht65" from the top level directory.
    test()