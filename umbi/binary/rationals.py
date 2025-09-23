from fractions import Fraction
from typing import Optional

from bitstring import BitArray

from .primitives import *


def normalize_rational(value: Fraction) -> Fraction:
    """Ensure that the denominator of a fraction is non-negative."""
    if value.denominator < 0:
        value = Fraction(-value.numerator, -value.denominator)
    return value


def integer_size(value: int) -> int:
    """Return the number of bytes needed to represent an integer value, rounded up to the nearest multiple of 8."""
    num_bytes = (value.bit_length() + 7) // 8
    if num_bytes % 8 != 0:
        num_bytes += 8 - (num_bytes % 8)
    return num_bytes


def rational_size(value: Fraction) -> int:
    """Return the number of bytes needed to represent a fraction."""
    return max(integer_size(value.numerator), integer_size(value.denominator))


def rational_to_bytes(value: Fraction, term_size: Optional[int] = None, little_endian: bool = True) -> bytes:
    """
    Convert a fraction to a bytestring. Both numberator and denominator are encoded as signed and unsigned integers, respectively, and have the same size.
    :param term_size: (optional) maximum size in bytes for numerator/denominator; if not provided, the size is determined automatically
    """
    value = normalize_rational(value)
    if term_size is None:
        term_size = rational_size(value) // 2
    byteorder = "little" if little_endian else "big"
    numerator_bytes = value.numerator.to_bytes(term_size, byteorder=byteorder, signed=True)
    denominator_bytes = value.denominator.to_bytes(term_size, byteorder=byteorder, signed=False)
    return numerator_bytes + denominator_bytes


def bytes_to_rational(data: bytes, little_endian: bool = True) -> Fraction:
    """Convert a bytestring to a fraction. The bytestring must have even length, with the first half representing the numerator as a signed integer and the second half representing the denominator as an unsigned integer."""
    assert len(data) % 2 == 0, "rational data must have even length"
    mid = len(data) // 2
    byteorder = "little" if little_endian else "big"
    numerator = int.from_bytes(data[:mid], byteorder=byteorder, signed=True)
    denominator = int.from_bytes(data[mid:], byteorder=byteorder, signed=False)
    return Fraction(numerator, denominator)


def rational_pack(value: Fraction) -> bytes:
    """Pack a fraction into a length-prefixed bytestring."""
    prefix_size = 2  # size of uint16
    value = normalize_rational(value)
    term_size = rational_size(value) // 2
    prefix_bytes = uint_to_bytes(term_size, prefix_size)
    numerator_bytes = int_to_bytes(value.numerator, term_size)
    denominator_bytes = uint_to_bytes(value.denominator, term_size)
    return prefix_bytes + numerator_bytes + denominator_bytes


def rational_unpack(bytestring: bytes) -> tuple[Fraction, bytes]:
    """
    Unpack a length-prefixed bytestring into a fraction.
    :return: the unpacked fraction
    :return: the remainder of the bytestring after extracting the fraction
    """
    prefix_size = 2  # size of uint16
    prefix, bytestring = split_bytes(bytestring, prefix_size)
    term_size = bytes_to_uint(prefix)
    numerator, bytestring = split_bytes(bytestring, term_size)
    numerator = bytes_to_int(numerator)
    denominator, remainder = split_bytes(bytestring, term_size)
    denominator = bytes_to_uint(denominator)
    rational = Fraction(numerator, denominator)
    return rational, remainder
