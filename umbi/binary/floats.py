import struct
from bitstring import BitArray

def double_to_bytes(value: float, little_endian: bool = True) -> bytes:
    ef = "<" if little_endian else ">"
    return struct.pack(f"{ef}d", value)

def bytes_to_double(data: bytes, little_endian: bool = True) -> float:
    ef = "<" if little_endian else ">"
    return struct.unpack(f"{ef}d", data)[0]

def double_pack(value: float) -> BitArray:
    """Convert a single double value to a fixed-length bit representation."""
    return BitArray(float=value, length=64)

def double_unpack(bits: BitArray) -> float:
    """Convert a fixed-length bit representation to a single double value."""
    assert len(bits) == 64, "double must be represented with 64 bits"
    return bits.float