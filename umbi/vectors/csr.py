"""
Auxiliary vector operations.
"""

# from dataclasses import dataclass

# @dataclass(frozen=False)
# class Range:
#     """A simple range datatype representing [start, end)."""
#     start: int
#     end: int

#     def __post_init__(self):
#         self.validate()

#     def validate(self):
#         if self.start > self.end:
#             raise ValueError(f"Range start ({self.start}) must be <= end ({self.end})")

#     def length(self) -> int:
#         """Return the length of the range."""
#         return self.end - self.start

#     def to_tuple(self) -> tuple[int, int]:
#         """Convert to tuple for compatibility with existing code."""
#         return (self.start, self.end)

#     @staticmethod
#     def from_tuple(t: tuple[int, int]) -> 'Range':
#         """Create a Range from a tuple."""
#         if len(t) != 2:
#             raise ValueError("Tuple must have exactly two elements")
#         return Range(t[0], t[1])


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
