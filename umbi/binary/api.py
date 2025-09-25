"""
A convenient interface for all (de)serializers in this package.
"""

from typing import Union

from .booleans import *
from .intervals import *
from .integers import *
from .rationals import *
from .strings import *
from .floats import *

Numeric = Union[int, float]

def standard_value_type_size(value_type: str) -> int:
    """Return the number of bytes needed to represent a value of the given type."""
    if "-interval" in value_type:
        base_value_type = value_type.replace("-interval", "")
        return 2 * standard_value_type_size(base_value_type)
    if value_type == "rational":
        # for rationals, the standard size is 8+8 bytes
        return standard_value_type_size("int64") + standard_value_type_size("uint64")
    if value_type == "double":
        return 8  # size of double
    _, num_bytes = fixed_size_integer_base_and_size(value_type)
    return num_bytes


def value_to_bytes(value: str | Numeric | Fraction | tuple, value_type: str, little_endian: bool = True) -> bytes:
    """
    Convert a value of a given type to a bytestring.
    :param value_type: either string or one of {int32|uint32|int64|uint64|double|rational}[-interval]
    """
    if value_type == "string":
        assert isinstance(value, str)
        return string_to_bytes(value)  # no endianness for strings
    elif value_type == "rational":
        assert isinstance(value, Fraction)
        return rational_to_bytes(value, little_endian=little_endian)
    elif "-interval" in value_type:
        assert isinstance(value, tuple) and len(value) == 2, "interval value must be a pair"
        return interval_to_bytes(value, value_type, little_endian)
    elif value_type == "double":
        assert isinstance(value, float)
        return double_to_bytes(value, little_endian)
    else:
        assert isinstance(value, int)
        return fixed_size_integer_to_bytes(value, value_type, little_endian)


def bytes_to_value(data: bytes, value_type: str, little_endian: bool = True) -> str | Numeric | Fraction | tuple:
    """
    Convert a binary string to a single value of the given type.
    :param value_type: string or one of {int32|uint32|int64|uint64|double|rational}[-interval]
    :return: a pair of left and right values for interval types, or a single value otherwise
    """
    if value_type == "string":
        return bytes_to_string(data)  # no endianness for strings
    elif value_type == "rational":
        return bytes_to_rational(data, little_endian)
    elif "-interval" in value_type:
        return bytes_to_interval(data, value_type, little_endian)
    elif value_type == "double":
        return bytes_to_double(data, little_endian)
    else:
        return bytes_to_fixed_size_integer(data, value_type, little_endian)


def numeric_pack(value: Numeric, value_type: str, num_bits: int) -> BitArray:
    """Convert a single primitive value of the given type to a fixed-length bit representation."""
    assert value_type in ["int", "uint", "double"], f"unsupported primitive type: {value_type}"
    if value_type == "double":
        assert isinstance(value, float)
        assert num_bits == 64, "double must be represented with 64 bits"
        return double_pack(value)
    assert isinstance(value, int)
    if value_type == "int":
        return int_pack(value, num_bits)
    else:
        return uint_pack(value, num_bits)


def numeric_unpack(bits: BitArray, value_type: str) -> Numeric:
    """Convert a BitArray to a single primitive value of the given type."""
    assert value_type in ["int", "uint", "double"], f"unsupported primitive type: {value_type}"
    if value_type == "double":
        return double_unpack(bits)
    elif value_type == "int":
        return int_unpack(bits)
    else:
        return uint_unpack(bits)
