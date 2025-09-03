"""
Auxiliary vector operations.
"""


def row_start_to_ranges(row_start: list) -> list[tuple[int, int]]:
    """Convert row start indices to ranges."""
    ranges = []
    num_rows = len(row_start) - 1
    for row in range(num_rows):
        ranges.append((row_start[row], row_start[row + 1]))
    return ranges


def ranges_to_row_start(ranges: list[tuple[int, int]]) -> list[int]:
    """Convert ranges to row start indices."""
    row_start = [interval[0] for interval in ranges]
    row_start.append(ranges[-1][-1] + 1)
    assert len(row_start) == len(ranges) + 1
    return row_start


def indices_to_bitvector(vector: list[int], num_entries: int) -> list[bool]:
    """Convert a list of unsigned integers to a bitvector.

    :param vector: a list of unsigned integers
    :param num_entries: the size of the resulting bitvector, must be no smaller than max(vector)
    """
    assert max(vector) < num_entries
    bitvector = [False] * num_entries
    for x in vector:
        bitvector[x] = True
    return bitvector


def bitvector_to_indices(bitvector: list[bool]) -> list[int]:
    """Convert a bitvector to a list of indices set to True.

    :param bitvector: a list of bools
    """
    return [i for i, bit in enumerate(bitvector) if bit]
