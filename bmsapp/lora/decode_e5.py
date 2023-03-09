"""Module to decode sensors developed with the SEEED E5 LoRaWAN module.
"""
from typing import Any, List, Tuple
import random

def decode_e5(data: bytes) -> List[Tuple[str, Any]]:
    """Decodes the payload from a custom Sensor from Analysis North using the
    SEEED E5 module.  Returns a list of tuples: (field name, value) or
    (field name, (value, time offset))
    """

    int16 = lambda ix: data[ix] << 8 | data[ix + 1]

    fields = []

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

    return fields

if __name__ == "__main__":
    cases = (
        '01ffff00A0',
        '0100000000',
        '0100010002',
        '02',
    )
    for dta in cases:
        res = decode_e5(bytes.fromhex(dta))
        print(res)
    