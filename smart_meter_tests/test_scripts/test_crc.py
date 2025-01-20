def crc16_ccitt_false(data: bytearray) -> int:
    """CRC-16/CCITT-FALSE"""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc = crc << 1
            crc &= 0xFFFF
    return crc


def crc16_ccitt_true(data: bytearray) -> int:
    """CRC-16/CCITT-TRUE"""
    crc = 0x0000
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc = crc << 1
            crc &= 0xFFFF
    return crc


def crc16_xmodem(data: bytearray) -> int:
    """CRC-16/XMODEM"""
    crc = 0x0000
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc = crc << 1
            crc &= 0xFFFF
    return crc


def crc16_x25(data: bytearray) -> int:
    """CRC-16/X-25"""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0x8408
            else:
                crc = crc >> 1
    return crc ^ 0xFFFF


def crc16_modbus(data: bytearray) -> int:
    """CRC-16/MODBUS"""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc = crc >> 1
    return crc


def crc16_kermit(data: bytearray) -> int:
    """CRC-16/KERMIT"""
    crc = 0x0000
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0x8408
            else:
                crc = crc >> 1
    return crc


def crc16_dnp(data: bytearray) -> int:
    """CRC-16/DNP"""
    crc = 0x0000
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA6BC
            else:
                crc = crc >> 1
    return ~crc & 0xFFFF


def crc16_ibm(data: bytearray) -> int:
    """CRC-16/IBM"""
    crc = 0x0000
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0x8005
            else:
                crc = crc >> 1
    return crc


# Test frame
frame_hex = "7ea067ceff031338bde6e700db084c475a6773745ddd4f2000e8c3f44d3b65fcf023f403e19036a1c9f5e6eabdf04c40a4800b1509a2252881267d0b90e585eef07f57c90ad75192893725ae5f06bacee5a422d33f1705a1919765812e06910abfdb2beb901270657e"
frame_hex = "4c475a6773745ddd4f2000e8c3f44d3b65fcf023f403e19036a1c9f5e6eabdf04c40a4800b1509a2252881267d0b90e585eef07f57c90ad75192893725ae5f06bacee5a422d33f1705a1919765812e06910abfdb2beb9012"
frame_bytes = bytearray.fromhex(frame_hex)

# Get data to check (excluding start flag, checksum, and end flag)
data_to_check = frame_bytes[1:-3]

# Calculate all variants
variants = [
    ("CRC-16/CCITT-FALSE", crc16_ccitt_false),
    ("CRC-16/CCITT-TRUE", crc16_ccitt_true),
    ("CRC-16/XMODEM", crc16_xmodem),
    ("CRC-16/X-25", crc16_x25),
    ("CRC-16/MODBUS", crc16_modbus),
    ("CRC-16/KERMIT", crc16_kermit),
    ("CRC-16/DNP", crc16_dnp),
    ("CRC-16/IBM", crc16_ibm),
]

print("Testing CRC variants...")
print("Looking for matches with 0x7065 or 0x6570")
print("=" * 50)

for name, func in variants:
    result = func(data_to_check)
    print(f"{name:20} : 0x{result:04X}")
    if result in [0x7065, 0x6570]:
        print("*** MATCH FOUND ***")

print("\nTesting byte-swapped results...")
print("=" * 50)

for name, func in variants:
    result = func(data_to_check)
    swapped = ((result >> 8) | (result << 8)) & 0xFFFF
    print(f"{name:20} : 0x{swapped:04X} (swapped)")
    if swapped in [0x7065, 0x6570]:
        print("*** MATCH FOUND ***")

# Also try with various initial values and XOR outputs
print("\nTrying variations with different initial values and XOR outputs...")
print("=" * 50)


def crc16_variant(data: bytearray, init_value: int, polynomial: int, final_xor: int = 0) -> int:
    crc = init_value
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ polynomial
            else:
                crc = crc << 1
            crc &= 0xFFFF
    return crc ^ final_xor


initial_values = [0x0000, 0xFFFF, 0x1D0F]
polynomials = [0x1021, 0x8005, 0x8408]
final_xors = [0x0000, 0xFFFF]

for init in initial_values:
    for poly in polynomials:
        for xor_out in final_xors:
            result = crc16_variant(data_to_check, init, poly, xor_out)
            print(f"Init=0x{init:04X}, Poly=0x{poly:04X}, XOR=0x{xor_out:04X} : 0x{result:04X}")
            if result in [0x7065, 0x6570]:
                print("*** MATCH FOUND ***")
