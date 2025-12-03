from fractions import Fraction

from .common_type import (
    CommonType,
    is_integer_type,
)
from .interval import Interval
from .json import is_json_instance

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
