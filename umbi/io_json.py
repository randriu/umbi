import json
import logging
import typing

import umbi

""" A type alias for (high-level) json objects. """
jsonlike = typing.Union[dict, list]


def json_remove_none(json_obj: object):
    """Recursively remove all None (null) values from a json (sub-)object."""
    if isinstance(json_obj, dict):
        return {k: json_remove_none(v) for k, v in json_obj.items() if v is not None}
    elif isinstance(json_obj, list):
        return [json_remove_none(v) for v in json_obj]
    else:
        return json_obj


def json_to_string(json_obj: jsonlike, remove_none: bool = False, indent: int = 4) -> str:
    """Encode a json object as a string."""
    if remove_none:
        json_obj = json_remove_none(json_obj)
    return json.dumps(json_obj, indent=indent)


def string_to_json(json_str: str) -> jsonlike:
    """Convert a string to a json object."""
    return json.loads(json_str)


def json_show(json_obj: jsonlike):
    """Print a json object to stdout."""
    logging.debug(json_to_string(json_obj))


def bytes_to_json(data: bytes) -> jsonlike:
    return string_to_json(umbi.bytes_to_string(data))


def json_to_bytes(json_obj: jsonlike) -> bytes:
    return umbi.string_to_bytes(json_to_string(json_obj))
