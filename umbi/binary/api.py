"""
A convenient interface for all (de)serializers in this package.
"""

from .booleans import *
from .intervals import *
from .primitives import *
from .rationals import *
from .strings import *


def standard_value_type_size(value_type: str) -> int:
    """Return the number of bytes needed to represent a value of the given type."""
    if "-interval" in value_type:
        base_value_type = value_type.replace("-interval", "")
        return 2 * standard_value_type_size(base_value_type)
    if value_type == "rational":
        # for rationals, the standard size is 8+8 bytes
        return standard_value_type_size("int64") + standard_value_type_size("uint64")
    return primitive_value_type_size(value_type)


def value_to_bytes(value: str | int | float | Fraction | tuple, value_type: str, little_endian: bool = True) -> bytes:
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
    else:
        assert isinstance(value, (int, float)), "primitive value must be an int or float"
        return primitive_to_bytes(value, value_type, little_endian)


def bytes_to_value(data: bytes, value_type: str, little_endian: bool = True) -> str | int | float | Fraction | tuple:
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
    else:
        return bytes_to_primitive(data, value_type, little_endian)


# def value_to_bits(
#     value: str | bool | int | float | Fraction, value_type: str, num_bits: Optional[int] = None
# ) -> BitArray:
#     """
#     Convert a value of a given type to a fixed-length bit representation.
#     :param value_type: one of {string,int,uint,double,rational}
#     """
#     if value_type == "string":
#         assert isinstance(value, str), "string value must be a str"
#         return string_to_bits(value)
#     elif value_type == "bool":
#         assert isinstance(value, bool), "boolean value must be a bool"
#         return bool_to_bits(value,num_bits)
#     elif value_type == "rational":
#         assert isinstance(value, Fraction), "rational value must be a Fraction"
#         return fraction_to_bits(value)
#     else:
#         assert isinstance(value, (int, float)), "primitive value must be an int or float"
#         assert num_bits is not None, "num_bits must be specified for primitive types"
#         return primitive_to_bits(value, value_type, num_bits)


# def bits_to_value(bits: BitArray, value_type: str) -> str | bool | int | float | Fraction:
#     """
#     Convert a fixed-length bit representation to a single value of the given type.
#     :param value_type: one of {string,int,uint,double,rational}
#     """
#     if value_type == "string":
#         return bits_to_string(bits)
#     elif value_type == "bool":
#         return bits_to_bool(bits)
#     elif value_type == "rational":
#         return bits_to_fraction(bits)
#     else:
#         return bits_to_primitive(bits, value_type)
