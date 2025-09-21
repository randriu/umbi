import pytest
import json
from umbi.io.json import *


def test_json_remove_none_dict():
    input = {
        "key1": "value1",
        "key2": [None, "value2", None],
        "key3": {
            "nested1": "value2",
            "nested2": None,
            "nested3": {
                "deep1": "value3",
                "deep2": None
            }
        },
        "key4": None
    }
    
    expected = {
        "key1": "value1",
        "key2": [None, "value2", None],
        "key3": {
            "nested1": "value2",
            "nested3": {
                "deep1": "value3"
            }
        }
    }
    
    output = json_remove_none_dict_values(input)
    assert output == expected

def test_json_remove_none_no_none_values():
    input = {
        "key1": "value1",
        "key2": {
            "nested": "value2"
        },
        "key3": [1, 2, 3]
    }
    
    output = json_remove_none_dict_values(input)
    assert output == input


def test_json_to_string_indent():
    input = {"key": "value"}
    assert json_to_string(input, indent=None) == '{"key": "value"}'
    assert json_to_string(input, indent=0) == '{\n"key": "value"\n}'
    assert json_to_string(input, indent=2) == '{\n  "key": "value"\n}'


def test_string_to_json_valid():
    input = '{"key": "value", "number": 42, "array": [1, 2, 3], "none": null}'
    output = string_to_json(input)
    expected = {
        "key": "value",
        "number": 42,
        "array": [1, 2, 3],
        "none": None
    }
    assert output == expected


def test_string_to_json_invalid():
    invalid_json = '{"key": "value"'  # Missing closing brace
    
    with pytest.raises(json.JSONDecodeError):
        string_to_json(invalid_json)


def test_string_to_json_empty():
    assert string_to_json('{}') == {}
    assert string_to_json('[]') == []
    assert string_to_json('null') is None
    assert string_to_json('""') == ""


def test_json_to_string_and_back():
    input = {
        "string": "hello world 🌍",
        "number": 42,
        "float": 3.14,
        "boolean": True,
        "null": None,
        "array": [1, 2, 3],
        "nested": {
            "key": "value"
        }
    }

    output = json_to_string(input)
    restored = string_to_json(output)

    assert restored == input


def test_json_to_bytes_and_back():
    """Test that JSON -> bytes -> JSON roundtrip preserves data."""
    input = {
        "string": "hello world 🌍",
        "number": 42,
        "float": 3.14,
        "boolean": True,
        "null": None,
        "array": [1, 2, 3],
        "nested": {
            "key": "value"
        }
    }

    output = json_to_bytes(input)
    restored = bytes_to_json(output)

    assert restored == input

