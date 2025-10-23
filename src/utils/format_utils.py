from hexbytes import HexBytes

def to_int(value):
    """Convert value to int, handling None and various formats"""
    if value is None:
        return None
    if isinstance(value, HexBytes):
        return int(value, 16)
    if isinstance(value, str) and value.startswith("0x"):
        return int(value, 16)
    if isinstance(value, str) and value.isdigit():
        return int(value)
    if isinstance(value, (int, float)):
        return int(value)
    return value


def to_str(value):
    if isinstance(value, HexBytes):
        return value.hex()
    return str(value)


def to_hex(value):
    if isinstance(value, int):
        return hex(value)
    
    if isinstance(value, str) and value.startswith("0x"):
        return value
    
    if isinstance(value, str) and value.isdigit():
        return hex(int(value))
    
    return value
