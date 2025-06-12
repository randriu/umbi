import logging
import struct

import umbi


def bytes_to_string(data: bytes) -> str:
    """Convert a binary string to a utf-8 string."""
    return data.decode("utf-8")


def string_to_bytes(string: str) -> bytes:
    """Convert a utf-8 string to a binary string."""
    return string.encode("utf-8")


def assert_key_in_dict(table: dict, key, desc: str):
    if key not in table:
        raise ValueError(f"{desc} must be in {table} but is {key}")


def value_type_to_struct_format(value_type: str) -> str:
    """Convert a value type to a formatting string for struct."""
    table = {
        "int32": "i",
        "uint32": "I",
        "int64": "q",
        "uint64": "Q",
        "double": "d",
    }
    assert_key_in_dict(table, value_type, "value type")
    return table[value_type]


def value_type_to_size(value_type: str) -> int:
    """Map value type to its size."""
    table = {
        "int32": 4,
        "uint32": 4,
        "int64": 8,
        "uint64": 8,
        "double": 8,
    }
    assert_key_in_dict(table, value_type, "value type")
    return table[value_type]


def endianness_to_struct_format(little_endian: bool) -> str:
    """
    Convert endianness flag to a formatting string for struct.
    :param little_endian: True for little-endian, False for big-endian
    """
    table = {False: ">", True: "<"}
    assert_key_in_dict(table, little_endian, "endianness")
    return table[little_endian]


def vector_to_bytes(vector: list, value_type: str, little_endian: bool = True) -> bytes:
    """Encode a list of values as a binary string.

    :param value_type: vector element type, one of {"bool", "uint64", "double"}
    """
    if len(vector) == 0:
        logging.warning("exporting empty binary file")
        return b""

    if value_type == "char":
        return string_to_bytes(vector)

    if value_type == "bool":
        # TODO respect endianness
        assert little_endian, "big-endianness for bitvectors is not implemented"
        # drop trailing zeros?

        # pad vector up to 64 bits
        target_pad = 64
        num_pad = (target_pad - (len(vector) % target_pad)) % target_pad
        vector = vector + [False] * num_pad
        bitmask = b""
        for byte_index in range(len(vector) // 8):
            bits = vector[byte_index * 8 : byte_index * 8 + 8]
            byte_int = sum((1 << i) for i, bit in enumerate(bits) if bit)
            bitmask += byte_int.to_bytes(1, byteorder="little")
        return bitmask

    for item in vector:
        assert isinstance(item, int) or isinstance(item, float)
        if value_type in ["uint32", "uint64"]:
            assert isinstance(item, int) and item >= 0
    endian_format = endianness_to_struct_format(little_endian)
    type_format = value_type_to_struct_format(value_type)
    return struct.pack(f"{endian_format}{len(vector)}{type_format}", *vector)


def bytes_to_vector(vector_bytes: bytes, value_type: str, little_endian: bool = True) -> list:
    """
    Decode a binary string as a list of numbers.

    :param value_type: vector element type, one of {"bool", "uint64", "double"}
    """
    if value_type == "char":
        return bytes_to_string(vector_bytes)
    if value_type == "bool":
        bitvector = []
        for bitmask in vector_bytes:
            for i in range(8):
                bitvector.append((bitmask >> i) & 1 == 1)
        return bitvector
    type_format = value_type_to_struct_format(value_type)
    endian_format = endianness_to_struct_format(little_endian)
    num_entries = len(vector_bytes) // value_type_to_size(value_type)
    vector = struct.unpack(f"{endian_format}{num_entries}{type_format}", vector_bytes)
    return list(vector)
