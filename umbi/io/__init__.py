"""
umbi.io: Utilities for binary and JSON serialization, and tar archive handling.

This sub-package provides:
- JSON encoding/decoding helpers
- Tar archive reading/writing classes
"""

from .bytes import bytes_to_vector, vector_to_bytes
from .json import (
    JsonLike,
    json_remove_none,
    json_show_debug,
    json_to_string,
    string_to_json,
)
from .tar import TarReader, TarWriter
from .vector import *

__all__ = [
    "JsonLike",
    "json_remove_none",
    "json_to_string",
    "string_to_json",
    "json_show_debug",
    "TarReader",
    "TarWriter",
    "bytes_to_vector",
    "vector_to_bytes",
]
