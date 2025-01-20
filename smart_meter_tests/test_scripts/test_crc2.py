def crc16_ansi(data: bytes):
    crc = 0xFFFF  # Initial CRC value
    polynomial = 0x8005  # Polynomial used in the M-Bus CRC

    for byte in data:
        crc ^= byte << 8  # XOR the byte with the high byte of the CRC

        for _ in range(8):  # Process each bit of the byte
            if crc & 0x8000:  # If MSB is set
                crc = (crc << 1) ^ polynomial  # Shift left and XOR with polynomial
            else:
                crc <<= 1  # Just shift left
            crc &= 0xFFFF  # Ensure CRC remains 16-bit

    return crc


# Adjusted frame (removed first byte and CRC bytes)
frame_hex = "a067ceff031338bde6e700db084c475a6773745ddd4f2000e8c3f44d3b65fcf023f403e19036a1c9f5e6eabdf04c40a4800b1509a2252881267d0b90e585eef07f57c90ad75192893725ae5f06bacee5a422d33f1705a1919765812e06910abfdb2beb90127065"
frame_hex = "db084c475a6773745ddd4f2000e8c3f44d3b65fcf023f403e19036a1c9f5e6eabdf04c40a4800b1509a2252881267d0b90e585eef07f57c90ad75192893725ae5f06bacee5a422d33f1705a1919765812e06910abfdb2beb9012"
frame_bytes = bytes.fromhex(frame_hex)

# Calculate CRC
crc_result = crc16_ansi(frame_bytes)
print(f"CRC Result: {crc_result:04X}")
