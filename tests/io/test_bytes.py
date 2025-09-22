import pytest
from umbi.binary import *
import fractions


def test_string_empty():
    input = ""
    b = string_to_bytes(input)
    assert b == b""
    restored = bytes_to_string(b)
    assert restored == input


def test_string_conversion():
    input = "hello world 🌍 你好 мир"
    b = string_to_bytes(input)
    restored = bytes_to_string(b)
    assert restored == input


def test_bitvector_converstion_empty():
    input = []
    b = bitvector_to_bytes(input)
    assert b == b""
    restored = bytes_to_bitvector(b)
    assert restored == input


def test_bitvector_conversion_one():
    # Test with a simple bitvector
    input = [True, False, True, True, False, False, False, True]  # 10110001 -> 0b10001101
    b = bitvector_to_bytes(input)
    assert b == 0b10001101.to_bytes(1, byteorder='little')
    restored = bytes_to_bitvector(b)
    assert restored == input


def test_bitvector_conversion_two():
    # Test with a longer bitvector (not a multiple of 8)
    input = [True, True, True, False, False, True, False, True, True, False] # 1110010110 -> 0b0110100111
    b = bitvector_to_bytes(input)
    assert b == 0b0110100111.to_bytes(2, byteorder='little')
    restored = bytes_to_bitvector(b)
    assert len(restored) > len(input)
    restored = restored[:len(input)]
    assert restored == input


@pytest.mark.parametrize(
    "value,value_type,kwargs",
    [
        (123456, "int32", {}),
        (2**60 + 123, "uint64", {}),
        (3.141592653589793, "double", {}),
        (fractions.Fraction(-7, 13), "rational", {}),
        (fractions.Fraction(7, -13), "rational", {}),
        (fractions.Fraction(2**100, -13), "rational", {}),
        ((42, 99), "int32-interval", {}),
        ((fractions.Fraction(1, 3), fractions.Fraction(2, 5)), "rational-interval", {}),
        ("test string", "string", {}),
        (0x12345678, "uint32", {"little_endian": True}),
        (0x12345678, "uint32", {"little_endian": False}),
    ]
)
def test_value_conversion(value, value_type, kwargs):
    b = value_to_bytes(value, value_type, **kwargs)
    restored = bytes_to_value(b, value_type, **kwargs)
    assert restored == value

@pytest.mark.parametrize(
    "value,value_type",
    [
        (2**40, "int32"),
        (-2**40, "int32"),
    ]
)
def test_value_conversion_int32_overflow(value, value_type):
    import struct
    with pytest.raises(struct.error):
        value_to_bytes(value, value_type)


def test_bytes_to_vector_asserts_on_wrong_size():
    # Provide data not divisible by value size
    with pytest.raises(AssertionError):
        bytes_to_vector(b"\x00\x01\x02", "int32")


@pytest.mark.parametrize(
    "vector,value_type,chunk_ranges_expected",
    [
        ([1, 2, 3, 4], "int32", False),
        ([2**32 - 1, 0, 123], "uint32", False),
        ([3.14, 2.71, -1.0], "double", False),
        ([fractions.Fraction(1, 2), fractions.Fraction(3, -4)], "rational", False),
        ([True, False, True, True, False, False, True, False, True], "bool", False),
        ([(1, 2), (3, 4)], "int32-interval", False),
        ([(fractions.Fraction(1, 3), fractions.Fraction(2, 5))], "rational-interval", False),
        ([], "int32", False),
        ([True, False, True, False, True], "bool", False),

        (["foo", "bar", "baz"], "string", True),
        ([fractions.Fraction(2**80, 3), fractions.Fraction(-2**60, 7)], "rational", True),
        ([(fractions.Fraction(2**80, 3), fractions.Fraction(5,7)),(fractions.Fraction(2,3), fractions.Fraction(1,2))], "rational-interval", True),
    ]
)
def test_vector_to_bytes_and_back(vector, value_type, chunk_ranges_expected):
    bytestring, chunk_ranges = vector_to_bytes(vector, value_type)
    assert (chunk_ranges is not None) == chunk_ranges_expected
    restored = bytes_to_vector(bytestring, value_type, chunk_ranges=chunk_ranges)
    if value_type == "bool":
        # bools may pad bits, so slice to original length
        restored = restored[:len(vector)]
    assert restored == vector

