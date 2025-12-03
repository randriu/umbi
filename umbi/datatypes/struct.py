"""
Composite datatype definitions.

This module contains the core classes for defining composite datatypes (structs).
The serialization operations for composites remain in umbi.binary.composites.
"""

from dataclasses import dataclass, field

from .common_type import CommonType


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
    size: int | None = (
        None  # number of bits for values of fixed-size types; None for variable-size types (string, rational)
    )
    lower: float | None = None  # lower bound (for numeric types)
    upper: float | None = None  # upper bound (for numeric types)
    offset: float | None = None  # lower value offset (for numeric types)

    def validate(self):
        if self.type not in [
            CommonType.BOOLEAN,
            CommonType.INT,
            CommonType.UINT,
            CommonType.DOUBLE,
            CommonType.RATIONAL,
            CommonType.STRING,
        ]:
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

    def validate(self):
        for item in self.fields:
            item.validate()
        # TODO check alignment

    def __str__(self) -> str:
        lines = [f"struct (alignment={self.alignment}):"]
        for f in self.fields:
            lines.append(f"  {f}")
        return "\n".join(lines)

    def __iter__(self):
        return iter(self.fields)

    def bits_to_pad(self) -> int:
        """Calculate the number of padding bits needed to align current struct to a full byte."""
        total_bits = 0
        for f in self.fields:
            if isinstance(f, StructPadding):
                total_bits += f.padding
            else:  # isinstance(f, StructAttribute)
                if f.size is None:
                    # variable-size field will be byte-aligned, skip
                    total_bits = 0
                else:
                    total_bits += f.size
        return (8 - total_bits % 8) % 8

    def add_padding(self, num_bits: int) -> None:
        assert isinstance(num_bits, int) and num_bits >= 0
        if num_bits == 0:
            return
        self.fields.append(StructPadding(padding=num_bits))

    def pad_to_byte(self, num_bits: int | None) -> None:
        """Add padding bits to the struct."""
        if num_bits is None:
            num_bits = self.bits_to_pad()
        assert isinstance(num_bits, int) and num_bits >= 0
        self.add_padding(num_bits)
        # TODO validate alignment?

    def add_attribute(self, name: str, type: CommonType) -> None:
        """Add an attribute field to the struct."""
        size = None
        if type in [CommonType.STRING, CommonType.RATIONAL]:
            # add padding to byte-align before string/rational
            self.add_padding(self.bits_to_pad())
        else:
            size = {
                CommonType.BOOLEAN: 1,
                CommonType.INT: 64,
                CommonType.DOUBLE: 64,
            }[type]
        self.fields.append(StructAttribute(name=name, type=type, size=size))
