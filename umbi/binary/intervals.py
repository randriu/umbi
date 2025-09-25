"""Utilities for de()serializing intervals."""

from fractions import Fraction

from .rationals import rational_size, rational_to_bytes, bytes_to_rational
from .floats import double_to_bytes, bytes_to_double


def interval_to_bytes(value: tuple[object, object], value_type: str, little_endian: bool = True) -> bytes:
    """Convert a tuple of two integers into a bytestring representing an interval."""
    assert len(value) == 2, "interval value must be a pair"
    base_value_type = value_type.replace("-interval", "")
    assert base_value_type in {"rational", "double"}, f"unsupported base value type for interval: {base_value_type}"
    lower, upper = value
    if base_value_type == "rational":
        assert isinstance(lower, Fraction) and isinstance(upper, Fraction)
        # ensure both rationals use the same size for numerator and denominator
        term_size = max(rational_size(lower), rational_size(upper)) // 2
        lower = rational_to_bytes(lower, term_size, little_endian)
        upper = rational_to_bytes(upper, term_size, little_endian)
    else:
        assert base_value_type == "double"
        assert isinstance(lower, float) and isinstance(upper, float)
        lower = double_to_bytes(lower, little_endian)
        upper = double_to_bytes(upper, little_endian)
    return lower + upper


def bytes_to_interval(data: bytes, value_type: str, little_endian: bool = True) -> tuple[object, object]:
    """Convert a bytestring representing an interval into a tuple of two base values."""
    assert len(data) % 2 == 0, "interval data must have even length"
    mid = len(data) // 2
    base_value_type = value_type.replace("-interval", "")
    assert base_value_type in {"rational", "double"}, f"unsupported base value type for interval: {base_value_type}"
    lower, upper = data[:mid], data[mid:]
    converter = {
        "rational": bytes_to_rational,
        "double": bytes_to_double,
    }[base_value_type]
    lower = converter(lower, little_endian)
    upper = converter(upper, little_endian)
    return (lower, upper)
