from bitstring import BitArray

import umbi
import umbi.binary as binary


def main():

    def print_bytes(bytestring: bytes):
        for byte in bytestring:
            print(f"{byte:08b}", end=" ")
        print()

    # bits = BitArray(int=-16897, length=16) + BitArray(uint=56, length=8)
    # for i in range(0, len(bits.bin), 8):
    #     byte = bits.bin[i:i+8]
    #     print(byte)
    # exit()

    fields = [
        binary.Field("v0", "int", 8),
        binary.Field("v1", "int", 16),
    ]
    values = {
        "v0": 56,
        "v1": -16897,
    }

    fields = [
        binary.Field("v0", "bool", 2),
        binary.Field("v1", "uint", 7),
        binary.Padding(7),
        binary.Field("v2", "string", None),
        binary.Field("v3", "bool", 3),
        binary.Padding(5),
    ]
    values = {
        "v0": True,
        "v1": 27,
        "v2": "hello",
        "v3": True,
    }

    bytestring, fields = binary.composite_pack(fields, values)
    print_bytes(bytestring)
    print(fields)

    values_out = binary.composite_unpack(bytestring, fields)
    print(values_out)


if __name__ == "__main__":
    main()
