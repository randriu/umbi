from umbi import binary
from bitstring import BitArray

def main():

    def print_bits(bits: BitArray):
        bitstr = bits.bin
        print()
        for i in range(0, len(bitstr), 8):
            byte = bitstr[i:i+8]
            print(byte)

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


    # handle composite data types:
    # fields = [
    #     binary.Field("v0", "bool", 2),
    #     binary.Field("v1", "uint", 7),
    #     binary.Field("v2", "string", None),
    #     binary.Field("v3", "bool", 3),
    # ]
    # values = {
    #     "v0": True,
    #     "v1": 27,
    #     "v2": "ab",
    #     "v3": True,
    # }

    
    bytestring,field_info = binary.composite_to_bytes(fields,values)
    print(field_info)
    bitarr = BitArray(bytes=bytestring)
    print_bits(bitarr)



if __name__ == "__main__":
    main()