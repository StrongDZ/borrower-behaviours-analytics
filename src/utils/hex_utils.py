
from hexbytes import HexBytes

def to_int(value):
    """Chuyển đổi an toàn: int, str('0x...'), HexBytes → int"""
    if value is None:
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, HexBytes):
        return int(value.hex(), 16)
    if isinstance(value, str):
        if value.startswith("0x"):
            return int(value, 16)
        elif value.isdigit():
            return int(value)
    return 0

def to_str(value):
    """Chuyển đổi an toàn: HexBytes, str, bytes → str (lowercase)"""
    if value is None:
        return ""
    if isinstance(value, HexBytes):
        return value.hex()
    if isinstance(value, (bytes, bytearray)):
        return value.hex()
    if isinstance(value, str):
        return value.lower()
    return str(value).lower()

def to_hex(value):
    if isinstance(value, int):
        return hex(value)
    if isinstance(value, str) and value.startswith("0x"):
        return value
    if isinstance(value, str) and value.isdigit():
        return hex(int(value))
    return value
