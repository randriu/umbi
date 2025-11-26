"""
(De)serialization of sequences of common types or structs.
"""

import logging

from umbi.datatypes import CommonType, StructType

from .bitvectors import bitvector_to_bytes, bytes_to_bitvector
from .common import (
    bytes_to_common_value,
    common_value_to_bytes,
    num_bytes_for_common_type,
)
from .structs import struct_pack, struct_unpack

logger = logging.getLogger(__name__)


def bytes_into_chunk_ranges(data: bytes, chunk_ranges: list[tuple[int, int]]) -> list[bytes]:
    """Split bytestring into chunks according to chunk ranges."""
    assert len(data) == chunk_ranges[-1][1], "data length does not match the end of the last chunk range"
    return [data[start:end] for start, end in chunk_ranges]


def chunks_to_csr(chunks: list[bytes]) -> list[int]:
    """Build csr for a list of chunks."""
    current_pos = 0
    csr = [current_pos]
    for chunk in chunks:
        current_pos += len(chunk)
        csr.append(current_pos)
    return csr


def bytes_into_chunks(data: bytes, chunk_size: int) -> list[bytes]:
    """Split bytestring into evenly sized chunks."""
    assert chunk_size > 0, f"expected {chunk_size} to be a positive number"
    assert len(data) % chunk_size == 0, f"expected {len(data)} to be divisible by {chunk_size}"
    return [data[i : i + chunk_size] for i in range(0, len(data), chunk_size)]


def bytes_to_vector(
    data: bytes,
    value_type: CommonType | StructType,
    chunk_ranges: list[tuple[int, int]] | None = None,
    little_endian: bool = True,
) -> list:
    """
    Decode a binary string as a list of numbers.
    :param value_type: vector element type, either composite, bool, string or one of {int32|uint32|int64|uint64|double|rational}[-interval]
    :param chunk_ranges: (optional) chunk ranges to split the data into
    :param little_endian: if True, the binary string is interpreted as little-endian
    """

    if isinstance(value_type, StructType):
        assert chunk_ranges is not None, "chunk_ranges must be provided when value_type is a StructType"
        chunks = bytes_into_chunk_ranges(data, chunk_ranges)
        return [struct_unpack(chunk, value_type) for chunk in chunks]

    if value_type == CommonType.BOOLEAN:
        assert little_endian, "big-endianness for bitvectors is not implemented"
        return bytes_to_bitvector(data)

    if len(data) == 0:
        return []

    if chunk_ranges is None:
        chunk_size = num_bytes_for_common_type(value_type)
        chunks = bytes_into_chunks(data, chunk_size)
    else:
        chunks = bytes_into_chunk_ranges(data, chunk_ranges)
    return [bytes_to_common_value(chunk, value_type, little_endian) for chunk in chunks]


def vector_to_bytes(
    vector: list, value_type: CommonType | StructType, little_endian: bool = True
) -> tuple[bytes, list[int] | None]:
    """Encode a list of values as a binary string.
    :param value_type: vector element type
    :return: encoded binary string
    :return: (optional) chunk csr if non-trivial splitting is needed to split the resulting bytestring into chunks, e.g. for strings or non-standard rationals
    """

    if len(vector) == 0:
        logger.warning("converting empty vector to bytes")
        return (b"", None)

    if isinstance(value_type, StructType):
        chunks = [struct_pack(value_type, item) for item in vector]
        chunks_csr = chunks_to_csr(chunks)
        bytestring = b"".join(chunks)
        return bytestring, chunks_csr

    if value_type == CommonType.BOOLEAN:
        assert little_endian, "big-endianness for bitvectors is not implemented"
        return (bitvector_to_bytes(vector), None)

    chunks = [common_value_to_bytes(item, value_type, little_endian) for item in vector]
    chunks_csr = None
    if value_type == CommonType.STRING or any(len(chunk) != num_bytes_for_common_type(value_type) for chunk in chunks):
        chunks_csr = chunks_to_csr(chunks)
    bytestring = b"".join(chunks)

    return bytestring, chunks_csr
