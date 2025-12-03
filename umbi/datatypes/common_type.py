"""
Data types and type identifiers used throughout umbi. This module centralizes:
1. String identifiers for common value types in umbfiles
2. Python type aliases for these common types
3. Functions to check and assert type names and instances
"""

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


### integers


def is_fixed_size_integer_type(type: CommonType) -> bool:
    return type in [
        CommonType.INT16,
        CommonType.UINT16,
        CommonType.INT32,
        CommonType.UINT32,
        CommonType.INT64,
        CommonType.UINT64,
    ]


def is_variable_size_integer_type(type: CommonType) -> bool:
    return type in [CommonType.INT, CommonType.UINT]


def is_integer_type(type: CommonType) -> bool:
    return is_variable_size_integer_type(type) or is_fixed_size_integer_type(type)


def assert_integer_type(type: CommonType):
    assert is_integer_type(type), f"not an integer type: {type}"


def integer_type_signed(type: CommonType) -> bool:
    assert_integer_type(type)
    return type.name.startswith("i")


### interval types (defined in interval.py)


def is_interval_type(type: CommonType) -> bool:
    return type in [CommonType.DOUBLE_INTERVAL, CommonType.RATIONAL_INTERVAL]


def assert_interval_type(type: CommonType):
    assert is_interval_type(type), f"not an interval type: {type}"


def interval_base_type(type: CommonType) -> CommonType:
    assert_interval_type(type)
    return {
        CommonType.DOUBLE_INTERVAL: CommonType.DOUBLE,
        CommonType.RATIONAL_INTERVAL: CommonType.RATIONAL,
    }[type]


def is_numeric_type(type: CommonType) -> bool:
    """Check if the given common type is a numeric type (including intervals)."""
    return type in [
        CommonType.INT,
        CommonType.DOUBLE,
        CommonType.RATIONAL,
        CommonType.DOUBLE_INTERVAL,
        CommonType.RATIONAL_INTERVAL,
    ]
