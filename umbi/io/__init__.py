"""
umbi.io: Utilities for binary and JSON serialization, and tar archive handling.
"""

from .bytes import bytes_to_vector, vector_to_bytes
from .json import *
from .tar import TarReader, TarWriter

__all__ = [
    "bytes_to_vector",
    "JsonLike",
    "json_remove_none_dict_values",
    "json_to_string",
    "TarReader",
    "TarWriter",
]
