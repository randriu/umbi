"""
Utilities for (de)serializing JSONs.
"""

import json
import logging

logger = logging.getLogger(__name__)
import typing

import umbi

"""A type alias for (high-level) JSON objects."""
JsonLike = typing.Union[dict, list]


def json_remove_none_dict_values(json_obj: JsonLike) -> JsonLike:
    """Recursively remove all None (null) dictionary values from a JSON (sub-)object."""
    if isinstance(json_obj, dict):
        return {k: json_remove_none_dict_values(v) for k, v in json_obj.items() if v is not None}
    elif isinstance(json_obj, list):
        return [json_remove_none_dict_values(v) for v in json_obj]
    return json_obj


def json_to_string(json_obj: JsonLike, remove_none: bool = False, indent: int | None = 4, **kwargs) -> str:
    """
    Encode a JSON object as a string.
    :raises: JSONEncodeError if the object is not serializable
    """
    if remove_none:
        json_obj = json_remove_none_dict_values(json_obj)
    return json.dumps(json_obj, indent=indent, **kwargs)


def string_to_json(json_str: str) -> JsonLike:
    """
    Convert a string to a JSON object.
    :raises: JSONDecodeError if the string is not valid JSON
    """
    return json.loads(json_str)


def bytes_to_json(data: bytes) -> JsonLike:
    """Convert bytes to a JSON object."""
    return string_to_json(umbi.binary.bytes_to_string(data))


def json_to_bytes(json_obj: JsonLike) -> bytes:
    """Convert a JSON object to bytes."""
    return umbi.binary.string_to_bytes(json_to_string(json_obj))
