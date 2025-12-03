from fractions import Fraction

from .common_type import (
    CommonType,
    is_interval_type,
    interval_base_type,
    is_numeric_type,
)
from .vector import vector_element_types
from .interval import Interval
from .utils import NumericPrimitive, Numeric


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
            print(f"promoting float {value} to rational {Fraction.from_float(value)}")
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


def can_promote_numeric_to(types: set[CommonType]) -> CommonType:
    """Determine the common numeric type from a set of numeric types. Used for type promotion."""
    if len(types) == 0:
        raise ValueError("cannot determine common numeric type of empty set")
    if any(not is_numeric_type(t) for t in types):
        raise ValueError(f"non-numeric types found in set: {types}")
    if CommonType.RATIONAL_INTERVAL in types:
        return CommonType.RATIONAL_INTERVAL
    elif CommonType.DOUBLE_INTERVAL in types:
        if CommonType.RATIONAL in types:
            return CommonType.RATIONAL_INTERVAL
        else:
            return CommonType.DOUBLE_INTERVAL
    elif CommonType.RATIONAL in types:
        return CommonType.RATIONAL
    elif CommonType.DOUBLE in types:
        return CommonType.DOUBLE
    else:  # CommonType.INT in types
        return CommonType.INT


def can_promote_to(types: set[CommonType]) -> CommonType:
    """Determine the common type from a set of types. Used for type promotion."""
    if len(types) == 0:
        raise ValueError("cannot determine common type of empty set")
    if CommonType.STRING in types:
        return CommonType.STRING

    if len(types) == 1:
        return types.pop()
    # currently only numeric types are supported for promotion
    return can_promote_numeric_to(types)


def can_promote_vector_to(vector: list) -> CommonType:
    """Determine the common type to which all elements in the vector can be promoted."""
    if len(vector) == 0:
        return CommonType.INT  # whatever
    types = vector_element_types(vector)
    return can_promote_numeric_to(types)


def promote_to_vector_of_numeric_primitive(vector: list, target_type: CommonType) -> list:
    return [promote_numeric_primitive(elem, target_type) for elem in vector]


def promote_to_vector_of_numeric(vector: list, target_type: CommonType) -> list:
    return [promote_numeric(elem, target_type) for elem in vector]


def promote_vector(vector: list) -> list:
    """Promote a vector of numeric values to a common type."""
    target_type = can_promote_vector_to(vector)
    return promote_to_vector_of_numeric(vector, target_type)
