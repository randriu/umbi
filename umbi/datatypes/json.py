"""
JSON operations and utilities.
"""

import json as std_json

JsonPrimitive = None | bool | int | float | str
JsonList = list["JsonLike"]
JsonDict = dict[str, "JsonLike"]
JsonLike = JsonPrimitive | JsonList | JsonDict


def is_json_instance(value: object) -> bool:
    if isinstance(value, (type(None), bool, int, float, str)):
        return True
    elif isinstance(value, list):
        return all(is_json_instance(v) for v in value)
    elif isinstance(value, dict):
        return all(isinstance(k, str) and is_json_instance(v) for k, v in value.items())
    return False


def json_remove_none_dict_values(json_obj: JsonLike) -> JsonLike:
    """Recursively remove all None (null) dictionary values from a JSON (sub-)object."""
    if isinstance(json_obj, dict):
        return {k: json_remove_none_dict_values(v) for k, v in json_obj.items() if v is not None}
    elif isinstance(json_obj, list):
        return [json_remove_none_dict_values(v) for v in json_obj]
    return json_obj


def json_to_string(json_obj: JsonLike, indent: int | None = 4, **kwargs) -> str:
    """
    :raises: JSONEncodeError if the object is not serializable
    """
    return std_json.dumps(json_obj, indent=indent, **kwargs)


def string_to_json(json_str: str) -> JsonLike:
    """
    :raises: JSONDecodeError if the string is not valid JSON
    """
    return std_json.loads(json_str)
