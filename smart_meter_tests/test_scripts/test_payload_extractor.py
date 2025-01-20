class MBusFrame:
    def __init__(self, hex_string):
        # Remove any whitespace and ensure lowercase
        self.raw_frame = hex_string.strip().lower()
        # Validate start and end flags
        if not (self.raw_frame.startswith("7e") and self.raw_frame.endswith("7e")):
            raise ValueError("Invalid M-Bus frame: Missing start/end flags")

        # Remove start and end flags
        self.frame_data = self.raw_frame[2:-2]

    def extract_fields(self):
        """Extract all fields from the M-Bus frame."""
        current_pos = 0

        # Length field (2 bytes)
        self.length = self.frame_data[current_pos : current_pos + 4]
        current_pos += 4

        # Control field (1 byte)
        self.control = self.frame_data[current_pos : current_pos + 2]
        current_pos += 2

        # Address field (variable length)
        self.address = self.frame_data[current_pos : current_pos + 8]  # Updated length
        current_pos += 8

        # Control Information field (3 bytes)
        self.control_info = self.frame_data[current_pos : current_pos + 6]
        current_pos += 6

        # Find the start of the actual payload (looking for 'db')
        remaining = self.frame_data[current_pos:]
        db_pos = remaining.find("db")

        if db_pos != -1:
            self.additional_addr = remaining[:db_pos]
            self.payload = remaining[db_pos:]
        else:
            self.additional_addr = ""
            self.payload = remaining

        return {
            "length": self.length,
            "control": self.control,
            "address": self.address,
            "control_info": self.control_info,
            "additional_address": self.additional_addr,
            "payload": self.payload,
        }

    def get_payload(self):
        """Return just the payload portion."""
        fields = self.extract_fields()
        return fields["payload"]


def parse_mbus_frame(hex_string):
    """Parse an M-Bus frame and print all fields."""
    try:
        frame = MBusFrame(hex_string)
        fields = frame.extract_fields()

        print("M-Bus Frame Analysis:")
        print("-" * 50)
        print(f"Start Flag: 7e")
        print(f"Length Field: {fields['length']}")
        print(f"Control Field: {fields['control']}")
        print(f"Address Field: {fields['address']}")
        print(f"Control Info: {fields['control_info']}")
        print(f"Additional Address: {fields['additional_address']}")
        print(f"Payload (starts with db): {fields['payload']}")
        print(f"End Flag: 7e")

        return fields["payload"]

    except ValueError as e:
        print(f"Error: {e}")
        return None


# Example usage
if __name__ == "__main__":
    # Your example frames
    frame1 = "7ea08bceff0313eee1e6e700e0400001000077db084c475a67737c7e8e820103300009833108abce90b04deb2c46f68ae7d8e04f42404131bb25d50be0de4b6c81c6bcb7f094c2f9cf41f85dae692eefd67d74a1c12045fc673e72143da1ea280d7b38751e33a38af80d5b641c2b9025dfa64d2ad115064af080086a141563f5056caf7b3a99595f904ef3527e"
    frame2 = "7ea067ceff031338bde6e700db084c475a6773745ddd4f2000e8c3f44d3b65fcf023f403e19036a1c9f5e6eabdf04c40a4800b1509a2252881267d0b90e585eef07f57c90ad75192893725ae5f06bacee5a422d33f1705a1919765812e06910abfdb2beb901270657e"

    print("\nAnalyzing Frame 1:")
    payload1 = parse_mbus_frame(frame1)

    print("\nAnalyzing Frame 2:")
    payload2 = parse_mbus_frame(frame2)
