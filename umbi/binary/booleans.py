"""
Utilities for (de)serializing booleans and bitvectors.
"""

from typing import Optional
from bitstring import BitArray


def bytes_to_bitvector(bytestring: bytes) -> list[bool]:
    """Convert a bytestring representing a bitvector into a list of booleans."""
    return [(byte >> bit) & 1 == 1 for byte in bytestring for bit in range(8)]


def bitvector_to_bytes(bitvector: list[bool]) -> bytes:
    """Convert a list of booleans representing a bitvector into a bytestring."""
    byte_array = bytearray()
    for i in range(0, len(bitvector), 8):
        byte = sum((1 << j) for j in range(8) if i + j < len(bitvector) and bitvector[i + j])
        byte_array.append(byte)
    return bytes(byte_array)


def boolean_pack(value: bool, num_bits: Optional[int] = None) -> BitArray:
    """Convert a single boolean value to a fixed-length bit representation."""
    value_uint = 1 if value else 0
    if num_bits is None:
        num_bits = 1
    return BitArray(uint=value_uint, length=num_bits)


def boolean_unpack(bits: BitArray) -> bool:
    """Convert a BitArray to a single boolean value."""
    return bits.uint != 0
