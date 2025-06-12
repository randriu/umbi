import importlib.resources
import tempfile

import pytest
import umby


@pytest.mark.parametrize(
    "vector, value_type",
    [
        ([3.14, 0, 150.5, -1 / 7], "double"),
        ([0, 2, 76, 5], "uint"),
        ([False, False, False, False, True], "bool"),
    ],
)
def test_vector_bytes(vector, value_type):
    vector_in = vector
    vector_bytes = umby.vector_to_bytes(vector_in, value_type)
    assert isinstance(vector_bytes, bytes)
    vector_out = umby.vector_from_bytes(vector_bytes, value_type)
    if value_type != "bool":
        assert len(vector_in) == len(vector_out)
    else:
        assert len(vector_out) % 64 == 0
    for i in range(len(vector_in)):
        assert vector_in[i] == vector_out[i]


def test_json_bytes():
    json_in = {"a": 0, "b": "c", "c": {"aa": ["alex", "bob"]}, "d": None}
    json_bytes = umby.json_to_bytes(json_in)
    assert isinstance(json_bytes, bytes)
    json_out = umby.json_from_bytes(json_bytes)
    assert json_in["a"] == json_out["a"]


def test_tar():
    filename_data = umby.tar_read("data/nand-20-1.umb")
    assert "index.json" in filename_data
    for data in filename_data.values():
        assert isinstance(data, bytes)
    with tempfile.NamedTemporaryFile(delete=True) as temp_file:
        umby.tar_write(temp_file.name, filename_data)
