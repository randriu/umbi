from fractions import Fraction

from .common_type import (
    CommonType,
    interval_base_type,
    is_integer_type,
    is_interval_type,
)
from .interval import Interval
from .json import is_json_instance
from .struct import StructType

""" Alias for primitive numeric types. """
NumericPrimitive = int | float | Fraction
""" Alias for all numeric types, including intervals. """
Numeric = NumericPrimitive | Interval


def get_instance_type(value: object) -> CommonType:
    """Determine the common type of a given value."""
    if isinstance(value, bool):
        return CommonType.BOOLEAN
    elif isinstance(value, int):
        return CommonType.INT
    elif isinstance(value, float):
        return CommonType.DOUBLE
    elif isinstance(value, Fraction):
        return CommonType.RATIONAL
    elif isinstance(value, Interval):
        if isinstance(value.left, Fraction) or isinstance(value.right, Fraction):
            return CommonType.RATIONAL_INTERVAL
        else:
            return CommonType.DOUBLE_INTERVAL
    elif isinstance(value, str):
        return CommonType.STRING
    elif is_json_instance(value):
        return CommonType.JSON
    elif isinstance(value, StructType):
        return CommonType.STRUCT
    else:
        raise ValueError(f"cannot match value to a common type: {value}")


def is_instance_of_common_type(value: object, type: CommonType) -> bool:
    """Check if a value is an instance of the given common type."""
    value_type = get_instance_type(value)
    if value_type == CommonType.INT:
        # int matches all integer types
        # technically, we don't check the sign of the integer here,
        # e.g. is_instance_of_common_type(-1, CommonType.UINT) -> True
        return is_integer_type(type)
    else:
        return value_type == type


def promote_numeric_primitive(value: NumericPrimitive, target_type: CommonType) -> NumericPrimitive:
    if target_type == CommonType.INT:
        assert isinstance(value, int), f"cannot promote value {value} to int"
        return value
    elif target_type == CommonType.DOUBLE:
        assert isinstance(value, (int, float)), f"cannot promote value {value} to double"
        return float(value)
    else:
        assert target_type == CommonType.RATIONAL, f"unexpected target type: {target_type}"
        if isinstance(value, Fraction):
            return value
        elif isinstance(value, int):
            return Fraction(value, 1)
        elif isinstance(value, float):
            return Fraction.from_float(value)
        else:
            raise ValueError(f"cannot promote value {value} to rational")


def promote_numeric(value: Numeric, target_type: CommonType) -> Numeric:
    """Promote a numeric value to the target type."""
    if not is_interval_type(target_type):
        assert isinstance(value, NumericPrimitive), f"cannot promote interval {value} to primitive type {target_type}"
        return promote_numeric_primitive(value, target_type)
    if isinstance(value, Interval):
        left = value.left
        right = value.right
    else:
        left = right = value
    base_type = interval_base_type(target_type)
    left = promote_numeric_primitive(left, base_type)
    right = promote_numeric_primitive(right, base_type)
    return Interval(left, right)
