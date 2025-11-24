"""
(De)serialization of jsons.
"""

import umbi.datatypes

from .strings import bytes_to_string, string_to_bytes


def bytes_to_json(data: bytes) -> umbi.datatypes.JsonLike:
    """Convert bytes to a JSON object."""
    return umbi.datatypes.string_to_json(bytes_to_string(data))


def json_to_bytes(json_obj: umbi.datatypes.JsonLike) -> bytes:
    """Convert a JSON object to bytes."""
    return string_to_bytes(umbi.datatypes.json_to_string(json_obj))
