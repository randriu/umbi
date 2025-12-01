"""
Utilities for packing and unpacking composite datatypes (structs).
"""

from fractions import Fraction

from bitstring import BitArray

from umbi.datatypes import (
    CommonType,
    Numeric,
    StructAttribute,
    StructPadding,
    StructType,
)

from .bitvectors import boolean_pack, boolean_unpack
from .floats import double_pack, double_unpack
from .integers import integer_pack, integer_unpack
from .rationals import rational_pack, rational_unpack
from .strings import string_pack, string_unpack
from .utils import split_bytes


class StructPacker:
    """Utility class for packing structs into a bytestring."""

    def __init__(self):
        self.buffer = BitArray()  # bit buffer, MSB at [0]
        self.bytestring = bytes()  # output bytestring, little-endian order

    def assert_buffer_empty(self):
        if len(self.buffer) > 0:
            raise RuntimeError("expected the buffer to be empty")

    def flush_buffer(self):
        """Flush full bytes from the buffer to the bytestring."""
        while len(self.buffer) >= 8:  # append one byte at a time so that the bytestring is little-endian
            self.buffer, bits = (
                self.buffer[:-8],
                self.buffer[-8:],
            )  # get new bits from the end (LSB side)
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

    def pack_attribute(self, field: StructAttribute, value: object):
        """Pack a single attribute into the buffer or the bytestring."""
        if field.type in [CommonType.STRING, CommonType.RATIONAL]:
            # expected to be byte-aligned before packing string/rational
            self.assert_buffer_empty()
            # send byte-aligned output directly to the bytestring
            if field.type == CommonType.STRING:
                assert isinstance(value, str)
                self.bytestring += string_pack(value)
            else:  # field.type == CommonType.RATIONAL:
                assert isinstance(value, Fraction)
                self.bytestring += rational_pack(value)
            return
        # the remaining datatypes are bitstrings that go into the buffer
        value_bits = None
        if field.type == CommonType.BOOLEAN:
            assert isinstance(value, bool)
            value_bits = boolean_pack(value, field.size)
        elif field.type in [CommonType.INT, CommonType.UINT]:
            assert isinstance(value, int)
            signed = field.type == CommonType.INT
            assert field.size is not None
            value_bits = integer_pack(value, field.size, signed)
        elif field.type == CommonType.DOUBLE:
            assert isinstance(value, float)
            assert field.size == 64, f"expected {field.size} to be 64 for double type"
            value_bits = double_pack(value)
        else:
            raise ValueError(f"unsupported field type: {field.type}")
        self.append_to_buffer(value_bits)

    def pack_struct(self, value_type: StructType, values: dict[str, object]) -> bytes:
        for field in value_type:
            if isinstance(field, StructPadding):
                self.add_padding(field.padding)
                continue
            assert isinstance(field, StructAttribute)
            self.pack_attribute(field, values[field.name])
        self.assert_buffer_empty()
        return self.bytestring


class StructUnpacker:
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

    def unpack_attribute(self, field: StructAttribute) -> str | bool | Numeric:
        """Unpack a single field from the buffer or the bytestring."""
        if field.type in [CommonType.STRING, CommonType.RATIONAL]:
            self.assert_buffer_empty()
            if field.type == CommonType.STRING:
                value, self.bytestring = string_unpack(self.bytestring)
                return value
            elif field.type == CommonType.RATIONAL:
                value, self.bytestring = rational_unpack(self.bytestring)
                return value
        # fixed-size types come from the buffer
        assert field.size is not None
        bits = self.extract_from_buffer(field.size)
        if field.type == CommonType.BOOLEAN:
            return boolean_unpack(bits)
        elif field.type in [CommonType.INT, CommonType.UINT]:
            signed = field.type == CommonType.INT
            return integer_unpack(bits, signed)
        elif field.type == CommonType.DOUBLE:
            return double_unpack(bits)
        else:
            raise ValueError(f"unsupported field type: {field.type}")

    def unpack_struct(self, value_type: StructType) -> dict[str, object]:
        name_value = dict()
        for field in value_type:
            if isinstance(field, StructPadding):
                self.skip_padding(field.padding)
                continue
            name_value[field.name] = self.unpack_attribute(field)
        self.assert_buffer_empty()
        return name_value


def struct_pack(value_type: StructType, values: dict[str, object]) -> bytes:
    """Convert a composite datatype to a BitArray."""
    return StructPacker().pack_struct(value_type, values)


def struct_unpack(bytestring: bytes, value_type: StructType) -> dict[str, object]:
    """Unpack a BitArray to a composite datatype."""
    return StructUnpacker(bytestring).unpack_struct(value_type)
