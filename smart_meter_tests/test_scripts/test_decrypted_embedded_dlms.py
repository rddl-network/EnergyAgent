from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from binascii import unhexlify, hexlify
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class DLMSHeader:
    tag: int
    length: int
    value: bytes

@dataclass
class SecurityHeader:
    system_title: bytes
    frame_counter: bytes
    encrypted_payload: bytes
    auth_tag: bytes

class DLMSParser:
    def __init__(self, encryption_key: str, auth_key: str):
        self.encryption_key = unhexlify(encryption_key)
        self.auth_key = unhexlify(auth_key)

    def parse_tlv(self, data: bytes, offset: int = 0) -> Tuple[DLMSHeader, int]:
        """Parse TLV (Tag-Length-Value) structure from bytes."""
        tag = data[offset]
        length = data[offset + 1]
        value = data[offset + 2:offset + 2 + length]
        return DLMSHeader(tag, length, value), offset + 2 + length

    def parse_obis_codes(self, data: bytes) -> List[str]:
        """Extract OBIS codes from the payload."""
        obis_codes = []
        offset = 0
        
        while offset < len(data):
            if data[offset:offset+2] == b'\x02\x04':  # Structure marker
                length = data[offset+2]
                if length >= 6:  # Minimum OBIS code length
                    # Check for OBIS code pattern (09 06 followed by 6 bytes)
                    if data[offset+4:offset+6] == b'\x09\x06':
                        obis_code = data[offset+6:offset+12]
                        obis_codes.append('.'.join(str(b) for b in obis_code))
                offset += 4 + length
            else:
                offset += 1
                
        return obis_codes

    def parse_security_header(self, data: bytes) -> SecurityHeader:
        """Parse the security header structure."""
        # Find the start of security wrapper
        security_start = data.find(b'\x02\x04\x12\x00\x03\x09\x06')
        if security_start == -1:
            raise ValueError("Security wrapper not found")
        
        # Skip the header bytes
        data = data[security_start + 7:]
        
        # Extract components
        system_title = data[:8]
        frame_counter = data[8:12]
        
        # The rest is encrypted payload + auth tag
        encrypted_data = data[12:]
        
        # Last 12 bytes are typically the auth tag
        auth_tag = encrypted_data[-12:]
        encrypted_payload = encrypted_data[:-12]
        
        return SecurityHeader(
            system_title=system_title,
            frame_counter=frame_counter,
            encrypted_payload=encrypted_payload,
            auth_tag=auth_tag
        )

    def decrypt_payload(self, security_header: SecurityHeader) -> bytes:
        """Decrypt the payload using AES-GCM."""
        try:
            # Construct IV from system title and frame counter
            iv = security_header.system_title + security_header.frame_counter
            
            # Create AESGCM cipher
            aesgcm = AESGCM(self.encryption_key)
            
            # Combine encrypted payload and auth tag
            ciphertext = security_header.encrypted_payload + security_header.auth_tag
            
            # Decrypt
            decrypted = aesgcm.decrypt(iv, ciphertext, associated_data=None)
            return decrypted
            
        except Exception as e:
            print(f"Decryption error: {e}")
            return b''

def main():
    # Your encrypted payload
    encrypted_payload = "0f00b1ce270c07e70a0c040e0528ff80000002120112020412002809060008190900ff0f02120000020412002809060008190900ff0f01120000020412000109060000600100ff0f02120000020412000809060000010000ff0f02120000020412000309064c0b7ca80cbbadc4b1061f912b63ee54b092ba19f428024561235a514f6410e6500c47e4b477f93f4a32b3afaec87c3d5efb79aae0b7b3e125736f124eeb1d8a70eb10c3319916d247f783a1b7cd760399025e057ebd96caa6ac601b56ab15eaf55f560dd4ffa781d94e2d327c2e2682fbbb4bf3ee37e27b2da96be3038f6c1e4e601ca21e7762dfe8bfd845f3578faf98f1f5e669001d9ac77f329465146c55c842e0f06ed0c28614f55141d4f431991ea27622544865e9aaf28424ad506dd6757a538dc655b51d8b922f49b7303f5cc235bf01c06125f29921877a145975e25adf43823afc4daeba6db17518ed8a6d3aca1e07d85c5fbd7e777b9eaa49e7e7a2b6ab7c617f94bcba7d5971d4015eed62b3375eb04f5e7f1d95e7b5ca224a26ea3beb540c3d249928af4d3c0569c1d7498d905808e1fc6aeec8402b92c5d2cccabdc1c483ff5e87fb53109353a9995ea94eef"
    
    # Test keys (all zeros)
    encryption_key = "00000000000000000000000000000000"
    auth_key = "00000000000000000000000000000000"
    
    # Create parser instance
    parser = DLMSParser(encryption_key, auth_key)
    
    # Convert hex string to bytes
    data = unhexlify(encrypted_payload)
    
    # Parse OBIS codes from the unencrypted part
    obis_codes = parser.parse_obis_codes(data)
    print("Found OBIS codes:", obis_codes)
    
    # Parse security header
    security_header = parser.parse_security_header(data)
    print("\nSecurity Header:")
    print(f"System Title: {hexlify(security_header.system_title).decode()}")
    print(f"Frame Counter: {hexlify(security_header.frame_counter).decode()}")
    
    # Attempt decryption
    decrypted = parser.decrypt_payload(security_header)
    if decrypted:
        print("\nDecrypted payload (hex):")
        print(hexlify(decrypted).decode())
        
        # Try to parse OBIS codes from decrypted data
        decrypted_obis = parser.parse_obis_codes(decrypted)
        if decrypted_obis:
            print("\nOBIS codes in decrypted data:", decrypted_obis)

if __name__ == "__main__":
    main()