"""
Utilities for packing and unpacking composite datatypes (structs).
"""

from dataclasses import dataclass
from fractions import Fraction
from types import SimpleNamespace

from bitstring import BitArray

from .api import *
from .utils import split_bytes


@dataclass(frozen=False)
class Padding:
    """A simple range datatype representing [start, end)."""

    padding: int

    @classmethod
    def from_namespace(cls, data: SimpleNamespace) -> "Padding":
        return cls(padding=data.padding)

    def validate(self):
        if self.padding <= 0:
            raise ValueError(f"Padding must be positive ({self.padding})")


@dataclass(frozen=False)
class Field:
    """A field in a composite datatype."""

    name: str
    type: str
    size: Optional[int] = (
        None  # number of bits for values of fixed-size types; None for variable-size types (string, rational)
    )
    lower: Optional[float] = None  # lower bound (for numeric types)
    upper: Optional[float] = None  # upper bound (for numeric types)
    offset: Optional[float] = None  # lower value offset (for numeric types)

    @classmethod
    def from_namespace(cls, data: SimpleNamespace) -> "Field":
        return cls(
            name=data.name,
            type=data.type,
            size=getattr(data, "size", None),
            lower=getattr(data, "lower", None),
            upper=getattr(data, "upper", None),
            offset=getattr(data, "offset", None),
        )

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


class CompositeType:
    """A composite datatype consisting of fields and paddings."""

    def __init__(self, fields: list[Field | Padding] = []):
        self._fields = fields

    @classmethod
    def from_namespace(cls, data: list[SimpleNamespace]) -> "CompositeType":
        fields = []
        for item in data:
            if hasattr(item, "padding"):
                fields.append(Padding.from_namespace(item))
            else:
                fields.append(Field.from_namespace(item))
        return cls(fields)

    def __iter__(self):
        return iter(self._fields)

    def __getitem__(self, index):
        return self._fields[index]

    def __len__(self):
        return len(self._fields)

    def append(self, field: Field | Padding):
        self._fields.append(field)

    @property
    def fields(self):
        return self._fields

    def validate(self):
        for item in self._fields:
            item.validate()

    @staticmethod
    def new_padding(total_bits: int) -> Padding | None:
        """Create a new padding field to align the total_bits to the next byte boundary."""
        padding = (8 - total_bits % 8) % 8
        if padding > 0:
            return Padding(padding)
        return None

    def add_paddings(self):
        """Add padding fields to properly align the composite to byte boundaries."""
        new_fields = []
        total_bits = 0
        for field in self._fields:
            if isinstance(field, Padding):
                total_bits += field.padding
            else:
                # isinstance(field, Field)
                if field.type in {"string", "rational"}:
                    # add padding to next byte boundary
                    padding = self.new_padding(total_bits)
                    if padding is not None:
                        new_fields.append(padding)
                        total_bits += padding.padding
                else:
                    assert field.size is not None
                    total_bits += field.size
            new_fields.append(field)
        # add final padding to byte boundary
        padding = self.new_padding(total_bits)
        if padding is not None:
            new_fields.append(padding)
        self._fields = new_fields


class CompositePacker:
    """Utility class for packing composite datatypes into a bytestring."""

    def __init__(self):
        self.buffer = BitArray()  # bit buffer, MSB at [0]
        self.bytestring = bytes()  # output bytestring, little-endian order

    def assert_buffer_empty(self):
        if len(self.buffer) > 0:
            raise RuntimeError("expected the buffer to be empty")

    def flush_buffer(self):
        """Flush full bytes from the buffer to the bytestring."""
        while len(self.buffer) >= 8:  # append one byte at a time so that the bytestring is little-endian
            self.buffer, bits = self.buffer[:-8], self.buffer[-8:]  # get new bits from the end (LSB side)
            new_bytes = bits.tobytes()
            self.bytestring += new_bytes

    def append_to_buffer(self, bits: BitArray):
        """Append bits to the buffer flush full bytes to the bytestring."""
        self.buffer = bits + self.buffer  # prepend to the start (MSB side)
        self.flush_buffer()

    def add_padding(self, num_bits: int):
        """Add padding bits to the buffer."""
        assert num_bits > 0
        self.append_to_buffer(BitArray(uint=0, length=num_bits))

    def pack_field(self, field: Field, value: object):
        """Pack a single field into the buffer or the bytestring."""
        if field.type in ["string", "rational"]:
            self.assert_buffer_empty()
        if field.type == "string":
            assert isinstance(value, str)
            self.bytestring += string_pack(value)
        elif field.type == "rational":
            assert isinstance(value, Fraction)
            self.bytestring += rational_pack(value)
        else:
            # send fixed-size types to the buffer
            value_bits = None
            if field.type == "bool":
                assert isinstance(value, bool)
                value_bits = boolean_pack(value, field.size)
            else:
                assert isinstance(value, (int, float))
                assert field.size is not None
                value_bits = numeric_pack(value, field.type, field.size)
            self.append_to_buffer(value_bits)

    def pack_fields(self, value_type: CompositeType, values: dict[str, object]) -> bytes:
        for field in value_type:
            if isinstance(field, Padding):
                self.add_padding(field.padding)
                continue
            if field.name not in values:
                raise ValueError(f"Missing value for field {field.name}")
            self.pack_field(field, values[field.name])
        self.assert_buffer_empty()
        return self.bytestring


class CompositeUnpacker:
    """Utility class for unpacking composite datatypes from a bytestring."""

    def __init__(self, bytestring: bytes):
        self.bytestring = bytestring  # input bytestring, little-endian order
        self.buffer = BitArray()  # bit buffer, MSB at [0]

    def assert_buffer_empty(self):
        if len(self.buffer) > 0:
            raise RuntimeError("expected the buffer to be empty")

    def align_buffer(self, num_bits: int):
        """Ensure the buffer has the required number ofbits."""
        if len(self.buffer) >= num_bits:
            return
        num_bytes_needed = (num_bits - len(self.buffer) + 7) // 8
        assert len(self.bytestring) >= num_bytes_needed, "not enough data to fill the buffer"
        for _ in range(num_bytes_needed):  # read one byte at a time since the bytestring is little-endian
            next_bytes, self.bytestring = split_bytes(self.bytestring, 1)
            self.buffer = BitArray(bytes=next_bytes) + self.buffer  # prepend to the buffer to keep MSB at [0]

    def extract_from_buffer(self, num_bits: int):
        """Extract the given number of bits from the buffer."""
        assert num_bits >= 0
        self.align_buffer(num_bits)
        bits = self.buffer[-num_bits:]  # remove from the end (LSB side)
        self.buffer = self.buffer[:-num_bits]
        return bits

    def skip_padding(self, num_bits: int):
        self.extract_from_buffer(num_bits)

    def unpack_field(self, field: Field) -> object:
        """Unpack a single field from the buffer or the bytestring."""
        if field.type in ["string", "rational"]:
            self.assert_buffer_empty()
        if field.type == "string":
            value, self.bytestring = string_unpack(self.bytestring)
        elif field.type == "rational":
            value, self.bytestring = rational_unpack(self.bytestring)
        else:
            # fixed-size types come from the buffer
            assert field.size is not None
            bits = self.extract_from_buffer(field.size)
            if field.type == "bool":
                value = boolean_unpack(bits)
            else:
                value = numeric_unpack(bits, field.type)
        return value

    def unpack_fields(self, value_type: CompositeType) -> dict[str, object]:
        values = dict()
        for field in value_type:
            if isinstance(field, Padding):
                self.skip_padding(field.padding)
                continue
            values[field.name] = self.unpack_field(field)
        self.assert_buffer_empty()
        return values


def composite_pack(value_type: CompositeType, values: dict[str, object]) -> bytes:
    """Convert a composite datatype to a BitArray."""
    return CompositePacker().pack_fields(value_type, values)


def composite_unpack(bytestring: bytes, value_type: CompositeType) -> dict[str, object]:
    """Convert a BitArray back to a composite datatype."""
    return CompositeUnpacker(bytestring).unpack_fields(value_type)
