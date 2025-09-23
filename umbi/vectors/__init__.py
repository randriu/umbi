"""
umbi.vectors: Utilities for working with vector data structures.
"""

from .csr import *

__all__ = ["is_vector_csr", "is_vector_ranges", "csr_to_ranges", "ranges_to_csr"]
