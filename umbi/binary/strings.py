"""
Utilities for (de)serializing strings.
"""

from .primitives import *

def bytes_to_string(bytestring: bytes) -> str:
    """Convert a binary string to a utf-8 string."""
    return bytestring.decode("utf-8")


def string_to_bytes(string: str) -> bytes:
    """Convert a utf-8 string to a binary string."""
    return string.encode("utf-8")


def string_to_bits(string: str) -> BitArray:
    """Convert a utf-8 string to a uint16 length-prefixed byte string."""
    string_bytes = string_to_bytes(string)
    length = len(string_bytes)
    prefix_bytes = primitive_to_bytes(length, "uint16", little_endian=True)
    bytestring = prefix_bytes + string_bytes
    bits = BitArray()
    bits.prepend(BitArray(bytes=prefix_bytes))
    bits.prepend(BitArray(bytes=string_bytes))
    return bits


def bits_to_string(bits: BitArray) -> str:
    """Convert a uint16 length-prefixed byte string to a utf-8 string."""
    prefix_size = 2 # size of uint16
    bytestring = bits.tobytes()
    prefix, bytestring = bytestring[:prefix_size], bytestring[prefix_size:]
    length = bytes_to_primitive(prefix, "uint16")
    assert len(bytestring) >= length, "data is shorter than the specified length"
    return bytes_to_string(bytestring)
