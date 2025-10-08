from dataclasses import dataclass

@dataclass
class HDLCFrame:
    """Represents a parsed HDLC frame"""
    index: int
    sequence_byte: int
    sequence_number: int
    payload: bytes
    payload_length: int