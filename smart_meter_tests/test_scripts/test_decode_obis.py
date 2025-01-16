from dataclasses import dataclass
from typing import List, Any, Optional
from binascii import unhexlify, hexlify

@dataclass
class OBISCode:
    raw_code: bytes
    value: Any
    value_type: int

    @property
    def code_string(self) -> str:
        return '.'.join(str(b) for b in self.raw_code)

    def get_description(self) -> str:
        descriptions = {
            "0.0.1.0.0.255": "Clock object",
            "0.0.96.1.0.255": "Device ID",
            "0.8.19.9.0.255": "Status of billing period",
            # Add more as needed
        }
        return descriptions.get(self.code_string, "Unknown OBIS code")

class DLMSDecoder:
    def __init__(self, data: bytes):
        self.data = data
        self.position = 0

    def read_bytes(self, length: int) -> bytes:
        """Read specified number of bytes and advance position"""
        data = self.data[self.position:self.position + length]
        self.position += length
        return data

    def read_byte(self) -> int:
        """Read a single byte and advance position"""
        value = self.data[self.position]
        self.position += 1
        return value

    def find_obis_structures(self) -> List[OBISCode]:
        obis_codes = []
        
        while self.position < len(self.data):
            try:
                # Look for structure marker (0x02) followed by length (0x04)
                if self.read_bytes(2) == b'\x02\x04':
                    # Read length of the structure
                    length = self.read_byte()
                    
                    # Check for OBIS code identifier (0x09 0x06)
                    if self.read_bytes(2) == b'\x09\x06':
                        # Read OBIS code (6 bytes)
                        obis_code = self.read_bytes(6)
                        
                        # Read value type and value
                        value_type = self.read_byte()
                        value_length = self.read_byte()
                        value = self.read_bytes(value_length)
                        
                        obis_codes.append(OBISCode(
                            raw_code=obis_code,
                            value=value,
                            value_type=value_type
                        ))
                    else:
                        self.position -= 1  # Step back one byte for next iteration
                else:
                    self.position -= 1  # Step back one byte for next iteration
                    
            except IndexError:
                break
                
        return obis_codes

def decode_dlms_message(hex_string: str) -> None:
    # Convert hex string to bytes
    data = unhexlify(hex_string)
    
    # Create decoder instance
    decoder = DLMSDecoder(data)
    
    # Find and decode OBIS structures
    obis_codes = decoder.find_obis_structures()
    
    # Print results
    print(f"Found {len(obis_codes)} OBIS codes:")
    for idx, code in enumerate(obis_codes, 1):
        print(f"\n{idx}. OBIS Code: {code.code_string}")
        print(f"   Description: {code.get_description()}")
        print(f"   Value type: 0x{code.value_type:02x}")
        print(f"   Raw value: {hexlify(code.value).decode()}")

def main():
    # Your payload
    payload = "0f00b1ce270c07e70a0c040e0528ff80000002120112020412002809060008190900ff0f02120000020412002809060008190900ff0f01120000020412000109060000600100ff0f02120000020412000809060000010000ff0f02120000020412000309064c0b7ca80cbbadc4b1"
    
    print("Decoding DLMS message...\n")
    decode_dlms_message(payload)

if __name__ == "__main__":
    main()