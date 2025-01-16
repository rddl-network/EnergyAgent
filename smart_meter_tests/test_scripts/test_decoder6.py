from dataclasses import dataclass
from typing import List, Optional, Dict
import binascii

@dataclass
class DLMSFrame:
    start: int
    format_byte: int
    control: int
    address: int
    ci_field: int
    header_data: bytes
    payload: bytes
    checksum: int
    stop: int

class LandisGyrDLMSDecoder:
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

    def calculate_hdlc_fcs(self, data: bytes) -> int:
        """Calculate HDLC Frame Check Sequence (FCS)"""
        fcs = 0xFFFF
        for byte in data:
            fcs ^= byte
            for _ in range(8):
                if fcs & 0x0001:
                    fcs = (fcs >> 1) ^ 0x8408
                else:
                    fcs = fcs >> 1
        return (~fcs) & 0xFFFF

    def calculate_checksums(self, frame_bytes: bytes) -> Dict[str, int]:
        """Calculate different checksum variants"""
        checksums = {}
        
        # Try different ranges for checksum calculation
        data_for_checksum = frame_bytes[1:-2]  # All except start/stop flags
        
        # HDLC FCS (Frame Check Sequence)
        checksums["hdlc_fcs"] = self.calculate_hdlc_fcs(data_for_checksum) & 0xFF
        
        # Simple XOR of all bytes
        xor_sum = 0
        for b in data_for_checksum:
            xor_sum ^= b
        checksums["xor"] = xor_sum
        
        # CRC-8
        crc8 = 0
        for b in data_for_checksum:
            crc8 ^= b
            for _ in range(8):
                if crc8 & 0x80:
                    crc8 = (crc8 << 1) ^ 0x07
                else:
                    crc8 <<= 1
                crc8 &= 0xFF
        checksums["crc8"] = crc8
        
        return checksums

    def decode(self) -> Optional[tuple[DLMSFrame, Dict[str, int]]]:
        try:
            original_bytes = self.raw_bytes[:]  # Keep original for checksum calc
            
            # Parse frame
            start = self.read_byte()
            if start != 0x7E:
                raise ValueError(f"Invalid start character: {hex(start)}")
            
            format_byte = self.read_byte()
            control = self.read_byte()
            address = self.read_byte()
            ci_field = self.read_byte()
            
            # Read common header data (as observed in multiple frames)
            header_data = self.read_bytes(11)  # Length of common header data
            
            # Calculate remaining payload length
            remaining_bytes = len(self.raw_bytes) - self.position - 2  # -2 for checksum and stop
            payload = self.read_bytes(remaining_bytes)
            
            checksum = self.read_byte()
            stop = self.read_byte()
            
            if stop != 0x7E:
                raise ValueError(f"Invalid stop character: {hex(stop)}")
            
            # Create frame object
            frame = DLMSFrame(
                start=start,
                format_byte=format_byte,
                control=control,
                address=address,
                ci_field=ci_field,
                header_data=header_data,
                payload=payload,
                checksum=checksum,
                stop=stop
            )
            
            # Calculate different checksum variants
            checksums = self.calculate_checksums(original_bytes)
            
            return frame, checksums
            
        except Exception as e:
            print(f"Error decoding frame: {str(e)}")
            return None

def print_frame_analysis(frames: List[str]):
    """Analyze multiple frames to find patterns"""
    print("\nDLMS Frame Analysis:")
    print("===================")
    
    for i, frame_hex in enumerate(frames, 1):
        print(f"\nFrame {i}:")
        decoder = LandisGyrDLMSDecoder(frame_hex)
        result = decoder.decode()
        
        if result:
            frame, checksums = result
            print(f"Format Byte: 0x{frame.format_byte:02X}")
            print(f"Control: 0x{frame.control:02X}")
            print(f"Address: 0x{frame.address:02X}")
            print(f"CI Field: 0x{frame.ci_field:02X}")
            print(f"Common Header: {frame.header_data.hex()}")
            print(f"Payload Length: {len(frame.payload)} bytes")
            print(f"Received Checksum: 0x{frame.checksum:02X}")
            print("\nCalculated Checksums:")
            for name, value in checksums.items():
                match = "✓" if value == frame.checksum else "✗"
                print(f"- {name}: 0x{value:02X} {match}")

# Test frames
frames = [
    "7ea067ceff031338bde6e700db084c475a6773745ddd4f2000e8c3f44d3b65fcf023f403e19036a1c9f5e6eabdf04c40a4800b1509a2252881267d0b90e585eef07f57c90ad75192893725ae5f06bacee5a422d33f1705a1919765812e06910abfdb2beb901270657e",
    "7ea067ceff031338bde6e700db084c475a6773745ddd4f2000e8cacbb3176bfb6d62b4340d8f1faed60d316317766f277899e0f285282779d1acf4b02960dd76d66210a77bddfb19338ce2ca4f41a083737cefc2d0134b3a5194c2656cc2647be83a21acaf1c17287e",
    "7ea067ceff031338bde6e700db084c475a6773745ddd4f2000e8caca3a52a875c7500f842da0ca6ac1d98c0abbf61ed49e3d6eb3d4ff133324b53371759b9a470b0ce2c1efeb8c20179cdb68b14b7bd6540cb596c91382e18b88bc04ecdc3104dadaeb5dbfa074cb7e",
    "7ea067ceff031338bde6e700db084c475a6773745ddd4f2000e8cac64953ac1f7aa3185c28b0642bd7bdf041628d27348f232b39484030207c9a272f68945a771960d72c2bef6d22660416c9e05436aecaa6167fe63b85473505cd4bfaadb477fd120be1ef9552d97e"
]

print_frame_analysis(frames)