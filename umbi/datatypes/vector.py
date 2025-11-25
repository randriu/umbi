"""
Auxiliary vector operations.
"""

from dataclasses import dataclass

from .common_type import CommonType, common_numeric_type
from .utils import (
    get_instance_type,
    is_instance_of_common_type,
    promote_numeric,
    promote_numeric_primitive,
)

# TODO add CSR vector?
# TODO add vector of ranges (for CSR?)


@dataclass
class VectorType:
    base_type: CommonType


"""Alias for a CSR vector type."""
CSR_TYPE = VectorType(CommonType.UINT64)


def assert_is_list(vector: object):
    if not isinstance(vector, list):
        raise TypeError(f"expected a list/vector, got {type(vector)}")


def is_vector_of_common_type(vector: list, element_type: CommonType) -> bool:
    return all(is_instance_of_common_type(elem, element_type) for elem in vector)


def is_vector_of_type(vector: list, element_type: VectorType) -> bool:
    return is_vector_of_common_type(vector, element_type.base_type)


def promote_to_vector_of_numeric_primitive(vector: list, target_type: CommonType) -> list:
    return [promote_numeric_primitive(elem, target_type) for elem in vector]


def promote_to_vector_of_numeric(vector: list, target_type: CommonType) -> list:
    return [promote_numeric(elem, target_type) for elem in vector]


def vector_element_types(vector: list) -> set[CommonType]:
    """Determine the set of common types of elements in the vector."""
    return set([get_instance_type(x) for x in vector])


def vector_element_type(vector: list) -> CommonType:
    """Determine the common type of elements in the vector. Raises an error if multiple types are found."""
    types = vector_element_types(vector)
    if len(types) != 1:
        raise ValueError(f"vector has multiple element types: {types}")
    return types.pop()


def vector_common_numeric_type(vector: list) -> CommonType:
    """Determine the common type to which all elements in the vector can be promoted."""
    if len(vector) == 0:
        return CommonType.INT  # whatever
    types = vector_element_types(vector)
    return common_numeric_type(types)


def promote_vector(vector: list) -> list:
    """Promote a vector of numeric values to a common type."""
    target_type = vector_common_numeric_type(vector)
    return promote_to_vector_of_numeric(vector, target_type)


def is_vector_ranges(ranges: list[tuple[int, int]]) -> bool:
    """Check if a vector is a list of ranges."""
    if len(ranges) == 0:
        return False

    def is_interval(x: tuple[int, int]) -> bool:
        return isinstance(x, tuple) and len(x) == 2 and all(isinstance(y, int) for y in x) and x[0] <= x[1]

    if not all(is_interval(interval) for interval in ranges):
        return False
    for i in range(len(ranges) - 1):
        if ranges[i][1] != ranges[i + 1][0]:
            return False
    return True


def is_vector_csr(vector: list[int]) -> bool:
    """Check if a vector is a CSR row start index vector."""
    if len(vector) < 2:
        return False
    if not all(isinstance(x, int) for x in vector):
        return False
    if vector[0] != 0:
        return False
    if not all(vector[i] <= vector[i + 1] for i in range(len(vector) - 1)):
        return False
    return True


def csr_to_ranges(csr: list[int]) -> list[tuple[int, int]]:
    """Convert row start indices to ranges."""
    assert is_vector_csr(csr), "input is not a valid CSR vector"
    ranges = [(csr[i], csr[i + 1]) for i in range(len(csr) - 1)]
    return ranges


def ranges_to_csr(ranges: list[tuple[int, int]]) -> list[int]:
    """Convert ranges to CSR row start indices."""
    assert is_vector_ranges(ranges), "input is not a valid ranges vector"
    csr = [interval[0] for interval in ranges]
    csr.append(ranges[-1][-1])
    return csr
