"""
Utilities for (de)serializing integers and floats.
"""

import struct

from bitstring import BitArray


def split_bytes(bytestring: bytes, length: int) -> tuple[bytes, bytes]:
    """Split a bytestring into chunks of the given size."""
    assert length > 0, "chunk size must be positive"
    assert len(bytestring) >= length, "data is shorter than the specified length"
    return bytestring[:length], bytestring[length:]


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
    """Convert a single integer value to a fixed-length byte representation."""
    check_int_range(value, num_bytes * 8)
    return value.to_bytes(num_bytes, byteorder="little" if little_endian else "big", signed=True)


def uint_to_bytes(value: int, num_bytes: int, little_endian: bool = True) -> bytes:
    """Convert a single unsigned integer value to a fixed-length byte representation."""
    check_uint_range(value, num_bytes * 8)
    return value.to_bytes(num_bytes, byteorder="little" if little_endian else "big", signed=False)


def bytes_to_int(data: bytes, little_endian: bool = True) -> int:
    """Convert a binary string to a single integer value."""
    return int.from_bytes(data, byteorder="little" if little_endian else "big", signed=True)


def bytes_to_uint(data: bytes, little_endian: bool = True) -> int:
    """Convert a binary string to a single unsigned integer value."""
    return int.from_bytes(data, byteorder="little" if little_endian else "big", signed=False)


def assert_is_primitive(value_type: str):
    """Assert that the given value type is a primitive type."""
    primitives = {"int16", "uint16", "int32", "int64", "uint32", "uint64", "double"}
    if value_type not in primitives:
        raise ValueError(f"value type must be one of {list(primitives)} but is {value_type}")


def value_type_to_struct_format(value_type: str) -> str:
    """Convert a value type to a formatting string for struct."""
    assert_is_primitive(value_type)
    return {
        "int16": "h",
        "uint16": "H",
        "int32": "i",
        "int64": "q",
        "uint32": "I",
        "uint64": "Q",
        "double": "d",
    }[value_type]


def primitive_value_type_size(value_type: str) -> int:
    """Return the size in bytes of a primitive value type."""
    assert_is_primitive(value_type)
    return {
        "int16": 2,
        "uint16": 2,
        "int32": 4,
        "int64": 8,
        "uint32": 4,
        "uint64": 8,
        "double": 8,
    }[value_type]


def endianness_to_struct_format(little_endian: bool) -> str:
    """Convert endianness flag to a formatting string for struct."""
    return "<" if little_endian else ">"


def primitive_to_bytes(value: int | float, value_type: str, little_endian: bool = True) -> bytes:
    """Convert a single primitive value of the given type to a bytestring."""
    type_format = value_type_to_struct_format(value_type)
    endian_format = endianness_to_struct_format(little_endian)
    return struct.pack(f"{endian_format}{type_format}", value)


def bytes_to_primitive(data: bytes, value_type: str, little_endian: bool = True) -> int | float:
    """Convert a binary string to a single primitive value of the given type."""
    type_format = value_type_to_struct_format(value_type)
    endian_format = endianness_to_struct_format(little_endian)
    return struct.unpack(f"{endian_format}{type_format}", data)[0]


def int_to_bits(value: int, num_bits: int) -> BitArray:
    check_int_range(value, num_bits)
    """Convert a single integer value to a fixed-length bit representation."""
    return BitArray(int=value, length=num_bits)


def uint_to_bits(value: int, num_bits: int) -> BitArray:
    """Convert a single unsigned integer value to a fixed-length bit representation."""
    check_uint_range(value, num_bits)
    return BitArray(uint=value, length=num_bits)


def double_to_bits(value: float) -> BitArray:
    """Convert a single double value to a fixed-length bit representation."""
    return BitArray(float=value, length=64)


def primitive_to_bits(value: int | float, value_type: str, num_bits: int) -> BitArray:
    """Convert a single primitive value of the given type to a fixed-length bit representation."""
    assert value_type in ["int", "uint", "double"], f"unsupported primitive type: {value_type}"
    if value_type == "double":
        assert num_bits == 64, "double must be represented with 64 bits"
        assert isinstance(value, float), "double values must be floats"
        return double_to_bits(value)
    else:
        # value_type in ["int", "uint"]
        assert isinstance(value, int), "int and uint values must be integers"
        if value_type == "int":
            return int_to_bits(value, num_bits)
        else:
            return uint_to_bits(value, num_bits)


def bits_to_int(bits: BitArray) -> int:
    """Convert a BitArray to a single integer value."""
    return bits.int


def bits_to_uint(bits: BitArray) -> int:
    """Convert a BitArray to a single unsigned integer value."""
    return bits.uint


def bits_to_double(bits: BitArray) -> float:
    """Convert a BitArray to a single double value."""
    return bits.float


def bits_to_primitive(bits: BitArray, value_type: str) -> int | float:
    """Convert a BitArray to a single primitive value of the given type."""
    assert value_type in ["int", "uint", "double"], f"unsupported primitive type: {value_type}"

    if value_type == "double":
        assert len(bits) == 64, "double must be represented with 64 bits"
        return bits_to_double(bits)
    elif value_type == "int":
        return bits_to_int(bits)
    else:
        # value_type == "uint":
        return bits_to_uint(bits)
