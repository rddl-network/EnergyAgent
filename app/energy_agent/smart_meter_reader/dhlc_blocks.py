#!/usr/bin/env python3
"""
Smart Meter Payload Extractor for Iskra AM550
Handles HDLC frame parsing and payload assembly based on MSB flags
"""

import struct
from typing import List, Dict, Optional, Tuple
from enum import Enum
import re
import binascii

class ParserState(Enum):
    IDLE = "idle"
    DATA_BLOCK_START = "data_block_start"
    DATA_CONTINUATION = "data_continuation"
    DATA_BLOCK_END = "data_block_end"
    COMPLETE = "complete"

class SmartMeterFrame:
    """Represents a parsed HDLC frame from the smart meter"""
    
    def __init__(self, raw_data: bytes, start_pos: int, end_pos: int):
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.raw_data = raw_data
        self.unstuffed_data = self._unstuff_data(raw_data)
        
        # Parse frame components
        if len(self.unstuffed_data) >= 4:
            self.address = self.unstuffed_data[0]
            self.control = self.unstuffed_data[1]
            self.fixed_header = self.unstuffed_data[0:19] if len(self.unstuffed_data) >= 19 else self.unstuffed_data[0:2]
            
            # Variable data starts after fixed header (19 bytes) and excludes FCS (last 2 bytes)
            if len(self.unstuffed_data) > 21:  # Header + at least 1 byte + FCS
                self.variable_data = self.unstuffed_data[19:-2]
            else:
                self.variable_data = b''
                
            # Extract FCS
            if len(self.unstuffed_data) >= 2:
                self.fcs = struct.unpack('<H', self.unstuffed_data[-2:])[0]
            else:
                self.fcs = 0
                
            # Determine packet type based on MSB
            if self.variable_data:
                self.msb_flag = (self.variable_data[0] >> 7) & 1
                self.is_continuation = self.msb_flag == 1
                self.is_end_marker = self.msb_flag == 0
            else:
                self.msb_flag = 0
                self.is_continuation = False
                self.is_end_marker = True
        else:
            # Invalid frame
            self.address = 0
            self.control = 0
            self.fixed_header = b''
            self.variable_data = b''
            self.fcs = 0
            self.msb_flag = 0
            self.is_continuation = False
            self.is_end_marker = True
    
    def _unstuff_data(self, data: bytes) -> bytes:
        """Remove HDLC byte stuffing (0x7D escape sequences)"""
        if not data:
            return b''
            
        unstuffed = bytearray()
        i = 0
        while i < len(data):
            if data[i] == 0x7D and i + 1 < len(data):
                # Escape sequence: XOR next byte with 0x20
                unstuffed.append(data[i + 1] ^ 0x20)
                i += 2
            else:
                unstuffed.append(data[i])
                i += 1
        return bytes(unstuffed)
    
    def get_payload_data(self) -> bytes:
        """Get the actual payload data (excluding MSB flag)"""
        if len(self.variable_data) > 1:
            return self.variable_data[1:]  # Skip MSB flag byte
        return b''
    
    def __str__(self) -> str:
        return (f"Frame(pos={self.start_pos}-{self.end_pos}, "
                f"addr=0x{self.address:02X}, ctrl=0x{self.control:02X}, "
                f"msb={self.msb_flag}, payload={len(self.get_payload_data())} bytes)")

class SmartMeterPayloadExtractor:
    """
    Extracts and assembles payload data from Iskra AM550 smart meter HDLC frames.
    
    Uses a state machine to handle packet fragmentation based on MSB flags:
    - MSB=1 (0xB8): Data continuation packet
    - MSB=0 (0x38): End of data block packet
    """
    
    def __init__(self):
        self.state = ParserState.IDLE
        self.current_block_buffer = []
        self.complete_blocks = []
        self.session_context = None
        self.frame_count = 0
        self.errors = []
    
    def process_hex_payload(self, hex_payload: str) -> List[Dict]:
        """
        Process a complete hex payload string and extract all data blocks.
        
        Args:
            hex_payload: Hex string of the complete transmission
            
        Returns:
            List of extracted data blocks with metadata
        """
        # Clean hex string
        hex_payload = hex_payload.replace(' ', '').replace('\n', '').replace('\r', '')
        
        try:
            payload_bytes = bytes.fromhex(hex_payload)
        except ValueError as e:
            self.errors.append(f"Invalid hex data: {e}")
            return []
        
        # Parse all HDLC frames
        frames = self._parse_hdlc_frames(payload_bytes)
        
        # Process frames through state machine
        for frame in frames:
            self._process_frame(frame)
        
        # Finalize any remaining block
        if self.current_block_buffer:
            self._finalize_current_block()
        
        return self.get_results()
    
    def _parse_hdlc_frames(self, data: bytes) -> List[SmartMeterFrame]:
        """Parse HDLC frames from byte data"""
        frames = []
        i = 0
        
        while i < len(data):
            if data[i] == 0x7E:  # HDLC flag
                start_pos = i
                
                # Find next flag
                end_pos = -1
                for j in range(i + 1, len(data)):
                    if data[j] == 0x7E:
                        end_pos = j
                        break
                
                if end_pos != -1 and end_pos > start_pos + 1:
                    # Extract frame data (between flags)
                    frame_data = data[start_pos + 1:end_pos]
                    
                    if len(frame_data) > 0:
                        frame = SmartMeterFrame(frame_data, start_pos, end_pos)
                        frames.append(frame)
                        print(f"Parsed: {frame}")
                    
                    i = end_pos + 1
                else:
                    i += 1
            else:
                i += 1
        
        return frames
    
    def _process_frame(self, frame: SmartMeterFrame):
        """Process a single frame through the state machine"""
        self.frame_count += 1
        
        print(f"\nProcessing frame {self.frame_count}: State={self.state.value}, MSB={frame.msb_flag}")
        
        if self.state == ParserState.IDLE:
            if frame.is_continuation:
                self.state = ParserState.DATA_BLOCK_START
                self.session_context = frame.fixed_header
                self.current_block_buffer = [frame.get_payload_data()]
                print(f"  → Started new data block")
            elif frame.is_end_marker:
                # Single frame block
                self._process_single_frame_block(frame)
        
        elif self.state in [ParserState.DATA_BLOCK_START, ParserState.DATA_CONTINUATION]:
            if frame.is_continuation:
                self.state = ParserState.DATA_CONTINUATION
                self.current_block_buffer.append(frame.get_payload_data())
                print(f"  → Added to buffer (total: {len(self.current_block_buffer)} packets)")
            elif frame.is_end_marker:
                self.state = ParserState.DATA_BLOCK_END
                self.current_block_buffer.append(frame.get_payload_data())
                self._finalize_current_block()
                print(f"  → Finalized data block")
        
        elif self.state == ParserState.DATA_BLOCK_END:
            if frame.is_continuation:
                # Start new block
                self.state = ParserState.DATA_BLOCK_START
                self.current_block_buffer = [frame.get_payload_data()]
                print(f"  → Started new data block")
            elif frame.is_end_marker:
                # Control frame or multiple end markers
                self._process_control_frame(frame)
    
    def _process_single_frame_block(self, frame: SmartMeterFrame):
        """Process a single-frame data block"""
        raw_payload = frame.get_payload_data()
        
        block_data = {
            'block_id': len(self.complete_blocks) + 1,
            'frame_count': 1,
            'total_size': len(raw_payload),
            'raw_data': raw_payload.hex(),  # Convert bytes to hex string
            'session_context': frame.fixed_header.hex(),  # Convert bytes to hex string
            'type': 'single_frame'
        }
        
        # Try to parse the data
        parsed_data = self._parse_block_data(raw_payload)
        block_data.update(parsed_data)
        
        self.complete_blocks.append(block_data)
        print(f"  → Single frame block complete: {len(raw_payload)} bytes")
    
    def _process_control_frame(self, frame: SmartMeterFrame):
        """Process a control frame (consecutive end markers)"""
        raw_payload = frame.get_payload_data()
        
        block_data = {
            'block_id': len(self.complete_blocks) + 1,
            'frame_count': 1,
            'total_size': len(raw_payload),
            'raw_data': raw_payload.hex(),  # Convert bytes to hex string
            'session_context': frame.fixed_header.hex(),  # Convert bytes to hex string
            'type': 'control_frame'
        }
        
        # Try to parse the data
        parsed_data = self._parse_block_data(raw_payload)
        block_data.update(parsed_data)
        
        self.complete_blocks.append(block_data)
        print(f"  → Control frame processed: {len(raw_payload)} bytes")
    
    def _finalize_current_block(self):
        """Finalize the current data block buffer"""
        if not self.current_block_buffer:
            return
        
        # Concatenate all payload data
        concatenated_data = b''.join(self.current_block_buffer)
        
        block_data = {
            'block_id': len(self.complete_blocks) + 1,
            'frame_count': len(self.current_block_buffer),
            'total_size': len(concatenated_data),
            'raw_data': concatenated_data.hex(),  # Convert bytes to hex string
            'session_context': self.session_context.hex() if self.session_context else '',  # Convert bytes to hex string
            'type': 'multi_frame'
        }
        
        # Try to parse the concatenated data
        parsed_data = self._parse_block_data(concatenated_data)
        block_data.update(parsed_data)
        
        self.complete_blocks.append(block_data)
        self.current_block_buffer = []
        
        print(f"  → Multi-frame block complete: {len(concatenated_data)} bytes from {block_data['frame_count']} frames")
    
    def _parse_block_data(self, data: bytes) -> Dict:
        """
        Parse the concatenated block data to extract meaningful information.
        This is where you'd implement DLMS/COSEM or OBIS code parsing.
        """
        parsed = {
            'hex_data': data.hex(),
            'ascii_preview': self._get_ascii_preview(data),
            'potential_obis_codes': self._find_obis_patterns(data),
            'potential_values': self._find_numeric_patterns(data),
            'data_analysis': self._analyze_data_structure(data)
        }
        
        return parsed
    
    def _get_ascii_preview(self, data: bytes, max_length: int = 100) -> str:
        """Get ASCII preview of data, replacing non-printable chars"""
        preview = ""
        for byte in data[:max_length]:
            if 32 <= byte <= 126:  # Printable ASCII
                preview += chr(byte)
            else:
                preview += f"\\x{byte:02x}"
        
        if len(data) > max_length:
            preview += "..."
        
        return preview
    
    def _find_obis_patterns(self, data: bytes) -> List[str]:
        """Look for OBIS code patterns in the data"""
        patterns = []
        
        # Convert to string for regex search
        try:
            text = data.decode('ascii', errors='ignore')
            
            # OBIS pattern: A-B:C.D.E*F or variations
            obis_regex = r'(\d+-\d+:\d+\.\d+\.\d+(?:\*\d+)?)'
            matches = re.findall(obis_regex, text)
            patterns.extend(matches)
            
            # Look for value patterns: (value*unit)
            value_regex = r'\(([0-9.]+)\*?([a-zA-Z]*)\)'
            value_matches = re.findall(value_regex, text)
            for value, unit in value_matches:
                patterns.append(f"Value: {value} {unit}")
                
        except:
            pass
        
        return patterns
    
    def _find_numeric_patterns(self, data: bytes) -> List[str]:
        """Find potential numeric values in the data"""
        patterns = []
        
        # Look for float patterns in bytes
        for i in range(len(data) - 3):
            try:
                # Try as 32-bit float (little endian)
                float_val = struct.unpack('<f', data[i:i+4])[0]
                if 0.001 < abs(float_val) < 999999 and not (float_val != float_val):  # Check for NaN
                    patterns.append(f"Float at {i}: {float_val:.3f}")
            except:
                pass
            
            try:
                # Try as 32-bit float (big endian)
                float_val = struct.unpack('>f', data[i:i+4])[0]
                if 0.001 < abs(float_val) < 999999 and not (float_val != float_val):  # Check for NaN
                    patterns.append(f"Float BE at {i}: {float_val:.3f}")
            except:
                pass
            
            try:
                # Try as 32-bit integer (little endian)
                int_val = struct.unpack('<I', data[i:i+4])[0]
                if 0 < int_val < 1000000:  # Reasonable range
                    patterns.append(f"Int at {i}: {int_val}")
            except:
                pass
            
            try:
                # Try as 16-bit integer (little endian)
                if i < len(data) - 1:
                    int_val = struct.unpack('<H', data[i:i+2])[0]
                    if 0 < int_val < 65535:  # Full 16-bit range
                        patterns.append(f"Short at {i}: {int_val}")
            except:
                pass
        
        return patterns[:15]  # Limit output
    
    def _analyze_data_structure(self, data: bytes) -> Dict:
        """Analyze the structure and characteristics of the data"""
        if not data:
            return {'entropy': 0, 'structure': 'empty', 'length': 0, 'unique_bytes': 0, 'most_common_byte': '0x00'}
        
        # Calculate Shannon entropy properly
        freq = [0] * 256
        for byte in data:
            freq[byte] += 1
        
        entropy = 0.0
        data_len = len(data)
        for count in freq:
            if count > 0:
                p = count / data_len
                entropy -= p * self._log2(p)  # Shannon entropy formula
        
        # Check for patterns
        max_freq = max(freq)
        most_common_byte_index = freq.index(max_freq)
        
        structure_info = {
            'entropy': round(entropy, 2),
            'length': len(data),
            'unique_bytes': sum(1 for x in freq if x > 0),
            'most_common_byte': f"0x{most_common_byte_index:02X}",
            'structure': 'binary'
        }
        
        # Check if it looks like text
        printable_count = sum(1 for b in data if 32 <= b <= 126)
        if printable_count > len(data) * 0.7:
            structure_info['structure'] = 'text_like'
        
        return structure_info
    
    def _log2(self, x: float) -> float:
        """Calculate log base 2 using natural log"""
        import math
        return math.log(x) / math.log(2)
    
    def get_results(self) -> List[Dict]:
        """Get all extracted and processed data blocks"""
        return self.complete_blocks
    
    def print_summary(self):
        """Print a summary of the extraction results"""
        print(f"\n=== Smart Meter Payload Extraction Summary ===")
        print(f"Total frames processed: {self.frame_count}")
        print(f"Data blocks extracted: {len(self.complete_blocks)}")
        print(f"Errors encountered: {len(self.errors)}")
        
        if self.errors:
            print("\nErrors:")
            for error in self.errors:
                print(f"  - {error}")
        
        print(f"\nExtracted Data Blocks:")
        for i, block in enumerate(self.complete_blocks):
            print(f"\nBlock {block['block_id']}:")
            print(f"  Type: {block['type']}")
            print(f"  Frames: {block['frame_count']}")
            print(f"  Size: {block['total_size']} bytes")
            print(f"  Entropy: {block['data_analysis']['entropy']}")
            print(f"  Structure: {block['data_analysis']['structure']}")
            
            if block['potential_obis_codes']:
                print(f"  OBIS codes found: {block['potential_obis_codes']}")
            
            if block['potential_values']:
                print(f"  Potential values: {block['potential_values'][:3]}")  # Show first 3
            
            print(f"  Hex: {block['hex_data']}")
