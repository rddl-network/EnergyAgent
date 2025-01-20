class DLMSFrame:
    # DLMS types for multi-segment messages
    DLMS_TYPES = {b"\xe0\x40": "Block Transfer", b"\xe0\xc0": "Final Block"}

    # Control field interpretations
    CONTROL_FIELDS = {b"\xee\xe1": "Request/Response", b"\x84\x63": "Final Block Response"}

    @staticmethod
    def _calculate_crc16(data: bytearray) -> int:
        fcs = 0xFFFF
        for byte in data:
            fcs ^= byte << 8
            for _ in range(8):
                if fcs & 0x8000:
                    fcs = (fcs << 1) ^ 0x1021
                else:
                    fcs = fcs << 1
                fcs &= 0xFFFF

        return fcs ^ 0xFFFF  # Fina

    def verify_checksum(self) -> bool:
        """
        Verify frame checksum
        Returns:
            bool: True if checksum is valid, False otherwise
        """
        # Get all data between start flag and checksum
        data_to_check = self.frame_bytes[1:-3]  # Exclude start flag, checksum and end flag

        # Calculate CRC
        calculated_crc = self._calculate_crc16(self.payload)

        # Get received checksum (need to swap bytes for correct comparison)
        # received_crc = (self.checksum[1] << 8) | self.checksum[0]
        received_crc = int.from_bytes(self.checksum, byteorder="big")
        # Debug print
        print(f"Data length: {len(self.payload)}")
        print(f"Calculated CRC: {calculated_crc:04X}")
        print(f"Received CRC: {received_crc:04X}")
        print(f"Raw checksum bytes: {self.checksum.hex()}")

        return calculated_crc == received_crc

    def get_checksum_info(self) -> dict:
        """
        Get detailed checksum information
        Returns:
            dict: Dictionary with checksum details
        """
        data_to_check = self.frame_bytes[1:-3]
        calculated_crc = self._calculate_crc16(data_to_check)
        received_crc = int.from_bytes(self.checksum, byteorder="big")

        return {
            "received_checksum": f"{received_crc:04X}",
            "calculated_checksum": f"{calculated_crc:04X}",
            "is_valid": calculated_crc == received_crc,
        }

    def __init__(self, frame_data: bytearray):
        """
        Initialize DLMS frame parser with bytearray
        Args:
            frame_data (bytearray): Frame data as bytearray
        """
        self.frame_bytes = frame_data
        self._parse_frame()

    @classmethod
    def from_hex_string(cls, hex_string: str):
        """
        Alternative constructor to create frame from hex string
        Args:
            hex_string (str): Hex string of the frame
        Returns:
            DLMSFrame: New frame instance
        """
        clean_hex = hex_string.replace(" ", "").upper()
        frame_data = bytearray.fromhex(clean_hex)
        return cls(frame_data)

    def _parse_frame(self):
        """Parse the frame into its components"""
        if self.frame_bytes[0] != 0x7E or self.frame_bytes[-1] != 0x7E:
            raise ValueError("Invalid frame: Missing start/end flags")

        # Basic frame components always present
        self.start_flag = self.frame_bytes[0]
        self.format_type = self.frame_bytes[1]
        self.length = self.frame_bytes[2]
        self.source_addr = self.frame_bytes[3:5]
        self.dest_addr = self.frame_bytes[5:7]
        self.control_field = self.frame_bytes[7:9]
        self.control_field_meaning = self.CONTROL_FIELDS.get(self.control_field.hex(), "Unknown")

        # Start checking from control field position
        current_pos = 9

        # Try to detect frame type by looking ahead
        next_bytes = self.frame_bytes[current_pos : current_pos + 3]

        # Check for service type E6E700
        if next_bytes.startswith(b"\xe6\xe7\x00"):
            self.service_type = next_bytes
            self.service_type_name = self._get_service_type_name()
            current_pos += 3

            # Look at what follows E6E700
            next_dlms = self.frame_bytes[current_pos : current_pos + 2]

            if next_dlms == b"\xdb\x08":  # Single message with OBIS
                self.is_first_segment = False
                self.is_multi_segment = False
                self.is_final_segment = False
                # Don't parse OBIS code, leave it in payload

            elif next_dlms == b"\xe0\x40":  # First message of multi-segment
                self.is_first_segment = True
                self.is_multi_segment = True
                self.is_final_segment = False
                self.dlms_type = next_dlms
                self.dlms_type_name = self.DLMS_TYPES.get(self.dlms_type.hex(), "Unknown")
                current_pos += 2
                # Process sequence info for multi-segment
                self.sequence_number = int.from_bytes(self.frame_bytes[current_pos : current_pos + 2], byteorder="big")
                current_pos += 2
                # Skip two bytes (0x00 0x00)
                current_pos += 2
                self.segment_control = self.frame_bytes[current_pos]
                current_pos += 1

        elif self.frame_bytes[current_pos : current_pos + 2] in [
            b"\xe0\x40",
            b"\xe0\xc0",
        ]:  # Subsequent or final segment
            self.is_first_segment = False
            self.is_multi_segment = True
            self.service_type = None
            self.service_type_name = None
            self.dlms_type = self.frame_bytes[current_pos : current_pos + 2]
            self.dlms_type_name = self.DLMS_TYPES.get(self.dlms_type.hex(), "Unknown")
            self.is_final_segment = self.dlms_type == b"\xe0\xc0"
            current_pos += 2
            # Process sequence info for multi-segment
            self.sequence_number = int.from_bytes(self.frame_bytes[current_pos : current_pos + 2], byteorder="big")
            current_pos += 2
            # Skip two bytes (0x00 0x00)
            current_pos += 2
            self.segment_control = self.frame_bytes[current_pos]
            current_pos += 1

        else:
            # Unknown frame type
            self.is_first_segment = False
            self.is_multi_segment = False
            self.is_final_segment = False
            self.service_type = None
            self.service_type_name = None

        # Extract payload and checksum
        self.payload = self.frame_bytes[current_pos:-3]
        self.checksum = self.frame_bytes[-3:-1]
        self.end_flag = self.frame_bytes[-1]

    def _get_service_type_name(self) -> str:
        """Get the service type name based on the service type bytes"""
        if not self.service_type:
            return None

        service_type_prefix = self.service_type[0]
        service_type_suffix = self.service_type[1]
        full_type = f"{service_type_prefix:02X}{service_type_suffix:02X}"

        service_types = {
            "E6E7": "General-Block-Transfer with Access-Request",
            "E6E8": "General-Block-Transfer with Access-Response",
        }

        return service_types.get(full_type, f"Unknown ({full_type})")

    def get_addresses(self) -> tuple:
        """Return source and destination addresses as hex strings"""
        return (self.source_addr.hex(), self.dest_addr.hex())

    def get_payload(self) -> bytearray:
        """Return the payload as bytearray"""
        return self.payload

    def get_payload_hex(self) -> str:
        """Return the payload as hex string"""
        return self.payload.hex()

    def get_payload_length(self) -> int:
        """Return the length of the payload"""
        return len(self.payload)

    def get_frame_details(self) -> dict:
        """Get detailed information about the frame"""
        details = {
            "length": self.length,
            "source": self.source_addr.hex(),
            "destination": self.dest_addr.hex(),
            "control_field": f"{self.control_field.hex()} ({self.control_field_meaning})",
            "is_multi_segment": self.is_multi_segment,
            "is_first_segment": self.is_first_segment,
            "is_final_segment": self.is_final_segment if self.is_multi_segment else False,
            "payload_length": len(self.payload),
            "checksum": self.get_checksum_info(),
        }

        if self.service_type:
            details["service_type"] = self.service_type_name

        if self.is_multi_segment:
            details.update(
                {
                    "sequence_number": self.sequence_number,
                    "dlms_type": f"{self.dlms_type.hex()} ({self.dlms_type_name})",
                    "segment_control": f"{self.segment_control:02X}",
                }
            )

        return details

    def __str__(self) -> str:
        """String representation of the frame"""
        base_info = (
            f"DLMS Frame:\n"
            f"  Length: {self.length}\n"
            f"  Source: {self.source_addr.hex()}\n"
            f"  Destination: {self.dest_addr.hex()}\n"
            f"  Control Field: {self.control_field.hex()} ({self.control_field_meaning})\n"
            f"  Is Multi-Segment: {self.is_multi_segment}\n"
            f"  Payload Length: {len(self.payload)}\n"
        )

        if self.service_type:
            base_info += f"  Service Type: {self.service_type_name}\n"

        if self.is_multi_segment:
            base_info += (
                f"  Is First Segment: {self.is_first_segment}\n"
                f"  Is Final Segment: {self.is_final_segment}\n"
                f"  DLMS Type: {self.dlms_type.hex()} ({self.dlms_type_name})\n"
                f"  Sequence Number: {self.sequence_number}\n"
                f"  Segment Control: {self.segment_control:02X}\n"
            )

        return base_info


# Example usage:
if __name__ == "__main__":
    # Example multi-segment sequence
    frame1 = "7ea08bceff0313eee1e6e700e0400001000077db084c475a677362f13a8201c53000b1cdb52ec1eb626fde9e6d337047190e0cb1ca7f6d681d0dbede752c685dadf86382cf4ea66bb1890e11fdb1eb87090db5fc451603362da0ce529e57cb0be9e3af314e61ef3c3ea7ec236dcc3846bacd3256c98a220165fcc30696c7a8a3b44114b87c816b760d420ae57e"
    frame2 = "7ea08bceff0313eee1e040000200007a474c319e92d674b21117089bb4c52b7cc551eaf3052a2892fcdd95c48bedf90d5d521cfe4b3cc4f3b974c865d9116d5208e19831d869db3a1d6609e4a54c43c9b9504495a43e21f5b344c462d5e79e9f1416484f359a0cc56ac0a1bae8445144bee3a7aa7e8320b36a2703374a6441cb307430c13d0ae891b80307197e"
    frame3 = "7ea078ceff03138463e0c00004000067a0c6fc1db0926f2ec72fc115bb4f8ff217c356a2752c1c0ef4195e1c5312ab0d23e2535cffc6bd4a0c9f002c753b05ac313888a81021e52c248cebf3c566639b6e82755d6abd1da2b4ca707812cdb9c44e4688c957c9d9c488705d0e098b41d6096d259ebde315dd0d7e"

    print("First message (with service type):")
    f1 = DLMSFrame.from_hex_string(frame1)
    print(f1)
    print("\nSecond message (intermediate):")
    f2 = DLMSFrame.from_hex_string(frame2)
    print(f2)
    print("\nThird message (final segment):")
    f3 = DLMSFrame.from_hex_string(frame3)
    print(f3)
