"""
BitArray field handling utilities.
"""

from fractions import Fraction
from dataclasses import dataclass
from bitstring import BitArray

from .api import *

@dataclass(frozen=False)
class Padding:
    """A simple range datatype representing [start, end)."""
    padding: int

    def __post_init__(self):
        self.validate()

    def validate(self):
        if self.padding <= 0:
            raise ValueError(f"Padding must be positive ({self.padding})")


@dataclass(frozen=False)
class Field:
    """A field in a composite datatype."""
    name: str
    type: str
    size: int | None # number of bits for values of fixed-size types; None for variable-size types (string, rational)

    def __post_init__(self):
        self.validate()

    def validate(self):
        if self.type not in ["bool", "int", "uint", "double", "rational", "string"]:
            raise ValueError(f"Unsupported field type: {self.type}")
        if self.size is None:
            if self.type not in ["rational", "string"]:
                raise ValueError("Field size must be specified for fixed-size types (bool,int,uint,double)")
        else:
            if self.size <= 0:
                raise ValueError(f"Field size must be positive ({self.size})")
            elif self.type == "double" and self.size != 64:
                raise ValueError("Field size for double must be 64")


def composite_to_bytes(fields: list[Field], values: dict[str, object], little_endian: bool = True) -> tuple[bytes, list[Field|Padding]]:
    """Convert a composite datatype to a BitArray."""
    bits = BitArray()
    fields_output = list[Field|Padding]()
    assert little_endian, "big-endianness for composite types is not supported"

    def pad_to_byte(bits: BitArray) -> int:
        """
        Add padding to align to the next byte boundary.
        :return: number of padding bits added
        """
        padding = (8 - (len(bits) % 8)) % 8
        bits.prepend(BitArray(length=padding))
        return padding

    def print_bits(bits: BitArray):
        bitstr = bits.bin
        print()
        for i in range(0, len(bitstr), 8):
            byte = bitstr[i:i+8]
            print(byte)

    for field in fields:
        print("-----", field.name)
        if field.name not in values:
            raise ValueError(f"Missing value for field {field.name}")
        if field.type in ["string", "rational"]:
            # strings and fractions must start on a full byte
            padding = pad_to_byte(bits)
            if padding > 0:
                fields_output.append(Padding(padding))
                print_bits(bits)
        value_bits = value_to_bits(values[field.name], field.type, field.size) # type: ignore
        print(">", value_bits.bin, "<")
        bits.prepend(value_bits) # prepend bits for little-endian
        fields_output.append(field)
        print_bits(bits)

    padding = pad_to_byte(bits)
    if padding > 0:
        fields_output.append(Padding(padding))
    print_bits(bits)
    bytestring = bits.tobytes()

    bytestring = bytes(reversed(bytestring)) # reverse bytes for little-endian
    return bytestring, fields_output
