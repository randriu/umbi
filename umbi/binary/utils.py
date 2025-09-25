"""Utility functions for binary operations."""


def split_bytes(bytestring: bytes, length: int) -> tuple[bytes, bytes]:
    """Split a bytestring into chunks of the given size."""
    assert length > 0, "chunk size must be positive"
    assert len(bytestring) >= length, "data is shorter than the specified length"
    return bytestring[:length], bytestring[length:]