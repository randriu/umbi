from umbi.datatypes.vector import (
    is_vector_csr,
    is_vector_ranges,
    csr_to_ranges,
    ranges_to_csr,
)


def test_is_vector_csr_valid():
    assert is_vector_csr([0, 2, 5, 7]) is True
    assert is_vector_csr([0, 1]) is True
    assert is_vector_csr([0, 0]) is True
    assert is_vector_csr([0, 0, 0]) is True


def test_is_vector_csr_invalid():
    assert is_vector_csr([]) is False
    assert is_vector_csr([0]) is False
    assert is_vector_csr([1, 2, 3]) is False
    assert is_vector_csr([0, 2, 1]) is False
    assert is_vector_csr([0, 2, "a"]) is False  # type: ignore


def test_is_vector_ranges_valid():
    assert is_vector_ranges([(0, 2), (2, 5), (5, 7)]) is True
    assert is_vector_ranges([(1, 3)]) is True
    assert is_vector_ranges([(0, 0)]) is True


def test_is_vector_ranges_invalid():
    assert is_vector_ranges([]) is False
    assert is_vector_ranges([(0, 2), (3, 5)]) is False
    assert is_vector_ranges([(0, 2), (2, 1)]) is False
    assert is_vector_ranges([(0, 2, 3)]) is False  # type: ignore
    assert is_vector_ranges([(0, "a")]) is False  # type: ignore
    assert is_vector_ranges([(2, 0)]) is False


def test_csr_to_ranges_basic():
    input = [0, 2, 5, 7]
    expected = [(0, 2), (2, 5), (5, 7)]
    assert csr_to_ranges(input) == expected


def test_ranges_to_csr_basic():
    input = [(0, 2), (2, 5), (5, 7)]
    expected = [0, 2, 5, 7]
    assert ranges_to_csr(input) == expected


def test_csr_to_ranges_and_back():
    input = [0, 3, 6, 10]
    output = ranges_to_csr(csr_to_ranges(input))
    assert input == output


def test_ranges_to_csr_and_back():
    input = [(0, 4), (4, 8), (8, 10)]
    output = csr_to_ranges(ranges_to_csr(input))
    assert input == output
