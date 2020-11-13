"""Some utilities to assist in decoding LoRaWAN payloads.
"""

def bin16dec(bin: int) -> int:
    """Returns a signed integer from the first 16 bits of an integer
    """
    num = bin & 0xFFFF
    return num - 0x010000 if 0x8000 & num else num

def bin8dec(bin: int) -> int:
    """Return a signed integer from the first 8 bits of an integer
    """
    num = bin & 0xFF
    return num - 0x0100 if 0x80 & num else num
