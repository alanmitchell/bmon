"""Module to decode sensors developed with the SEEED E5 LoRaWAN module.
"""
from typing import Any, List, Tuple
import random
from struct import unpack

def decode_e5(data: bytes) -> List[Tuple[str, Any]]:
    """Decodes the payload from a custom Sensor from Analysis North using the
    SEEED E5 module.  Returns a list of tuples: (field name, value) or
    (field name, (value, time offset))
    """

    int16 = lambda ix: data[ix] << 8 | data[ix + 1]

    fields = []

    # fix special case of Resol controllers.  They sometimes report an extra Hex 0 at
    # beginning and end of data payload.
    hex_str = data.hex()
    if len(hex_str) == 72 and hex_str[:3] == '007':
        # trim off first and last hex digits
        data = bytes.fromhex(hex_str[1:-1])

    if data[0] == 1:
        # list of power values
        val_ct = (len(data) - 1) // 2  #  of readings
        # most current reading is last (0 time offset), and readings are
        # spaced 1 second apart.
        for rdg_ix in range(val_ct):
            data_ix = 1 + rdg_ix * 2
            pwr = int16(data_ix) * 0.1      # value is tenths of a Watt
            fields.append(
                ('power', (pwr, -(val_ct - rdg_ix - 1)))
            )

    elif data[0] == 2:
        # reboot.  Return a random value so that it is easy to find reboot points
        # on the graph.
        fields.append(
            ('reboot', random.random())
        )

    elif data[0] == 3:
        # average power for an interval.
        pwr = int16(1) * 0.1    # power is given in tenths of Watt in payload
        ts_offset = -int16(3)   # timestamp offset, needs to be negative
        fields.append(
            ('power', (pwr, ts_offset))
        )

    elif data[0] == 4:
        # ID plus a value
        field_id = int.from_bytes(data[1:6], 'big')
        val = int.from_bytes(data[6:], 'big')
        fields.append(
            (str(field_id), val)
        )

    elif data[0] == 5:
        # BTU meter values
        heat_count = int.from_bytes(data[1:4], 'big') / 10.0    # now in deg-F * gallons
        flow_count = int.from_bytes(data[4:7], 'big')           # gallons
        temp_hot = int.from_bytes(data[7:9], 'big') / 10.0      # deg F
        temp_cold = int.from_bytes(data[9:11], 'big') / 10.0    # deg F
        fields = [
            ('heat', heat_count),
            ('flow', flow_count),
            ('temp_hot', temp_hot),
            ('temp_cold', temp_cold)
        ]

    elif data[0] == 6:
        # multi-channel counter
        channel_ct = int((len(data) - 1) / 3)
        for ch in range(channel_ct):
            ct = int.from_bytes(data[1 + ch*3 : 4 + ch*3], 'big')
            fields.append(
                (f'count{ch}', ct)
            )

    elif data[0] == 7:
        # Decoder for Resol solar controller.  See the data collection system here:
        # https://github.com/alanmitchell/resol-to-lora
        
        # Decode the temperature/switch channels 1 - 15.
        # Each channel is a 2-byte signed integer; the first channel starts as data[1].
        # If the channel is a temperature sensor, the value is in tenths of deg C;
        # a value of 8888 indicates no sensor present; do not report this channel.
        # If the channel is a switch, the value is 9999 if open and -9999 if close. Convert
        # open to 0 and closed to 1.
        for i in range(1, 16):
            val = unpack('>h', data[i*2-1:i*2+1])[0]
            if val != 8888:
                field_id = f'ch{i:02d}'
                if val == 9999:
                    val = 0
                elif val == -9999:
                    val = 1
                else:
                    # value is a temperature in tenths deg C. Convert to deg F
                    val = val * 0.18 + 32.0
                fields.append(
                    (field_id, val)
                )

        # Now the irradiation sensor, W / m2 are the units
        val = unpack('>h', data[31:33])[0]
        if val != 8888:
            fields.append(
                ('solar', val)
            )

        # Now the 14 relay values, which are packed into the bits of the last two bytes
        # of data.
        val = int.from_bytes(data[33:35], 'big')
        for i in range(14):
            relay_val = (val & (1 << i)) >> i
            field_id = f'relay{i+1:02d}'
            fields.append(
                (field_id, relay_val)
            )

    return fields

if __name__ == "__main__":
    cases = (
        '01ffff00A0',
        '0100000000',
        '0100010002',
        '02',
        '07FFF400D9D8F1270F22B822B822B822B822B822B822B822B8270F270F270F00000000',
        '00701C00209021000AE01670175023B023C012E020500FD22B800F8011C0119010996000'
    )
    for dta in cases:
        res = decode_e5(bytes.fromhex(dta))
        print(res)
    