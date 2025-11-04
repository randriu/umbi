"""
A convenient interface for all (de)serializers in this package.
"""

from .booleans import *
from .floats import *
from .integers import *
from .intervals import *
from .rationals import *
from .strings import *
from .jsons import *




def value_to_bytes(value: JsonLike | str | int | float | Fraction | Interval, value_type: str, little_endian: bool = True) -> bytes:
    """
    Convert a value of a given type to a bytestring.
    :param value_type: either json, string or one of {int32|uint32|int64|uint64|double|rational}[-interval]
    """
    if value_type == "json":
        assert isinstance(value, JsonLike)
        return json_to_bytes(value)
    elif value_type == "string":
        assert isinstance(value, str)
        return string_to_bytes(value)  # no endianness for strings
    elif value_type == "rational":
        assert isinstance(value, Fraction)
        return rational_to_bytes(value, little_endian=little_endian)
    elif "-interval" in value_type:
        assert isinstance(value, Interval)
        return interval_to_bytes(value, value_type, little_endian)
    elif value_type == "double":
        assert isinstance(value, float)
        return double_to_bytes(value, little_endian)
    else:
        assert isinstance(value, int)
        return fixed_size_integer_to_bytes(value, value_type, little_endian)


def bytes_to_value(data: bytes, value_type: str, little_endian: bool = True) -> JsonLike | str | int | float | Fraction | Interval:
    """
    Convert a binary string to a single value of the given type.
    :param value_type: json, string or one of {int32|uint32|int64|uint64|double|rational}[-interval]
    """
    if value_type == "json":
        return bytes_to_json(data)
    elif value_type == "string":
        return bytes_to_string(data)  # no endianness for strings
    elif value_type == "rational":
        return bytes_to_rational(data, little_endian)
    elif "-interval" in value_type:
        return bytes_to_interval(data, value_type, little_endian)
    elif value_type == "double":
        return bytes_to_double(data, little_endian)
    else:
        return bytes_to_fixed_size_integer(data, value_type, little_endian)


def numeric_pack(value: int | float, value_type: str, num_bits: int) -> BitArray:
    """Convert a single primitive value of the given type to a fixed-length bit representation."""
    assert value_type in ["int", "uint", "double"], f"unsupported primitive type: {value_type}"
    if value_type == "double":
        assert isinstance(value, float)
        assert num_bits == 64, "double must be represented with 64 bits"
        return double_pack(value)
    assert isinstance(value, int)
    signed = value_type == "int"
    return integer_pack(value, num_bits, signed)


def numeric_unpack(bits: BitArray, value_type: str) -> int | float:
    """Convert a BitArray to a single primitive value of the given type."""
    assert value_type in ["int", "uint", "double"], f"unsupported primitive type: {value_type}"
    if value_type == "double":
        return double_unpack(bits)
    signed = value_type == "int"
    return integer_unpack(bits, signed)
