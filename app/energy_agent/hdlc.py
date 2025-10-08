import logging
from typing import List, Optional
from app.model.hdlc_frame import HDLCFrame

import struct

def parse_hdlc_frames( frameset_hex: str) -> List[HDLCFrame]:
    """
    Parse HDLC frames from hex string and extract payloads
    
    Args:
        frameset_hex: Complete frameset as hex string
        
    Returns:
        List of parsed HDLC frames
    """
    logger.info("Starting HDLC frame parsing...")
    
    frameset_bytes = bytes.fromhex(frameset_hex)
    frames = []
    
    # Find all header positions
    positions = []
    pos = 0
    while True:
        pos = frameset_bytes.find(self.hdlc_header_pattern, pos)
        if pos == -1:
            break
        positions.append(pos)
        pos += len(self.hdlc_header_pattern)
    
    logger.info(f"Found {len(positions)} HDLC frames")
    
    # Extract payload from each frame
    for i, frame_start in enumerate(positions):
        frame_end = positions[i + 1] if i + 1 < len(positions) else len(frameset_bytes)
        
        # Calculate payload boundaries
        payload_start = frame_start + len(self.hdlc_header_pattern) + 1  # +1 for sequence byte
        payload_end = frame_end
        
        # Remove trailing 0x7E delimiter if present
        frame_data = frameset_bytes[frame_start:frame_end]
        if frame_data.endswith(b'\x7e'):
            payload_end = frame_end - 1
        
        # Extract sequence byte and payload
        sequence_byte = frameset_bytes[frame_start + len(self.hdlc_header_pattern)]
        payload = frameset_bytes[payload_start:payload_end]
        
        # Determine sequence number (0xB8 = 1, 0x38 = 0)
        sequence_number = 1 if sequence_byte == 0xB8 else 0
        
        frame = HDLCFrame(
            index=i + 1,
            sequence_byte=sequence_byte,
            sequence_number=sequence_number,
            payload=payload,
            payload_length=len(payload)
        )
        
        frames.append(frame)
        
        logger.debug(f"Frame {i+1}: Seq=0x{sequence_byte:02x} ({sequence_number}), "
                    f"Payload={len(payload)} bytes")
    
    self.frames = frames
    logger.info(f"Successfully parsed {len(frames)} frames")
    return frames


class HDLCParser:
    """
    HDLC Frame Parser for parsing HDLC frames from raw payload data.
    
    HDLC Frame Structure:
    - Flag (0x7E): Start/End delimiter
    - Address: Usually 1 byte (can be extended)
    - Control: 1 byte (frame type and sequence numbers)
    - Information: Variable length payload
    - FCS: 2 bytes (Frame Check Sequence - CRC16)
    - Flag (0x7E): End delimiter
    """
    
    HDLC_FLAG = 0x7E
    HDLC_ESCAPE = 0x7D
    HDLC_ESCAPE_XOR = 0x20
    
    # CRC16-CCITT polynomial (0x1021)
    CRC16_CCITT_TABLE = [
        0x0000, 0x1021, 0x2042, 0x3063, 0x4084, 0x50A5, 0x60C6, 0x70E7,
        0x8108, 0x9129, 0xA14A, 0xB16B, 0xC18C, 0xD1AD, 0xE1CE, 0xF1EF,
        0x1231, 0x0210, 0x3273, 0x2252, 0x52B5, 0x4294, 0x72F7, 0x62D6,
        0x9339, 0x8318, 0xB37B, 0xA35A, 0xD3BD, 0xC39C, 0xF3FF, 0xE3DE,
        0x2462, 0x3443, 0x0420, 0x1401, 0x64E6, 0x74C7, 0x44A4, 0x5485,
        0xA56A, 0xB54B, 0x8528, 0x9509, 0xE5EE, 0xF5CF, 0xC5AC, 0xD58D,
        0x3653, 0x2672, 0x1611, 0x0630, 0x76D7, 0x66F6, 0x5695, 0x46B4,
        0xB75B, 0xA77A, 0x9719, 0x8738, 0xF7DF, 0xE7FE, 0xD79D, 0xC7BC,
        0x48C4, 0x58E5, 0x6886, 0x78A7, 0x0840, 0x1861, 0x2802, 0x3823,
        0xC9CC, 0xD9ED, 0xE98E, 0xF9AF, 0x8948, 0x9969, 0xA90A, 0xB92B,
        0x5AF5, 0x4AD4, 0x7AB7, 0x6A96, 0x1A71, 0x0A50, 0x3A33, 0x2A12,
        0xDBFD, 0xCBDC, 0xFBBF, 0xEB9E, 0x9B79, 0x8B58, 0xBB3B, 0xAB1A,
        0x6CA6, 0x7C87, 0x4CE4, 0x5CC5, 0x2C22, 0x3C03, 0x0C60, 0x1C41,
        0xEDAE, 0xFD8F, 0xCDEC, 0xDDCD, 0xAD2A, 0xBD0B, 0x8D68, 0x9D49,
        0x7E97, 0x6EB6, 0x5ED5, 0x4EF4, 0x3E13, 0x2E32, 0x1E51, 0x0E70,
        0xFF9F, 0xEFBE, 0xDFDD, 0xCFFC, 0xBF1B, 0xAF3A, 0x9F59, 0x8F78,
        0x9188, 0x81A9, 0xB1CA, 0xA1EB, 0xD10C, 0xC12D, 0xF14E, 0xE16F,
        0x1080, 0x00A1, 0x30C2, 0x20E3, 0x5004, 0x4025, 0x7046, 0x6067,
        0x83B9, 0x9398, 0xA3FB, 0xB3DA, 0xC33D, 0xD31C, 0xE37F, 0xF35E,
        0x02B1, 0x1290, 0x22F3, 0x32D2, 0x4235, 0x5214, 0x6277, 0x7256,
        0xB5EA, 0xA5CB, 0x95A8, 0x8589, 0xF56E, 0xE54F, 0xD52C, 0xC50D,
        0x34E2, 0x24C3, 0x14A0, 0x0481, 0x7466, 0x6447, 0x5424, 0x4405,
        0xA7DB, 0xB7FA, 0x8799, 0x97B8, 0xE75F, 0xF77E, 0xC71D, 0xD73C,
        0x26D3, 0x36F2, 0x0691, 0x16B0, 0x6657, 0x7676, 0x4615, 0x5634,
        0xD94C, 0xC96D, 0xF90E, 0xE92F, 0x99C8, 0x89E9, 0xB98A, 0xA9AB,
        0x5844, 0x4865, 0x7806, 0x6827, 0x18C0, 0x08E1, 0x3882, 0x28A3,
        0xCB7D, 0xDB5C, 0xEB3F, 0xFB1E, 0x8BF9, 0x9BD8, 0xABBB, 0xBB9A,
        0x4A75, 0x5A54, 0x6A37, 0x7A16, 0x0AF1, 0x1AD0, 0x2AB3, 0x3A92,
        0xFD2E, 0xED0F, 0xDD6C, 0xCD4D, 0xBDAA, 0xAD8B, 0x9DE8, 0x8DC9,
        0x7C26, 0x6C07, 0x5C64, 0x4C45, 0x3CA2, 0x2C83, 0x1CE0, 0x0CC1,
        0xEF1F, 0xFF3E, 0xCF5D, 0xDF7C, 0xAF9B, 0xBFBA, 0x8FD9, 0x9FF8,
        0x6E17, 0x7E36, 0x4E55, 0x5E74, 0x2E93, 0x3EB2, 0x0ED1, 0x1EF0
    ]
    
    def __init__(self):
        self.frames = []
        self.errors = []
    
    def crc16_ccitt(self, data: bytes) -> int:
        """Calculate CRC16-CCITT checksum for given data."""
        crc = 0xFFFF
        for byte in data:
            tbl_idx = ((crc >> 8) ^ byte) & 0xFF
            crc = ((crc << 8) ^ self.CRC16_CCITT_TABLE[tbl_idx]) & 0xFFFF
        return crc ^ 0xFFFF
    
    def unstuff_data(self, data: bytes) -> bytes:
        """Remove byte stuffing from HDLC frame data."""
        unstuffed = bytearray()
        i = 0
        while i < len(data):
            if data[i] == self.HDLC_ESCAPE and i + 1 < len(data):
                # Escape sequence found, XOR next byte with 0x20
                unstuffed.append(data[i + 1] ^ self.HDLC_ESCAPE_XOR)
                i += 2
            else:
                unstuffed.append(data[i])
                i += 1
        return bytes(unstuffed)
    
    def parse_control_field(self, control: int) -> dict:
        """Parse HDLC control field to determine frame type."""
        if (control & 0x01) == 0:
            # I-frame (Information)
            return {
                'type': 'I-frame',
                'ns': (control >> 1) & 0x07,  # Send sequence number
                'pf': (control >> 4) & 0x01,  # Poll/Final bit
                'nr': (control >> 5) & 0x07   # Receive sequence number
            }
        elif (control & 0x03) == 0x01:
            # S-frame (Supervisory)
            s_type = (control >> 2) & 0x03
            s_types = {0: 'RR', 1: 'RNR', 2: 'REJ', 3: 'SREJ'}
            return {
                'type': 'S-frame',
                'subtype': s_types.get(s_type, 'Unknown'),
                'pf': (control >> 4) & 0x01,
                'nr': (control >> 5) & 0x07
            }
        else:
            # U-frame (Unnumbered)
            return {
                'type': 'U-frame',
                'pf': (control >> 4) & 0x01,
                'modifier': control & 0xEF  # All bits except P/F
            }
    
    def parse_frame(self, frame_data: bytes) -> Optional[dict]:
        """Parse a single HDLC frame."""
        if len(frame_data) < 4:  # Minimum: Address + Control + 2-byte FCS
            self.errors.append(f"Frame too short: {len(frame_data)} bytes")
            return None
        
        # Extract components
        address = frame_data[0]
        control = frame_data[1]
        
        # Information field and FCS
        if len(frame_data) > 4:
            information = frame_data[2:-2]
            fcs_received = struct.unpack('<H', frame_data[-2:])[0]  # Little-endian 16-bit
        else:
            information = b''
            fcs_received = struct.unpack('<H', frame_data[-2:])[0]
        
        # Calculate FCS for verification
        fcs_data = frame_data[:-2]  # All data except FCS
        fcs_calculated = self.crc16_ccitt(fcs_data)
        
        # Parse control field
        control_info = self.parse_control_field(control)
        
        frame_info = {
            'address': f"0x{address:02X}",
            'control': f"0x{control:02X}",
            'control_info': control_info,
            'information': information.hex() if information else '',
            'information_length': len(information),
            'fcs_received': f"0x{fcs_received:04X}",
            'fcs_calculated': f"0x{fcs_calculated:04X}",
            'fcs_valid': fcs_received == fcs_calculated,
            'frame_length': len(frame_data)
        }
        
        if not frame_info['fcs_valid']:
            self.errors.append(f"CRC mismatch in frame: received {frame_info['fcs_received']}, calculated {frame_info['fcs_calculated']}")
        
        return frame_info
    
    def parse_payload(self, hex_payload: str) -> List[dict]:
        """Parse HDLC frames from hex payload string."""
        # Clean and convert hex string to bytes
        hex_payload = hex_payload.replace(' ', '').replace('\n', '').replace('\r', '')
        try:
            payload_bytes = bytes.fromhex(hex_payload)
        except ValueError as e:
            self.errors.append(f"Invalid hex data: {e}")
            return []
        
        frames = []
        i = 0
        
        while i < len(payload_bytes):
            # Look for HDLC flag (0x7E)
            if payload_bytes[i] == self.HDLC_FLAG:
                # Found start flag, look for end flag
                start_idx = i + 1
                end_idx = -1
                
                for j in range(start_idx, len(payload_bytes)):
                    if payload_bytes[j] == self.HDLC_FLAG:
                        end_idx = j
                        break
                
                if end_idx != -1:
                    # Extract frame data (between flags)
                    raw_frame_data = payload_bytes[start_idx:end_idx]
                    
                    if len(raw_frame_data) > 0:
                        # Unstuff the data
                        unstuffed_data = self.unstuff_data(raw_frame_data)
                        
                        # Parse the frame
                        frame_info = self.parse_frame(unstuffed_data)
                        if frame_info:
                            frame_info['raw_data'] = raw_frame_data.hex()
                            frame_info['unstuffed_data'] = unstuffed_data.hex()
                            frames.append(frame_info)
                    
                    i = end_idx + 1
                else:
                    # No end flag found
                    break
            else:
                i += 1
        
        self.frames = frames
        return frames
    
    def print_summary(self):
        """Print a summary of parsed frames."""
        print(f"\n=== HDLC Frame Parser Results ===")
        print(f"Total frames found: {len(self.frames)}")
        print(f"Errors encountered: {len(self.errors)}")
        
        if self.errors:
            print("\nErrors:")
            for error in self.errors:
                print(f"  - {error}")
        
        print(f"\nFrame Summary:")
        for i, frame in enumerate(self.frames):
            print(f"\nFrame {i+1}:")
            print(f"  Address: {frame['address']}")
            print(f"  Control: {frame['control']} ({frame['control_info']['type']})")
            print(f"  Info Length: {frame['information_length']} bytes")
            print(f"  FCS Valid: {frame['fcs_valid']}")
            print(f"  Frame Length: {frame['frame_length']} bytes")
    
    def get_frame_details(self, frame_index: int) -> Optional[dict]:
        """Get detailed information about a specific frame."""
        if 0 <= frame_index < len(self.frames):
            return self.frames[frame_index]
        return None
