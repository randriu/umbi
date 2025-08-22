import json
import logging
import typing

import umbi

"""A type alias for (high-level) JSON objects."""
JsonLike = typing.Union[dict, list]

def json_remove_none(json_obj: JsonLike) -> JsonLike:
    """Recursively remove all None (null) values from a JSON (sub-)object."""
    if isinstance(json_obj, dict):
        return {k: json_remove_none(v) for k, v in json_obj.items() if v is not None}
    elif isinstance(json_obj, list):
        return [json_remove_none(v) for v in json_obj]
    return json_obj

def json_to_string(json_obj: JsonLike, remove_none: bool = False, indent: int = 4, **kwargs) -> str:
    """Encode a JSON object as a string."""
    if remove_none:
        json_obj = json_remove_none(json_obj)
    return json.dumps(json_obj, indent=indent, **kwargs)

def string_to_json(json_str: str) -> JsonLike:
    """Convert a string to a JSON object."""
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logging.error(f"JSON decode error: {e}")
        raise

def json_show(json_obj: JsonLike):
    """Print a JSON object to logging.debug."""
    logging.debug(json_to_string(json_obj))

def bytes_to_json(data: bytes) -> JsonLike:
    """Convert bytes to a JSON object."""
    return string_to_json(umbi.bytes_to_string(data))

def json_to_bytes(json_obj: JsonLike) -> bytes:
    """Convert a JSON object to bytes."""
    return umbi.string_to_bytes(json_to_string(json_obj))
