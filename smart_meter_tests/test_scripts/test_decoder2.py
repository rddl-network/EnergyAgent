from dataclasses import dataclass
from typing import List, Optional
import binascii

@dataclass
class MBusFrame:
    start: int           # Start character (0x7E)
    l_field: int         # Length field
    c_field: int         # Control field
    m_field: int         # Manufacturer ID
    a_field: int         # Address field
    ci_field: int        # Control Information field
    data: bytes          # User data
    checksum: int        # Checksum
    stop: int           # Stop character (0x7E)

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
        # Convert 2 bytes to 3 characters according to M-Bus specification
        man_id = ((man_bytes[0] & 0x0F) << 8) + man_bytes[1]
        char1 = ((man_id >> 10) & 0x1F) + 64
        char2 = ((man_id >> 5) & 0x1F) + 64
        char3 = (man_id & 0x1F) + 64
        return chr(char1) + chr(char2) + chr(char3)

    def decode(self) -> Optional[MBusFrame]:
        try:
            # Check start character
            start = self.read_byte()
            if start != 0x7E:
                raise ValueError(f"Invalid start character: {hex(start)}")
            
            # Length field
            l_field = self.read_byte()
            
            # Control field
            c_field = self.read_byte()
            
            # Address field
            a_field = self.read_byte()
            
            # Control Information field
            ci_field = self.read_byte()
            
            # Manufacturer ID (2 bytes)
            m_field_bytes = self.read_bytes(2)
            m_field_str = self.decode_manufacturer(m_field_bytes)
            
            # Calculate remaining data length (excluding checksum and stop byte)
            data_length = l_field - 3  # Subtract CI field and manufacturer ID
            
            # Read user data
            data = self.read_bytes(data_length)
            
            # Checksum
            checksum = self.read_byte()
            
            # Stop character
            stop = self.read_byte()
            if stop != 0x7E:
                raise ValueError(f"Invalid stop character: {hex(stop)}")
            
            # Create frame object
            frame = MBusFrame(
                start=start,
                l_field=l_field,
                c_field=c_field,
                m_field=m_field_str,
                a_field=a_field,
                ci_field=ci_field,
                data=data,
                checksum=checksum,
                stop=stop
            )
            
            return frame
            
        except Exception as e:
            print(f"Error decoding frame: {str(e)}")
            return None

def print_frame_details(frame: MBusFrame):
    """Print decoded frame details in a formatted way"""
    print("\nDecoded M-Bus Frame:")
    print("===================")
    print(f"Start Character: 0x{frame.start:02X}")
    print(f"Length Field: {frame.l_field}")
    print(f"Control Field: 0x{frame.c_field:02X}")
    print(f"Address Field: 0x{frame.a_field:02X}")
    print(f"CI Field: 0x{frame.ci_field:02X}")
    print(f"Manufacturer ID: {frame.m_field}")
    print("\nData Blocks (hex):")
    # Print data in chunks of 16 bytes
    for i in range(0, len(frame.data), 16):
        chunk = frame.data[i:i+16]
        hex_str = ' '.join([f'{b:02X}' for b in chunk])
        print(f"  {hex_str}")
    print(f"\nChecksum: 0x{frame.checksum:02X}")
    print(f"Stop Character: 0x{frame.stop:02X}")

# Your frame
frame_hex = "7ea067ceff031338bde6e700db084c475a6773745ddd4f2000e8c3f44d3b65fcf023f403e19036a1c9f5e6eabdf04c40a4800b1509a2252881267d0b90e585eef07f57c90ad75192893725ae5f06bacee5a422d33f1705a1919765812e06910abfdb2beb901270657e"

# Decode the frame
decoder = MBusFrameDecoder(frame_hex)
frame = decoder.decode()

if frame:
    print_frame_details(frame)