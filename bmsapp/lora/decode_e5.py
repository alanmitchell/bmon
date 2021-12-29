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
    