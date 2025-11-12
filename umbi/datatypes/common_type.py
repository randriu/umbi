"""
Data types and type identifiers used throughout umbi. This module centralizes:
1. String identifiers for common value types in umbfiles
2. Python type aliases for these common types
3. Functions to check and assert type names and instances
"""

from .json import is_json_instance

from fractions import Fraction
import enum

class CommonType(str, enum.Enum):
    """String literals for common datatypes."""
    BYTES = "bytes"
    BOOLEAN = "bool"

    INT = "int"
    UINT = "uint"

    INT16 = "int16"
    UINT16 = "uint16"
    INT32 = "int32"
    UINT32 = "uint32"
    INT64 = "int64"
    UINT64 = "uint64"

    DOUBLE = "double"
    RATIONAL = "rational"

    DOUBLE_INTERVAL = "double-interval"
    RATIONAL_INTERVAL = "rational-interval"

    STRING = "string"
    JSON = "json"

    STRUCT = "struct"

""" Alias for primitive numeric types. """
NumericPrimitive = int | float | Fraction

def is_instance_of_common_type(value: object, type: CommonType) -> bool:
    """Check if a value is an instance of the given common type."""
    if type == CommonType.BOOLEAN:
        return isinstance(value, bool)
    elif is_integer_type(type):
        return isinstance(value, int)
    elif type == CommonType.DOUBLE:
        return isinstance(value, float) or isinstance(value, int) # allow promotion from int to float
    elif type == CommonType.RATIONAL:
        return isinstance(value, Fraction)
    elif is_interval_type(type):
        from .interval import Interval
        return isinstance(value, Interval)
    elif type == CommonType.STRUCT:
        from .struct import StructType
        return isinstance(value, StructType)
    elif type == CommonType.STRING:
        return isinstance(value, str)
    elif type == CommonType.JSON:
        return is_json_instance(value)
    else:
        raise ValueError(f"unsupported common type: {type}")


### integers

def is_fixed_size_integer_type(type: CommonType) -> bool:
    return type in [
        CommonType.INT16, CommonType.UINT16,
        CommonType.INT32, CommonType.UINT32,
        CommonType.INT64, CommonType.UINT64
    ]

def is_variable_size_integer_type(type: CommonType) -> bool:
    return type in [
        CommonType.INT, CommonType.UINT
    ]

def is_integer_type(type: CommonType) -> bool:
    return is_variable_size_integer_type(type) or is_fixed_size_integer_type(type)

def assert_integer_type(type: CommonType):
    assert is_integer_type(type), f"not an integer type: {type}"

def integer_type_signed(type: CommonType) -> bool:
    assert_integer_type(type)
    return type.name.startswith("i")


### interval types (defined in interval.py)


def is_interval_type(type: CommonType) -> bool:
    return type in [
        CommonType.DOUBLE_INTERVAL,
        CommonType.RATIONAL_INTERVAL
    ]

def assert_interval_type(type: CommonType):
    assert is_interval_type(type), f"not an interval type: {type}"

def interval_base_type(type: CommonType) -> CommonType:
    assert_interval_type(type)
    return {
        CommonType.DOUBLE_INTERVAL: CommonType.DOUBLE,
        CommonType.RATIONAL_INTERVAL: CommonType.RATIONAL,
    }[type]


# def is_numeric_type(type: CommonType) -> bool:
#     """Check if the given common type is a numeric type (including intervals)."""
#     return is_integer_type(type) or type in [
#         CommonType.DOUBLE,
#         CommonType.RATIONAL,
#         CommonType.DOUBLE_INTERVAL,
#         CommonType.RATIONAL_INTERVAL
#     ]