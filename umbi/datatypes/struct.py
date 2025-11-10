"""
Composite datatype definitions.

This module contains the core classes for defining composite datatypes (structs).
The serialization operations for composites remain in umbi.binary.composites.
"""

from dataclasses import dataclass, field
from .common_type import *


@dataclass
class StructPadding:
    """Padding bits in a composite datatype."""

    padding: int

    def validate(self):
        if self.padding <= 0:
            raise ValueError(f"Padding must be positive ({self.padding})")


@dataclass
class StructAttribute:
    """A variable field in a composite datatype."""

    name: str
    type: CommonType
    size: int | None = None # number of bits for values of fixed-size types; None for variable-size types (string, rational)
    lower: float | None = None  # lower bound (for numeric types)
    upper: float | None = None  # upper bound (for numeric types)
    offset: float | None = None  # lower value offset (for numeric types)

    def validate(self):
        if self.type not in [CommonType.BOOLEAN, CommonType.INT, CommonType.UINT, CommonType.DOUBLE, CommonType.RATIONAL, CommonType.STRING]:
            raise ValueError(f"Unsupported field type: {self.type}")
        if self.size is None:
            if self.type in [CommonType.INT, CommonType.UINT]:
                raise ValueError("Field size must be specified for fixed-size types (int,uint)")
        else:
            if self.size <= 0:
                raise ValueError(f"Field size must be positive ({self.size})")
            elif self.type == CommonType.DOUBLE and self.size != 64:
                raise ValueError("Field size for double must be 64")


@dataclass
class StructType:
    """A composite datatype consisting of attributes and paddings."""

    alignment: int  # alignment in bits
    fields: list[StructPadding | StructAttribute] = field(default_factory=list)

    # @classmethod
    # def from_namespace(cls, data: SimpleNamespace) -> "StructType":
    #     fields = []
    #     for item in data.variables:
    #         if hasattr(item, "padding"):
    #             fields.append(StructPadding.from_namespace(item))
    #         else:
    #             fields.append(StructAttribute.from_namespace(item))
    #     return cls(data.alignment, fields)

    def validate(self):
        for item in self.fields:
            item.validate()
        #TODO check alignment
    
    def __str__(self) -> str:
        lines = [f"struct (alignment={self.alignment}):"]
        for f in self.fields:
            lines.append(f"  {f}")
        return "\n".join(lines)

    def __iter__(self):
        return iter(self.fields)
    