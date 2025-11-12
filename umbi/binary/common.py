"""
(De)serialization of common types.
"""

import umbi.datatypes
from umbi.datatypes import CommonType, Numeric, JsonLike

from .integers import num_bytes_for_fixed_size_integer, fixed_size_integer_to_bytes, bytes_to_fixed_size_integer
from .floats import double_to_bytes, bytes_to_double
from .rationals import rational_to_bytes, bytes_to_rational
from .intervals import interval_to_bytes, bytes_to_interval
from .strings import string_to_bytes, bytes_to_string
from .jsons import json_to_bytes, bytes_to_json

from typing import no_type_check

def num_bytes_for_common_type(type: CommonType) -> int:
    """Return the number of bytes needed to represent a value of the given type."""
    if umbi.datatypes.is_fixed_size_integer_type(type):
        return num_bytes_for_fixed_size_integer(type)
    if type == CommonType.DOUBLE:
        return 8  # size of double
    if type == CommonType.RATIONAL:
        return num_bytes_for_fixed_size_integer(CommonType.INT64) + num_bytes_for_fixed_size_integer(CommonType.UINT64)
    if umbi.datatypes.is_interval_type(type):
        base_value_type = umbi.datatypes.interval_base_type(type)
        return 2 * num_bytes_for_common_type(base_value_type)
    raise ValueError(f"unsupported common value type: {type}")


@no_type_check
def common_value_to_bytes(value: Numeric | str | JsonLike, type: CommonType, little_endian: bool = True) -> bytes:
    """Convert a value of a given type to a bytestring."""
    assert umbi.datatypes.is_instance_of_common_type(value, type), f"value {value} does not match type {type}"
    if umbi.datatypes.is_fixed_size_integer_type(type):
        return fixed_size_integer_to_bytes(value, type, little_endian)
    elif type == CommonType.DOUBLE:
        return double_to_bytes(value, little_endian=little_endian)
    elif type == CommonType.RATIONAL:
        return rational_to_bytes(value, little_endian=little_endian)
    elif umbi.datatypes.is_interval_type(type):
        return interval_to_bytes(value, type, little_endian=little_endian)
    elif type == CommonType.STRING:
        return string_to_bytes(value)
    elif type == CommonType.JSON:
        return json_to_bytes(value)
    else:
        raise ValueError(f"unsupported common value type: {type}")


def bytes_to_common_value(data: bytes, type: CommonType, little_endian: bool = True) -> Numeric | str | JsonLike:
    """Convert a binary string to a single value of the given common type."""
    if umbi.datatypes.is_fixed_size_integer_type(type):
        return bytes_to_fixed_size_integer(data, type, little_endian=little_endian)
    elif type == CommonType.DOUBLE:
        return bytes_to_double(data, little_endian=little_endian)
    elif type == CommonType.RATIONAL:
        return bytes_to_rational(data, little_endian=little_endian)
    elif umbi.datatypes.is_interval_type(type):
        return bytes_to_interval(data, type, little_endian=little_endian)
    elif type == CommonType.STRING:
        return bytes_to_string(data)
    elif type == CommonType.JSON:
        return bytes_to_json(data)
    else:
        raise ValueError(f"unsupported common value type: {type}")
