from dataclasses import dataclass
from typing import List, Optional
import binascii

@dataclass
class MBusFrame:
    start: int
    l_field: int
    c_field: int
    m_field: str
    a_field: int
    ci_field: int
    data: bytes
    checksum: int
    stop: int

class MBusFrameDecoder:
    def __init__(self, hex_string: str):
        # Convert hex string to bytes, removing any whitespace
        self.raw_bytes = bytes.fromhex(hex_string.replace(" ", ""))
        self.position = 0
        
    def read_byte(self) -> int:
        """Read a single byte and advance position"""
        byte = self.raw_bytes[self.position]
        self.position += 1
        return byte
    
    def read_bytes(self, count: int) -> bytes:
        """Read specified number of bytes and advance position"""
        data = self.raw_bytes[self.position:self.position + count]
        self.position += count
        return data
    
    def decode_manufacturer(self, man_bytes: bytes) -> str:
        """Decode manufacturer ID according to EN 61107"""
        man_id = ((man_bytes[0] & 0x0F) << 8) + man_bytes[1]
        char1 = ((man_id >> 10) & 0x1F) + 64
        char2 = ((man_id >> 5) & 0x1F) + 64
        char3 = (man_id & 0x1F) + 64
        return chr(char1) + chr(char2) + chr(char3)

    def calculate_checksum(self, l_field: int, c_field: int, a_field: int, ci_field: int, data: bytes) -> int:
        """Calculate M-Bus checksum (sum of all bytes from L-Field to last data byte)"""
        checksum = l_field + c_field + a_field + ci_field
        for byte in data:
            checksum += byte
        return checksum & 0xFF  # Take only the least significant byte

    def verify_checksum(self, calculated: int, received: int) -> bool:
        """Verify if calculated checksum matches received checksum"""
        return calculated == received

    def decode(self) -> Optional[MBusFrame]:
        try:
            # Store total frame length for validation
            total_length = len(self.raw_bytes)
            
            # Check start character
            start = self.read_byte()
            if start != 0x7E:
                raise ValueError(f"Invalid start character: {hex(start)}")
            
            # Length field - but don't trust it blindly
            l_field = self.read_byte()
            
            # Control field
            c_field = self.read_byte()
            
            # Address field
            a_field = self.read_byte()
            
            # Control Information field
            ci_field = self.read_byte()
            
            # Calculate actual remaining bytes (excluding checksum and stop)
            remaining_bytes = total_length - 7  # Subtract header (5), checksum (1), and stop (1)
            
            # Read all remaining data bytes except last 2 (checksum and stop)
            data = self.read_bytes(remaining_bytes)
            
            # Checksum
            checksum = self.read_byte()
            
            # Stop character
            stop = self.read_byte()
            if stop != 0x7E:
                raise ValueError(f"Invalid stop character: {hex(stop)}")
            
            # Calculate and verify checksum
            calculated_checksum = self.calculate_checksum(l_field, c_field, a_field, ci_field, data)
            checksum_valid = self.verify_checksum(calculated_checksum, checksum)
            print(f"Valid checksum: {checksum_valid} / {calculated_checksum:02X}")
            print
            # Create frame object
            frame = MBusFrame(
                start=start,
                l_field=l_field,
                c_field=c_field,
                a_field=a_field,
                ci_field=ci_field,
                data=data,
                checksum=checksum,
                stop=stop,
                m_field="N/A"  # Manufacturer ID might be part of data in this format
            )
            
            return frame
            
        except Exception as e:
            print(f"Error decoding frame: {str(e)}")
            return None

def print_frame_details(frame: MBusFrame, calculated_checksum: int, checksum_valid: bool):
    """Print decoded frame details in a formatted way"""
    print("\nDecoded M-Bus Frame:")
    print("===================")
    print(f"Start Character: 0x{frame.start:02X}")
    print(f"L-Field (raw): 0x{frame.l_field:02X} ({frame.l_field})")
    print(f"Control Field: 0x{frame.c_field:02X}")
    print(f"Address Field: 0x{frame.a_field:02X}")
    print(f"CI Field: 0x{frame.ci_field:02X}")
    
    print("\nData Blocks (hex):")
    # Print data in chunks of 16 bytes
    for i in range(0, len(frame.data), 16):
        chunk = frame.data[i:i+16]
        hex_str = ' '.join([f'{b:02X}' for b in chunk])
        print(f"  {hex_str}")
    
    print(f"\nActual Data Length: {len(frame.data)} bytes")
    print(f"Received Checksum: 0x{frame.checksum:02X}")
    #print(f"Calculated Checksum: 0x{calculated_checksum:02X}")
    print(f"Checksum Valid: {'Yes' if checksum_valid else 'No'}")
    print(f"Stop Character: 0x{frame.stop:02X}")

# Your frame
frame_hex = "7ea067ceff031338bde6e700db084c475a6773745ddd4f2000e8c3f44d3b65fcf023f403e19036a1c9f5e6eabdf04c40a4800b1509a2252881267d0b90e585eef07f57c90ad75192893725ae5f06bacee5a422d33f1705a1919765812e06910abfdb2beb901270657e"

# Decode the frame
decoder = MBusFrameDecoder(frame_hex)
frame = decoder.decode()
calculated_checksum = decoder.calculate_checksum(frame.l_field, frame.c_field, frame.a_field, frame.ci_field, frame.data)
checksum_valid = decoder.verify_checksum(calculated_checksum, frame.checksum)
if frame:
    print_frame_details(frame, decoder.calculate_checksum, checksum_valid)