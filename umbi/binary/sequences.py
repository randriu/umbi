"""
Utilities for (de)serialization of sequences of basic values (bytes).
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

from .api import *
from .booleans import *
from .composites import *
from .integers import *


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
    data: bytes,
    value_type: str | CompositeType,
    chunk_ranges: Optional[list[tuple[int, int]]] = None,
    little_endian: bool = True,
) -> list:
    """
    Decode a binary string as a list of numbers.
    :param value_type: vector element type, either composite, bool, string or one of {int32|uint32|int64|uint64|double|rational}[-interval]
    :param chunk_ranges: (optional) chunk ranges to split the data into
    :param little_endian: if True, the binary string is interpreted as little-endian
    """

    if isinstance(value_type, CompositeType):
        assert chunk_ranges is not None, "chunk_ranges must be provided when value_type is a CompositeType"
        chunks = bytes_into_chunk_ranges(data, chunk_ranges)
        return [composite_unpack(chunk, value_type) for chunk in chunks]

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
    else:
        chunks = bytes_into_chunk_ranges(data, chunk_ranges)
    return [bytes_to_value(chunk, value_type, little_endian) for chunk in chunks]


def vector_to_bytes(
    vector: list, value_type: str | CompositeType, little_endian: bool = True
) -> tuple[bytes, Optional[list[tuple[int, int]]]]:
    """Encode a list of values as a binary string.
    :param value_type: vector element type, either composite, bool, string or {int32|uint32|int64|uint64|double|rational}[-interval]
    :return: encoded binary string
    :return: (optional) chunk ranges if non-trivial splitting is needed to split the resulting bytestring into chunks, e.g. for strings or non-standard rationals
    """

    if len(vector) == 0:
        logger.warning("converting empty vector to bytes")
        return (b"", None)

    if isinstance(value_type, CompositeType):
        chunks = [composite_pack(value_type, item) for item in vector]
        chunk_ranges = []
        current_pos = 0
        for chunk in chunks:
            chunk_size = len(chunk)
            chunk_ranges.append((current_pos, current_pos + chunk_size))
            current_pos += chunk_size
        bytestring = b"".join(chunks)
        return bytestring, chunk_ranges

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
