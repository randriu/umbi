from fractions import Fraction

from typing import Optional
from bitstring import BitArray

from .primitives import *

def normalize_fraction(value: Fraction) -> Fraction:
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


def fraction_size(value: Fraction) -> int:
    """Return the number of bytes needed to represent a fraction."""
    return max(integer_size(value.numerator), integer_size(value.denominator))


def fraction_to_bytes(value: Fraction, term_size: Optional[int] = None, little_endian: bool = True) -> bytes:
    """
    Convert a fraction to a bytestring. Both numberator and denominator are encoded as signed and unsigned integers, respectively, and have the same size.
    :param term_size: (optional) maximum size in bytes for numerator/denominator; if not provided, the size is determined automatically
    """
    value = normalize_fraction(value)
    if term_size is None:
        term_size = fraction_size(value) // 2
    byteorder = "little" if little_endian else "big"
    numerator_bytes = value.numerator.to_bytes(term_size, byteorder=byteorder, signed=True)
    denominator_bytes = value.denominator.to_bytes(term_size, byteorder=byteorder, signed=False)
    return numerator_bytes + denominator_bytes


def bytes_to_fraction(data: bytes, little_endian: bool = True) -> Fraction:
    """Convert a bytestring to a fraction. The bytestring must have even length, with the first half representing the numerator as a signed integer and the second half representing the denominator as an unsigned integer."""
    assert len(data) % 2 == 0, "rational data must have even length"
    mid = len(data) // 2
    byteorder = "little" if little_endian else "big"
    numerator = int.from_bytes(data[:mid], byteorder=byteorder, signed=True)
    denominator = int.from_bytes(data[mid:], byteorder=byteorder, signed=False)
    return Fraction(numerator, denominator)


def fraction_to_bits(value: Fraction, little_endian: bool = True) -> BitArray:
    value = normalize_fraction(value)
    term_size = fraction_size(value) // 2
    term_size_bits = term_size * 8
    size_bits = uint_to_bits(term_size, 16)
    numerator_bits = int_to_bits(value.numerator, term_size_bits)
    denominator_bits = uint_to_bits(value.denominator, term_size_bits)
    return size_bits + numerator_bits + denominator_bits


def bits_to_fraction(bits: BitArray) -> Fraction:
    prefix_size = 16
    assert len(bits) >= prefix_size, "not enough bits to read rational size"
    fraction_bits = bits[prefix_size:]
    term_size = bits[:prefix_size].uint
    term_size_bits = term_size * 8
    expected_length = 2 * term_size_bits
    assert len(fraction_bits) == expected_length, f"expected {expected_length} bits for rational, got {len(fraction_bits)}"
    numerator = bits_to_int(fraction_bits[:term_size_bits])
    denominator = bits_to_uint(fraction_bits[term_size_bits:])
    return Fraction(numerator, denominator)

