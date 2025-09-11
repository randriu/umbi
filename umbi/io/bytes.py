"""
Utilities for (de)serializing binary strings.
"""

import logging

logger = logging.getLogger(__name__)

import fractions
import struct
from typing import Optional


def bytes_to_string(data: bytes) -> str:
    """Convert a binary string to a utf-8 string."""
    return data.decode("utf-8")


def string_to_bytes(string: str) -> bytes:
    """Convert a utf-8 string to a binary string."""
    return string.encode("utf-8")


def bytes_to_bitvector(bitvector_bytes: bytes) -> list[bool]:
    """Convert a bytestring representing a bitvector into a list of booleans."""
    return [(byte >> bit) & 1 == 1 for byte in bitvector_bytes for bit in range(8)]


def bitvector_to_bytes(bitvector: list[bool]) -> bytes:
    """Convert a list of booleans representing a bitvector into a bytestring."""
    byte_array = bytearray()
    for i in range(0, len(bitvector), 8):
        byte = sum((1 << j) for j in range(8) if i + j < len(bitvector) and bitvector[i + j])
        byte_array.append(byte)
    return bytes(byte_array)


def endianness_to_struct_format(little_endian: bool) -> str:
    """Convert endianness flag to a formatting string for struct."""
    return "<" if little_endian else ">"

def assert_key_in_dict(table: dict, key, desc):
    if key not in table:
        raise ValueError(f"{desc} must be one of {list(table.keys())} but is {key}")

def value_type_to_struct_format(value_type: str) -> str:
    """Convert a value type to a formatting string for struct."""
    table = {
        "int32": "i",
        "int64": "q",
        "uint32": "I",
        "uint64": "Q",
        "double": "d",
    }
    assert_key_in_dict(table, value_type, "value type")
    return table[value_type]



def bytes_to_value(
    data: bytes, value_type: str, little_endian: bool = True
) -> int | float | fractions.Fraction | str | tuple:
    """
    Convert a binary string to a single value of the given type.
    :param value_type: string or one of {int32|uint32|int64|uint64|double|rational}[-interval]
    :return: a pair of left and right values for interval types, or a single value otherwise
    """

    if value_type == "string":
        return bytes_to_string(data)

    if "-interval" in value_type:
        assert len(data) % 2 == 0, "interval data must have even length"
        mid = len(data) // 2
        base_value_type = value_type.replace("-interval", "")
        left = bytes_to_value(data[:mid], base_value_type)
        right = bytes_to_value(data[mid:], base_value_type)
        return (left, right)

    if value_type == "rational":
        assert len(data) % 2 == 0, "rational data must have even length"
        mid = len(data) // 2
        byteorder = "little" if little_endian else "big"
        numerator = int.from_bytes(data[:mid], byteorder=byteorder, signed=True)
        denominator = int.from_bytes(data[mid:], byteorder=byteorder, signed=False)
        return fractions.Fraction(numerator, denominator)

    assert value_type in ["int32", "uint32", "int64", "uint64", "double"], "unexpected value type"
    type_format = value_type_to_struct_format(value_type)
    endian_format = endianness_to_struct_format(little_endian)
    return struct.unpack(f"{endian_format}{type_format}", data)[0]


def normalize_rational(value: fractions.Fraction) -> fractions.Fraction:
    """Ensure that the denominator of a rational number is non-negative."""
    if value.denominator < 0:
        value = fractions.Fraction(-value.numerator, -value.denominator)
    return value


def standard_value_type_size(value_type: str) -> int:
    """Return the number of bytes needed to represent a value of the given type."""
    if "-interval" in value_type:
        base_value_type = value_type.replace("-interval", "")
        return 2 * standard_value_type_size(base_value_type)
    if value_type == "rational":
        # for rationals, the standard size is 8+8 bytes
        return standard_value_type_size("int64") + standard_value_type_size("uint64")
    table = {
        "int32": 4,
        "int64": 8,
        "uint32": 4,
        "uint64": 8,
        "double": 8,
    }
    assert_key_in_dict(table, value_type, "value type")
    return table[value_type]


def integer_value_size(value: int) -> int:
    """Return the number of bytes needed to represent an integer value, rounded up to the nearest multiple of 8."""
    num_bytes = (value.bit_length() + 7) // 8
    if num_bytes % 8 != 0:
        num_bytes += 8 - (num_bytes % 8)
    return num_bytes


def rational_value_size(value: fractions.Fraction) -> int:
    """Return the number of bytes needed to represent a rational value."""
    return 2*max(integer_value_size(value.numerator), integer_value_size(value.denominator))


def rational_to_bytes(value: fractions.Fraction, max_integer_size: Optional[int] = None, little_endian: bool = True) -> bytes:
    """
    Convert a rational number to a bytestring. Both numberator and denominator are encoded as signed and unsigned integers, respectively, and have the same size.
    :param max_integer_size: (optional) maximum size in bytes for numerator and denominator; if not provided, the size is determined automatically
    """
    value = normalize_rational(value)
    if max_integer_size is None:
        max_integer_size = rational_value_size(value) // 2
    byteorder = "little" if little_endian else "big"
    numerator_bytes = value.numerator.to_bytes(max_integer_size, byteorder=byteorder, signed=True)
    denominator_bytes = value.denominator.to_bytes(max_integer_size, byteorder=byteorder, signed=False)
    return numerator_bytes + denominator_bytes


def value_to_bytes(
    value: int | float | tuple | fractions.Fraction | str, value_type: str, little_endian: bool = True
) -> bytes:
    """
    Convert a value of a given type to a bytestring.
    :param value_type: either string or one of {int32|uint32|int64|uint64|double|rational}[-interval]
    """

    if value_type == "string":
        assert isinstance(value, str), "string value must be a str"
        return string_to_bytes(value)

    if value_type == "rational":
        assert isinstance(value, fractions.Fraction), "rational value must be a Fraction"
        return rational_to_bytes(value, little_endian=little_endian)

    if "-interval" in value_type:
        assert isinstance(value, tuple) and len(value) == 2, "interval value must be a tuple of two values"
        base_value_type = value_type.replace("-interval", "")
        if base_value_type != "rational":
            lower = value_to_bytes(value[0], base_value_type, little_endian)
            upper = value_to_bytes(value[1], base_value_type, little_endian)
        else:
            assert all(isinstance(v, fractions.Fraction) for v in value), "expected a pair of fractions"
            # ensure both rationals use the same size for numerator and denominator
            max_integer_size = max(rational_value_size(v) for v in value) // 2
            lower = rational_to_bytes(value[0], max_integer_size, little_endian)
            upper = rational_to_bytes(value[1], max_integer_size, little_endian)
        return lower + upper

    assert value_type in ["int32", "uint32", "int64", "uint64", "double"], "unexpected value type"
    type_format = value_type_to_struct_format(value_type)
    endian_format = endianness_to_struct_format(little_endian)
    return struct.pack(f"{endian_format}{type_format}", value)


def bytes_into_chunk_ranges(data: bytes, chunk_ranges: list[tuple[int, int]]) -> list[bytes]:
    """Split bytestring into chunks according to chunk ranges."""
    return [data[start:end] for start, end in chunk_ranges]


def bytes_into_num_chunks(data: bytes, num_chunks: int) -> list[bytes]:
    """Split bytestring into evenly sized chunks."""
    assert num_chunks > 0, "num_chunks must be a positive number"
    assert len(data) % num_chunks == 0, "len(data) must be divisible by num_chunks when item_ranges are not provided"
    chunk_size = len(data) // num_chunks
    chunk_ranges = [(i * chunk_size, (i + 1) * chunk_size) for i in range(num_chunks)]
    return bytes_into_chunk_ranges(data, chunk_ranges)


def bytes_to_vector(
    data: bytes, value_type: str, chunk_ranges: Optional[list[tuple[int, int]]] = None, little_endian: bool = True
) -> list:
    """
    Decode a binary string as a list of numbers.
    :param value_type: vector element type, either bool, string or one of {int32|uint32|int64|uint64|double|rational}[-interval]
    :param chunk_ranges: (optional) chunk ranges to split the data into
    :param little_endian: if True, the binary string is interpreted as little-endian
    """
    if value_type == "bool":
        assert little_endian, "big-endianness for bitvectors is not implemented"
        return bytes_to_bitvector(data)

    if len(data) == 0:
        return []

    if chunk_ranges is None:
        chunk_size = standard_value_type_size(value_type)
        assert len(data) % chunk_size == 0, "len(data) must be divisible by the size of the value type"
        num_chunks = len(data) // chunk_size
        chunks = bytes_into_num_chunks(data, num_chunks)
        return [bytes_to_value(chunk, value_type, little_endian) for chunk in chunks]

    return [bytes_to_value(data[start:end], value_type, little_endian) for start, end in chunk_ranges]


def vector_to_bytes(
    vector: list, value_type: str, little_endian: bool = True
) -> tuple[bytes, Optional[list[tuple[int, int]]]]:
    """Encode a list of values as a binary string.
    :param value_type: vector element type, either bool, string or {int32|uint32|int64|uint64|double|rational}[-interval]
    :return: encoded binary string
    :return: (optional) chunk ranges if non-trivial splitting is needed to split the resulting bytestring into chunks, e.g. for strings or non-standard rationals
    """
    if len(vector) == 0:
        logger.warning("converting empty vector to bytes")
        return (b"", None)

    if value_type == "bool":
        assert little_endian, "big-endianness for bitvectors is not implemented"
        return (bitvector_to_bytes(vector), None)

    chunks = [value_to_bytes(item, value_type, little_endian) for item in vector]
    chunk_ranges = None
    if value_type == "string" or any(len(chunk) != standard_value_type_size(value_type) for chunk in chunks):
        chunk_ranges = []
        current_pos = 0
        for chunk in chunks:
            chunk_size = len(chunk)
            chunk_ranges.append((current_pos, current_pos + chunk_size))
            current_pos += chunk_size
    bytestring = b"".join(chunks)

    return bytestring, chunk_ranges
