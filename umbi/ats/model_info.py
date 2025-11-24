from dataclasses import dataclass


@dataclass
class ModelInfo:
    """Container to store information about the model."""

    name: str | None = None
    version: str | None = None
    authors: list[str] | None = None
    description: str | None = None
    comment: str | None = None
    doi: str | None = None
    url: str | None = None
