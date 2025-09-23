"""Utilities for de()serializing intervals."""

import fractions

from bitstring import BitArray

from .primitives import *
from .rationals import *


def interval_to_bytes(value: tuple[object, object], value_type: str, little_endian: bool = True) -> bytes:
    """Convert a tuple of two integers into a bytestring representing an interval."""
    assert len(value) == 2, "interval value must be a pair"
    base_value_type = value_type.replace("-interval", "")
    if base_value_type == "rational":
        assert all(isinstance(v, fractions.Fraction) for v in value), "expected a pair of fractions"
        # ensure both rationals use the same size for numerator and denominator
        term_size = max(rational_size(v) for v in value) // 2
        lower = rational_to_bytes(value[0], term_size, little_endian)
        upper = rational_to_bytes(value[1], term_size, little_endian)
    else:
        assert all(isinstance(v, int | float) for v in value), "expected a pair of numbers"
        lower = primitive_to_bytes(value[0], base_value_type, little_endian)
        upper = primitive_to_bytes(value[1], base_value_type, little_endian)
    return lower + upper


def bytes_to_interval(data: bytes, value_type: str, little_endian: bool = True) -> tuple[object, object]:
    """Convert a bytestring representing an interval into a tuple of two base values."""
    assert len(data) % 2 == 0, "interval data must have even length"
    mid = len(data) // 2
    base_value_type = value_type.replace("-interval", "")
    lower, upper = None, None
    if base_value_type == "rational":
        lower = bytes_to_rational(data[:mid], little_endian)
        upper = bytes_to_rational(data[mid:], little_endian)
    else:
        lower = bytes_to_primitive(data[:mid], base_value_type, little_endian)
        upper = bytes_to_primitive(data[mid:], base_value_type, little_endian)
    return (lower, upper)
