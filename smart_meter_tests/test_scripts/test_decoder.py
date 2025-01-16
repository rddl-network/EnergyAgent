from dataclasses import dataclass
from typing import List, Tuple
import struct

@dataclass
class MBusField:
    """Represents a decoded M-Bus field"""
    dif: int
    vif: int
    value: any
    unit: str

class MBusDecoder:
    def __init__(self, payload: bytes):
        self.payload = payload
        self.position = 0
        self.fields = []

    def decode_dif(self) -> Tuple[int, int]:
        """Decode Data Information Field"""
        dif = self.payload[self.position]
        data_len = dif & 0x0F
        self.position += 1
        return dif, data_len

    def decode_vif(self) -> Tuple[int, str]:
        """Decode Value Information Field"""
        vif = self.payload[self.position]
        self.position += 1

        # Basic VIF decoding - extend based on your specific needs
        units = {
            0x00: "No unit",
            0x01: "Wh",
            0x02: "kWh",
            0x03: "MWh",
            0x04: "kJ",
            0x05: "MJ",
            0x06: "GJ",
            0x07: "W",
            0x08: "kW",
            0x09: "MW",
            0x0A: "kJ/h",
            0x0B: "MJ/h",
            0x0C: "GJ/h",
            0x0D: "ml",
            0x0E: "l",
            0x0F: "m³"
        }

        unit = units.get(vif & 0x0F, "Unknown")
        return vif, unit

    def decode_value(self, data_len: int) -> any:
        """Decode the actual value based on length"""
        value = None
        data = self.payload[self.position:self.position + data_len]

        if data_len == 1:
            value = struct.unpack('B', data)[0]
        elif data_len == 2:
            value = struct.unpack('<H', data)[0]
        elif data_len == 4:
            value = struct.unpack('<I', data)[0]
        elif data_len == 8:
            value = struct.unpack('<Q', data)[0]

        self.position += data_len
        return value

    def decode(self) -> List[MBusField]:
        """Main decode function"""
        try:
            while self.position < len(self.payload):
                dif, data_len = self.decode_dif()
                vif, unit = self.decode_vif()
                value = self.decode_value(data_len)

                field = MBusField(dif=dif, vif=vif, value=value, unit=unit)
                self.fields.append(field)

        except IndexError:
            print("Reached end of payload")
        except Exception as e:
            print(f"Error decoding at position {self.position}: {str(e)}")

        return self.fields

# Usage example
def decode_mbus_payload(payload: bytes) -> None:
    decoder = MBusDecoder(payload)
    decoded_fields = decoder.decode()

    print("\nDecoded M-Bus Fields:")
    print("--------------------")
    for i, field in enumerate(decoded_fields, 1):
        print(f"Field {i}:")
        print(f"  DIF: 0x{field.dif:02X}")
        print(f"  VIF: 0x{field.vif:02X}")
        print(f"  Value: {field.value}")
        print(f"  Unit: {field.unit}")
        print()

# Your payload
payload = b'\xc8dG\x15\x82\xdbV\xcf\x89\x95\x8c\xc6\x9a\x0f\xd6C\x80}D\x95\x89"!z\x9d\xbf\x958S\xe1\xea\x8a\xa5%\xe7Di\x18\x1b/wg\xb4\x96\x9braB\xb7\x9b@\xd6\xb8\xc5("\x87k\tf\x9fN4\'\x06X\xf9\x92P\xa6`{\xde-r'

# Decode the payload
decode_mbus_payload(payload)
