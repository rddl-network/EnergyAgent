from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple
import binascii
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

@dataclass
class DLMSFrame:
    start: int
    format_byte: int
    control: int
    address: int
    ci_field: int
    header_data: bytes
    payload: bytes
    decrypted_payload: Optional[bytes]
    checksum: int
    stop: int

class LandisGyrDLMSDecoder:
    def __init__(self, hex_string: str, encryption_key: str = None, auth_key: str = None):
        self.raw_bytes = bytes.fromhex(hex_string.replace(" ", ""))
        self.encryption_key = bytes.fromhex(encryption_key) if encryption_key else None
        self.auth_key = bytes.fromhex(auth_key) if auth_key else None
        self.position = 0
        
    def read_byte(self) -> int:
        byte = self.raw_bytes[self.position]
        self.position += 1
        return byte
    
    def read_bytes(self, count: int) -> bytes:
        data = self.raw_bytes[self.position:self.position + count]
        self.position += count
        return data

    def decrypt_payload(self, encrypted_data: bytes, security_control: bytes) -> Optional[bytes]:
        """Decrypt payload using AES-GCM"""
        try:
            if not self.encryption_key:
                return None

            # Extract components from security_control and encrypted data
            # In DLMS/COSEM, typically:
            # - First byte is security control
            # - Next 12 bytes are usually IV/nonce
            # - Last 12 bytes are authentication tag
            # Adjust these values based on your specific implementation
            
            iv = encrypted_data[:12]  # Assuming 12-byte IV
            ciphertext = encrypted_data[12:-12]  # Encrypted payload
            auth_tag = encrypted_data[-12:]  # Authentication tag
            
            # Create AES-GCM cipher
            cipher = AES.new(self.encryption_key, AES.MODE_GCM, nonce=iv)
            
            # If we have security control, add it as associated data
            if security_control:
                cipher.update(security_control)
            
            # Decrypt and verify
            try:
                decrypted = cipher.decrypt_and_verify(ciphertext, auth_tag)
                return decrypted
            except ValueError as e:
                print(f"Decryption failed: {e}")
                return None
                
        except Exception as e:
            print(f"Error during decryption: {e}")
            return None

    def calculate_checksums(self, frame_bytes: bytes, decrypted_payload: Optional[bytes] = None) -> Dict[str, int]:
        """Calculate different checksum variants"""
        checksums = {}
        
        # If we have decrypted payload, try calculating checksums with it
        if decrypted_payload is not None:
            # Replace encrypted part with decrypted in frame copy
            modified_frame = bytearray(frame_bytes)
            payload_start = 16  # Adjust based on your frame structure
            modified_frame[payload_start:-2] = decrypted_payload
            frame_for_checksum = bytes(modified_frame)
        else:
            frame_for_checksum = frame_bytes

        # Calculate checksums excluding start/stop bytes
        data_for_checksum = frame_for_checksum[1:-2]

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

        # HDLC FCS-16
        fcs = 0xFFFF
        for b in data_for_checksum:
            fcs ^= b
            for _ in range(8):
                if fcs & 0x0001:
                    fcs = (fcs >> 1) ^ 0x8408
                else:
                    fcs = fcs >> 1
        checksums["hdlc_fcs"] = (~fcs) & 0xFF  # Take only lower byte

        return checksums

    def decode(self) -> Optional[Tuple[DLMSFrame, Dict[str, int]]]:
        try:
            original_bytes = self.raw_bytes[:]
            
            # Parse frame
            start = self.read_byte()
            if start != 0x7E:
                raise ValueError(f"Invalid start character: {hex(start)}")
            
            format_byte = self.read_byte()
            control = self.read_byte()
            address = self.read_byte()
            ci_field = self.read_byte()
            
            # Read common header data
            header_data = bytearray()
            #header_data = self.read_bytes(11)
            
            # Calculate remaining payload length
            remaining_bytes = len(self.raw_bytes) - self.position - 2
            encrypted_payload = self.read_bytes(remaining_bytes)
            
            # Try to decrypt payload
            security_control = bytes([ci_field])  # Use CI field as security control
            decrypted_payload = self.decrypt_payload(encrypted_payload, security_control)
            
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
                payload=encrypted_payload,
                decrypted_payload=decrypted_payload,
                checksum=checksum,
                stop=stop
            )
            
            # Calculate checksums with both encrypted and decrypted payload
            checksums = self.calculate_checksums(original_bytes, decrypted_payload)
            
            return frame, checksums
            
        except Exception as e:
            print(f"Error decoding frame: {str(e)}")
            return None

def print_frame_analysis(frames: List[str], encryption_key: str, auth_key: str):
    """Analyze multiple frames with decryption"""
    print("\nDLMS Frame Analysis with Decryption:")
    print("==================================")
    
    for i, frame_hex in enumerate(frames, 1):
        print(f"\nFrame {i}:")
        decoder = LandisGyrDLMSDecoder(frame_hex, encryption_key, auth_key)
        result = decoder.decode()
        
        if result:
            frame, checksums = result
            print(f"Format Byte: 0x{frame.format_byte:02X}")
            print(f"Control: 0x{frame.control:02X}")
            print(f"Address: 0x{frame.address:02X}")
            print(f"CI Field: 0x{frame.ci_field:02X}")
            print(f"Common Header: {frame.header_data.hex()}")
            print(f"\nEncrypted Payload ({len(frame.payload)} bytes):")
            print(frame.payload.hex())
            if frame.decrypted_payload:
                print(f"\nDecrypted Payload ({len(frame.decrypted_payload)} bytes):")
                print(frame.decrypted_payload.hex())
            print(f"\nReceived Checksum: 0x{frame.checksum:02X}")
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

encryption_key = "4475D2230289243A4AE7732E2396C572"
auth_key = "8FEADE1D7057D94D816A41E09D17CB58"

print_frame_analysis(frames, encryption_key, auth_key)