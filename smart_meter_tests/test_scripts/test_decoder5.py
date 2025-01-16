from dataclasses import dataclass
from typing import List, Optional, Dict
import binascii

@dataclass
class LandisGyrFrame:
    start: int
    format_byte: int  # Previously L-Field, might be format identifier
    c_field: int
    a_field: int
    ci_field: int
    data: bytes
    checksum: int
    stop: int

class LandisGyrDecoder:
    def __init__(self, hex_string: str):
        self.raw_bytes = bytes.fromhex(hex_string.replace(" ", ""))
        self.position = 0
        
    def read_byte(self) -> int:
        byte = self.raw_bytes[self.position]
        self.position += 1
        return byte
    
    def read_bytes(self, count: int) -> bytes:
        data = self.raw_bytes[self.position:self.position + count]
        self.position += count
        return data

    def calculate_checksums(self, format_byte: int, c_field: int, a_field: int, ci_field: int, data: bytes) -> Dict[str, int]:
        """Calculate different checksum variants for Landis+Gyr"""
        checksums = {}
        
        # Standard arithmetic sum
        sum1 = format_byte + c_field + a_field + ci_field
        for byte in data:
            sum1 += byte
        checksums["standard"] = sum1 & 0xFF
        
        # XOR-based checksum (common in some L+G devices)
        xor_sum = format_byte ^ c_field ^ a_field ^ ci_field
        for byte in data:
            xor_sum ^= byte
        checksums["xor_based"] = xor_sum
        
        # IEC 62056-21 style (from C-Field)
        sum3 = c_field + a_field + ci_field
        for byte in data:
            sum3 += byte
        checksums["iec62056"] = sum3 & 0xFF
        
        # Calculate BCC (Block Check Character) as per IEC 62056-21
        bcc = 0
        for byte in [c_field, a_field, ci_field] + list(data):
            bcc ^= byte
        checksums["bcc"] = bcc
        
        return checksums

    def decode(self) -> Optional[tuple[LandisGyrFrame, Dict[str, int]]]:
        try:
            total_length = len(self.raw_bytes)
            
            # Parse frame
            start = self.read_byte()
            if start != 0x7E:
                raise ValueError(f"Invalid start character: {hex(start)}")
            
            format_byte = self.read_byte()  # Might be format identifier rather than length
            c_field = self.read_byte()
            a_field = self.read_byte()
            ci_field = self.read_byte()
            
            remaining_bytes = total_length - 7
            data = self.read_bytes(remaining_bytes)
            
            checksum = self.read_byte()
            
            stop = self.read_byte()
            if stop != 0x7E:
                raise ValueError(f"Invalid stop character: {hex(stop)}")
            
            # Create frame object
            frame = LandisGyrFrame(
                start=start,
                format_byte=format_byte,
                c_field=c_field,
                a_field=a_field,
                ci_field=ci_field,
                data=data,
                checksum=checksum,
                stop=stop
            )
            
            # Calculate different checksum variants
            checksums = self.calculate_checksums(format_byte, c_field, a_field, ci_field, data)
            
            return frame, checksums
            
        except Exception as e:
            print(f"Error decoding frame: {str(e)}")
            return None

def print_frame_details(frame: LandisGyrFrame, checksums: Dict[str, int]):
    """Print decoded frame details with all checksum variants"""
    print("\nDecoded Landis+Gyr Frame:")
    print("========================")
    print(f"Start Character: 0x{frame.start:02X}")
    print(f"Format Byte: 0x{frame.format_byte:02X}")
    print(f"Control Field: 0x{frame.c_field:02X}")
    print(f"Address Field: 0x{frame.a_field:02X}")
    print(f"CI Field: 0x{frame.ci_field:02X}")
    
    print("\nData Blocks (hex):")
    for i in range(0, len(frame.data), 16):
        chunk = frame.data[i:i+16]
        hex_str = ' '.join([f'{b:02X}' for b in chunk])
        print(f"  {hex_str}")
    
    print(f"\nActual Data Length: {len(frame.data)} bytes")
    print(f"\nChecksum Analysis:")
    print(f"Received Checksum: 0x{frame.checksum:02X}")
    print("\nCalculated Checksum Variants:")
    for name, value in checksums.items():
        match = "✓" if value == frame.checksum else "✗"
        print(f"- {name.replace('_', ' ').title()}: 0x{value:02X} {match}")
    
    print(f"\nStop Character: 0x{frame.stop:02X}")

# Test with your frame
frame_hex = "7ea067ceff031338bde6e700db084c475a6773745ddd4f2000e8c3f44d3b65fcf023f403e19036a1c9f5e6eabdf04c40a4800b1509a2252881267d0b90e585eef07f57c90ad75192893725ae5f06bacee5a422d33f1705a1919765812e06910abfdb2beb901270657e"

# Decode the frame
decoder = LandisGyrDecoder(frame_hex)
result = decoder.decode()

if result:
    frame, checksums = result
    print_frame_details(frame, checksums)