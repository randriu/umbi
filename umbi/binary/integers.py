"""
(De)serializers for integers.
"""
import umbi.datatypes
from umbi.datatypes import CommonType

from bitstring import BitArray

def num_bits_for_integer(value: int, signed: bool = True, round_up: bool = True) -> int:
    """
    Return the number of bits needed to represent an integer value.
    :param signed: if True, the integer is signed
    :param round_up: if True, the number of bits is rounded up to the nearest multiple of 8
    """
    if not signed:
        num_bits = value.bit_length()
    else:
        if value >= 0:
            num_bits = value.bit_length()
        else:
            num_bits = (-value-1).bit_length()
        num_bits += 1 # add sign bit
    if round_up and num_bits % 8 != 0:
        num_bits += 8 - (num_bits % 8)
    return num_bits


def num_bytes_for_integer(value: int, signed: bool = True, round_up: bool = True) -> int:
    """
    Return the number of bytes needed to represent an integer value.
    :param round_up: if True, the number of bytes is rounded up to the nearest multiple of 8
    """
    num_bytes = num_bits_for_integer(value, signed=signed, round_up=True) // 8 # round up to full bytes
    if round_up and num_bytes % 8 != 0:
        num_bytes += 8 - (num_bytes % 8)
    return num_bytes


def num_bytes_for_fixed_size_integer(type: CommonType) -> int:
    """Return the size in bytes of a fixed-size integer type."""
    assert umbi.datatypes.is_fixed_size_integer_type(type), f"not a fixed-size integer type: {type}"
    size_map = {
        CommonType.INT16: 2, CommonType.UINT16: 2,
        CommonType.INT32: 4, CommonType.UINT32: 4,
        CommonType.INT64: 8, CommonType.UINT64: 8
    }
    return size_map[type]



def assert_integer_fits(
        value: int, signed: bool = True, num_bits: int | None = None, num_bytes: int | None = None
):
    """Assert that an integer fits in the given number of bits/bytes."""
    assert (num_bits is None) != (num_bytes is None), "either num_bits or num_bytes must be provided, but not both"
    if num_bits is None:
        assert num_bytes is not None # for mypy
        num_bits = num_bytes * 8
    if signed:
        max_value = (1 << (num_bits - 1)) - 1
        min_value = -(1 << (num_bits - 1))
    else:
        max_value = (1 << num_bits) - 1
        min_value = 0
    if not (min_value <= value <= max_value):
        raise ValueError(
            f"integer value {value} is out of range for a {num_bits}-bit {'signed' if signed else 'unsigned'} integer [{min_value}, {max_value}]"
        )


def integer_to_bytes(value: int, num_bytes: int, signed: bool = True, little_endian: bool = True) -> bytes:
    assert_integer_fits(value, signed=signed, num_bytes=num_bytes)
    return value.to_bytes(num_bytes, byteorder="little" if little_endian else "big", signed=signed)


def bytes_to_integer(data: bytes, signed: bool = True, little_endian: bool = True) -> int:
    return int.from_bytes(data, byteorder="little" if little_endian else "big", signed=signed)


def fixed_size_integer_to_bytes(value: int, value_type: CommonType, little_endian: bool = True) -> bytes:
    signed = umbi.datatypes.integer_type_signed(value_type)
    num_bytes = num_bytes_for_fixed_size_integer(value_type)
    return integer_to_bytes(value, num_bytes, signed=signed, little_endian=little_endian)


def bytes_to_fixed_size_integer(data: bytes, value_type: CommonType, little_endian: bool = True) -> int:
    """Convert a binary string to a fixed-size integer value of the given type."""
    signed = umbi.datatypes.integer_type_signed(value_type)
    num_bytes = num_bytes_for_fixed_size_integer(value_type)
    assert (
        len(data) == num_bytes
    ), f"data length {len(data)} does not match expected size {num_bytes} for type {value_type}"
    return bytes_to_integer(data, signed=signed, little_endian=little_endian)


def integer_pack(value: int, num_bits: int, signed: bool = True) -> BitArray:
    """Convert a single integer value to a fixed-length bit representation."""
    assert_integer_fits(value, signed=signed, num_bits=num_bits)
    if signed:
        return BitArray(int=value, length=num_bits)
    else:
        return BitArray(uint=value, length=num_bits)


def integer_unpack(bits: BitArray, signed: bool = True) -> int:
    """Convert a BitArray to a single integer value."""
    if signed:
        return bits.int
    else:
        return bits.uint
