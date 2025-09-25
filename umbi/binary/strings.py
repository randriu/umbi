"""
Utilities for (de)serializing strings.
"""

from .integers import uint_to_bytes, bytes_to_uint
from .utils import split_bytes


def bytes_to_string(bytestring: bytes) -> str:
    """Convert a binary string to a utf-8 string."""
    return bytestring.decode("utf-8")


def string_to_bytes(string: str) -> bytes:
    """Convert a utf-8 string to a binary string."""
    return string.encode("utf-8")


def string_pack(string: str) -> bytes:
    """Convert a utf-8 string to a uint16 length-prefixed byte string."""
    string_bytes = string_to_bytes(string)
    length = len(string_bytes)
    prefix_bytes = uint_to_bytes(length, 2)
    return prefix_bytes + string_bytes


def string_unpack(bytestring: bytes) -> tuple[str, bytes]:
    """
    Convert a uint16 length-prefixed byte string to a utf-8 string.
    :return: the decoded string
    :return: the remainder of the bytestring after extracting the string
    """
    prefix_size = 2  # size of uint16
    prefix, bytestring = split_bytes(bytestring, prefix_size)
    length = bytes_to_uint(prefix)
    string_bytes, remainder = split_bytes(bytestring, length)
    string = bytes_to_string(string_bytes)
    return string, remainder
