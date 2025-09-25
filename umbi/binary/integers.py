"""
Utilities for (de)serializing integers and floats.
"""

from bitstring import BitArray


def check_int_range(value: int, num_bits: int):
    max_value = (1 << (num_bits - 1)) - 1
    min_value = -(1 << (num_bits - 1))
    if not (min_value <= value <= max_value):
        raise ValueError(f"integer value {value} is out of range for a {num_bits}-bit int [{min_value}, {max_value}]")

def check_uint_range(value: int, num_bits: int):
    max_value = (1 << num_bits) - 1
    min_value = 0
    if not (min_value <= value <= max_value):
        raise ValueError(f"integer value {value} is out of range for a {num_bits}-bit uint [{min_value}, {max_value}]")


def int_to_bytes(value: int, num_bytes: int, little_endian: bool = True) -> bytes:
    check_int_range(value, num_bytes * 8)
    return value.to_bytes(num_bytes, byteorder="little" if little_endian else "big", signed=True)

def uint_to_bytes(value: int, num_bytes: int, little_endian: bool = True) -> bytes:
    check_uint_range(value, num_bytes * 8)
    return value.to_bytes(num_bytes, byteorder="little" if little_endian else "big", signed=False)

def bytes_to_int(data: bytes, little_endian: bool = True) -> int:
    return int.from_bytes(data, byteorder="little" if little_endian else "big", signed=True)

def bytes_to_uint(data: bytes, little_endian: bool = True) -> int:
    return int.from_bytes(data, byteorder="little" if little_endian else "big", signed=False)



def fixed_size_integer_base_and_size(value_type: str) -> tuple[str, int]:
    fixed_size_integers = {"int16", "uint16", "int32", "int64", "uint32", "uint64"}
    if value_type not in fixed_size_integers:
        raise ValueError(f"value type must be one of {list(fixed_size_integers)} but is {value_type}")
    if value_type.startswith("int"):
        base_type = "int"
    else:
        base_type = "uint"
    num_bytes = int(value_type[-2:]) // 8
    return base_type, num_bytes

def fixed_size_integer_to_bytes(value: int, value_type: str, little_endian: bool = True) -> bytes:
    """Convert a single fixed-size integer value of the given type to a bytestring."""
    base_type, num_bytes = fixed_size_integer_base_and_size(value_type)
    method = int_to_bytes if base_type == "int" else uint_to_bytes
    return method(value, num_bytes, little_endian)

def bytes_to_fixed_size_integer(data: bytes, value_type: str, little_endian: bool = True) -> int:
    """Convert a binary string to a single fixed-size integer value of the given type."""
    base_type, num_bytes = fixed_size_integer_base_and_size(value_type)
    assert len(data) == num_bytes, f"data length {len(data)} does not match expected size {num_bytes} for type {value_type}"
    method = bytes_to_int if base_type == "int" else bytes_to_uint
    return method(data, little_endian)


def int_pack(value: int, num_bits: int) -> BitArray:
    """Convert a single int value to a fixed-length bit representation."""
    check_int_range(value, num_bits)
    return BitArray(int=value, length=num_bits)

def uint_pack(value: int, num_bits: int) -> BitArray:
    """Convert a single uint value to a fixed-length bit representation."""
    check_uint_range(value, num_bits)
    return BitArray(uint=value, length=num_bits)


def int_unpack(bits: BitArray) -> int:
    """Convert a BitArray to a single int value."""
    return bits.int

def uint_unpack(bits: BitArray) -> int:
    """Convert a BitArray to a single uint value."""
    return bits.uint

