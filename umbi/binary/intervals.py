"""Utilities for (de)serializing intervals."""

from fractions import Fraction

import umbi.datatypes
from umbi.datatypes import CommonType, Interval, interval_base_type

from .floats import bytes_to_double, double_to_bytes
from .rationals import bytes_to_rational, num_bytes_for_rational, rational_to_bytes


def interval_to_bytes(interval: Interval, type: CommonType, little_endian: bool = True) -> bytes:
    """Convert an Interval into a bytestring representation."""
    umbi.datatypes.assert_interval_type(type)
    base_type = interval_base_type(type)

    if base_type == CommonType.RATIONAL:
        assert isinstance(interval.left, Fraction) and isinstance(interval.right, Fraction)
        # ensure both rationals use the same size for numerator and denominator
        term_size = (
            max(
                num_bytes_for_rational(interval.left),
                num_bytes_for_rational(interval.right),
            )
            // 2
        )
        lower = rational_to_bytes(interval.left, term_size, little_endian)
        upper = rational_to_bytes(interval.right, term_size, little_endian)
    else:
        assert base_type == CommonType.DOUBLE
        assert isinstance(interval.left, float) and isinstance(interval.right, float)
        lower = double_to_bytes(interval.left, little_endian)
        upper = double_to_bytes(interval.right, little_endian)
    return lower + upper


def bytes_to_interval(data: bytes, type: CommonType, little_endian: bool = True) -> Interval:
    """Convert a bytestring representing an interval into an Interval object."""
    assert len(data) % 2 == 0, "interval data must have even length"
    mid = len(data) // 2
    base_type = interval_base_type(type)
    lower, upper = data[:mid], data[mid:]
    converter = {
        CommonType.DOUBLE: bytes_to_double,
        CommonType.RATIONAL: bytes_to_rational,
    }[base_type]
    lower = converter(lower, little_endian)
    upper = converter(upper, little_endian)
    return Interval(lower, upper)
