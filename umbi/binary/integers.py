"""
Utilities for (de)serializing integers and floats.
"""

from bitstring import BitArray


def assert_integer_range(value: int, num_bits: int, signed: bool = True):
    """Assert that an integer fits in the given number of bits."""
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
    assert_integer_range(value, num_bytes * 8, signed)
    return value.to_bytes(num_bytes, byteorder="little" if little_endian else "big", signed=signed)


def bytes_to_integer(data: bytes, signed: bool = True, little_endian: bool = True) -> int:
    return int.from_bytes(data, byteorder="little" if little_endian else "big", signed=signed)


def fixed_size_integer_base_and_size(value_type: str) -> tuple[str, int]:
    fixed_size_integers = {"int16", "uint16", "int32", "int64", "uint32", "uint64"}
    if value_type not in fixed_size_integers:
        raise ValueError(f"expected value type one of {list(fixed_size_integers)} but is {value_type}")
    base_type = "int" if value_type.startswith("int") else "uint"
    num_bytes = int(value_type[-2:]) // 8
    return base_type, num_bytes


def fixed_size_integer_to_bytes(value: int, value_type: str, little_endian: bool = True) -> bytes:
    """Convert a fixed-size integer value of the given type to a bytestring."""
    base_type, num_bytes = fixed_size_integer_base_and_size(value_type)
    return integer_to_bytes(value, num_bytes, signed=(base_type == "int"), little_endian=little_endian)


def bytes_to_fixed_size_integer(data: bytes, value_type: str, little_endian: bool = True) -> int:
    """Convert a binary string to a fixed-size integer value of the given type."""
    base_type, num_bytes = fixed_size_integer_base_and_size(value_type)
    assert (
        len(data) == num_bytes
    ), f"data length {len(data)} does not match expected size {num_bytes} for type {value_type}"
    return bytes_to_integer(data, signed=(base_type == "int"), little_endian=little_endian)


def integer_pack(value: int, num_bits: int, signed: bool = True) -> BitArray:
    """Convert a single integer value to a fixed-length bit representation."""
    assert_integer_range(value, num_bits, signed)
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
