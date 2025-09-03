"""
umbi.io: Utilities for binary and JSON serialization, and tar archive handling.
"""

from .bytes import bytes_to_vector, vector_to_bytes
from .json import *
from .tar import TarReader, TarWriter
from .vector import *

__all__ = [
    "bytes_to_vector",
    "JsonLike",
    "json_remove_none",
    "json_to_string",
    "TarReader",
    "TarWriter",
]
