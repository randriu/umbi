"""Utilities for (de)serializing intervals."""

from fractions import Fraction

from .floats import bytes_to_double, double_to_bytes
from .rationals import bytes_to_rational, rational_size, rational_to_bytes

# Type alias for numeric types (that can be used in intervals)
Numeric = int | float | Fraction

class Interval:
    """Represents a numeric interval where left <= right."""
    
    def __init__(self, left: Numeric, right: Numeric) -> None:
        self.left = left
        self.right = right
        self.validate()
    
    def validate(self) -> None:
        """Validate that the interval is well-formed."""
        if self.left > self.right:
            raise ValueError(f"left bound {self.left} must be <= right bound {self.right}")

    def __repr__(self) -> str:
        return f"Interval({self.left}, {self.right})"
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Interval):
            return False
        return self.left == other.left and self.right == other.right
    
    def __contains__(self, value: Numeric) -> bool:
        return self.left <= value <= self.right
    
    def overlaps(self, other: 'Interval') -> bool:
        """Check if this interval overlaps with another interval."""
        return self.left <= other.right and other.left <= self.right


def assert_continuous_datatype(value_type: str):
    """Assert that the given value type is a continuous datatype (rational or double)."""
    continuous_datatypes = {"rational", "double"}
    if value_type not in continuous_datatypes:
        raise ValueError(f"expected value type one of {list(continuous_datatypes)} but is {value_type}")

def interval_to_bytes(interval: Interval, value_type: str, little_endian: bool = True) -> bytes:
    """Convert an Interval into a bytestring representation."""
    base_value_type = value_type.replace("-interval", "")
    assert_continuous_datatype(base_value_type)
    
    if base_value_type == "rational":
        assert isinstance(interval.left, Fraction) and isinstance(interval.right, Fraction)
        # ensure both rationals use the same size for numerator and denominator
        term_size = max(rational_size(interval.left), rational_size(interval.right)) // 2
        lower = rational_to_bytes(interval.left, term_size, little_endian)
        upper = rational_to_bytes(interval.right, term_size, little_endian)
    else:
        assert base_value_type == "double"
        assert isinstance(interval.left, float) and isinstance(interval.right, float)
        lower = double_to_bytes(interval.left, little_endian)
        upper = double_to_bytes(interval.right, little_endian)
    return lower + upper


def bytes_to_interval(data: bytes, value_type: str, little_endian: bool = True) -> Interval:
    """Convert a bytestring representing an interval into an Interval object."""
    assert len(data) % 2 == 0, "interval data must have even length"
    mid = len(data) // 2
    base_value_type = value_type.replace("-interval", "")
    assert_continuous_datatype(base_value_type)
    lower, upper = data[:mid], data[mid:]
    converter = {
        "rational": bytes_to_rational,
        "double": bytes_to_double,
    }[base_value_type]
    lower = converter(lower, little_endian)
    upper = converter(upper, little_endian)
    return Interval(lower, upper)
