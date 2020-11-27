"""Module for decoding the Payload from Dragino LHT65 sensors.
See Javascript LHT65 decoder at:  http://www.dragino.com/downloads/index.php?dir=LHT65/payload_decode/
"""
import math
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

def decode_boat_lt2(data: bytes) -> Dict[str, Any]:
    """Decodes the values from a Dragino LT-22222-L sensor, configured
    to do boat monitoring.  The inputs on the LT-22222-L are wired as 
    follows:
        AV1 - Boat Battery Voltage
        AV2 - Voltage across a 10 K-ohm thermistor, with a Beta of 3950K, with a 20 K-ohm
            pull-up resistor to Boat Battery voltage.
        AC1 - Shore Power sensor, which is a DC Wall Wart, 3 - 24 VDC with a 10 K-ohm in
            series to produce a small current.
        DI1 - High Water sensor, which puts Boat Battery Voltage on this terminal when high
            water is present.
        DI2 - Bilge Pump sensor, which puts Boat Battery Voltage on this terminal if the 
            bilge pump is running.
    These signals are decoded into their engineering meaning, for example the Shore 
    Power sensor on the AC1 current input channel is decoded into a 1 if Shore power is
    present and a 0 if not present (the actual current value is *not* returned).
    The LT-22222-L must be in Mode = 1; if not, no values are returned.
    """

    # holds the dictionary of results
    res = {}

    if (data[10] & 0x3f) != 1:
        # not in Mode = 1, return with no values
        return res

    def int16(ix: int) -> int:
        """Returns a 16-bit integer from the 2 bytes starting at index 'ix' in data byte array.
        """
        return (data[ix] << 8) | (data[ix + 1])

    # ---- Battery voltage
    batV = int16(0) / 1000.
    res['batteryV'] = batV 

    # ---- Thermistor Temperatuare sensor
    thermV = int16(2) / 1000.     # voltage across thermistor

    # if the thermistor is not present, this voltage will be high, and do not return
    # a temperature value
    if thermV < 0.97 * batV:
        thermR = thermV / (batV - thermV) * 20000
        # Steinhart coefficients for Adafruit B=3950K thermistor, -10C, 10C, 30C as points.
        lnR = math.log(thermR)
        degK = 1 / (1.441352876e-3 + 1.827883939e-4 * lnR + 2.928343561e-7 * lnR ** 3)
        degF = (degK - 273.15) * 1.8 + 32
        res['temperature'] = degF

    # ------- Shore Power
    shore_ma = int16(4) / 1000.     # current from wall wart in mA
    
    # 3V wall wart with 10K resistor produces 0.3 mA of current.  Use 0.2 mA as 
    # cutoff.
    res['shorePower'] = 1 if shore_ma > 0.2 else 0
        
    # -------- High Water Level
    res['highWater'] = 1 if data[8] & 0x08 else 0

    # -------- Bilge Pump
    res['bilgePump'] = 1 if data[8] & 0x10 else 0

    return res


def test_lht65():
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

def test_boat_lt2():
    cases = (
        '300C1806012C0000FFFF01',
        '300C180600BE000000FF01',
        '300C180600BE000008FF01',
        '300C180600BE000018FF01',
        '300C18060000000018FF01',
        '300C18060000000018FF02',
    )
    for dta in cases:
        res = decode_boat_lt2(bytes.fromhex(dta))
        print(res)

if __name__ == '__main__':
    # To run this without import error, need to run "python -m decoder.decode_lht65" from the top level directory.
    test_lht65()
    test_boat_lt2()
