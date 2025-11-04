"""
Utilities for (de)serializing fractions.
"""

from fractions import Fraction
from typing import Optional

from .integers import *
from .utils import split_bytes


def normalize_rational(value: Fraction) -> Fraction:
    """Ensure that the denominator of a fraction is non-negative."""
    if value.denominator < 0:
        value = Fraction(-value.numerator, -value.denominator)
    return value


def rational_size(value: Fraction) -> int:
    """Return the number of bytes needed to represent a fraction."""
    return max(integer_size(value.numerator), integer_size(value.denominator))


def rational_to_bytes(value: Fraction, term_size: Optional[int] = None, little_endian: bool = True) -> bytes:
    """
    Convert a fraction to a bytestring. Both numberator and denominator are encoded as signed and unsigned integers, respectively, and have the same size.
    :param term_size: (optional) maximum size in bytes for numerator/denominator; if not provided, the size is determined automatically
    """
    value = normalize_rational(value)
    minimal_term_size = rational_size(value) // 2
    if term_size is None:
        term_size = minimal_term_size
    elif term_size < minimal_term_size:
        raise ValueError(
            f"term_size {term_size} is too small to represent the rational {value}, which requires at least {minimal_term_size} bytes per term"
        )
    numerator_bytes = integer_to_bytes(value.numerator, num_bytes=term_size, signed=True, little_endian=little_endian)
    denominator_bytes = integer_to_bytes(
        value.denominator, num_bytes=term_size, signed=False, little_endian=little_endian
    )
    return numerator_bytes + denominator_bytes


def bytes_to_rational(data: bytes, little_endian: bool = True) -> Fraction:
    """Convert a bytestring to a fraction. The bytestring must have even length, with the first half representing the numerator as a signed integer and the second half representing the denominator as an unsigned integer."""
    assert len(data) % 2 == 0, "rational data must have even length"
    mid = len(data) // 2
    numerator = bytes_to_integer(data[:mid], signed=True, little_endian=little_endian)
    denominator = bytes_to_integer(data[mid:], signed=False, little_endian=little_endian)
    return Fraction(numerator, denominator)


def rational_pack(value: Fraction) -> bytes:
    """Pack a fraction into a length-prefixed bytestring."""
    value = normalize_rational(value)
    rational_bytes = rational_to_bytes(value)
    term_size = len(rational_bytes) // 2
    prefix_bytes = integer_to_bytes(term_size, num_bytes=2, signed=False)  # store as uint16
    return prefix_bytes + rational_bytes


def rational_unpack(bytestring: bytes) -> tuple[Fraction, bytes]:
    """
    Unpack a length-prefixed bytestring into a fraction.
    :return: the unpacked fraction
    :return: the remainder of the bytestring after extracting the fraction
    """
    prefix, bytestring = split_bytes(bytestring, 2)  # read as uint16
    term_size = bytes_to_integer(prefix, signed=False)
    rational_bytes, remainder = split_bytes(bytestring, term_size * 2)
    rational = bytes_to_rational(rational_bytes)
    return rational, remainder
