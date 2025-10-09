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
from Crypto.Cipher import AES
from Crypto.Util import Counter
import logging

class ParserState(Enum):
    IDLE = "idle"
    DATA_BLOCK_START = "data_block_start"
    DATA_CONTINUATION = "data_continuation"
    DATA_BLOCK_END = "data_block_end"
    COMPLETE = "complete"

class SmartMeterFrame:
    """Represents a parsed HDLC frame from the smart meter"""
    
    def __init__(self, raw_data: bytes, start_pos: int, end_pos: int, complete_frame_data: bytes = None):
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.raw_data = raw_data
        self.complete_frame_data = complete_frame_data  # Store complete frame for duplicate detection
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
                
            # For Iskra AM550 frames with format 0x3B, MSB is at position 19 in the complete frame 
            # But in our unstuffed_data, it's at a different position since we removed the first 0x7E
            # The frame structure is: 7E 3B 3D02A4B4F1DE003B284D4B5A5775034F02 95xx xxxx FCA0 7E
            # So MSB (0x95) is at position 18 in unstuffed_data (position 19 in complete frame)
            if len(self.unstuffed_data) >= 19:
                msb_byte = self.unstuffed_data[18]  # MSB at position 18 in unstuffed data
                
                # For debugging - show the actual MSB byte we found
                if msb_byte == 0x95:
                    self.msb_flag = 1  # This is encrypted continuation data
                    self.is_continuation = True
                    self.is_end_marker = False
                elif msb_byte == 0x15:  # End pattern for encrypted data  
                    self.msb_flag = 0  # End marker
                    self.is_continuation = False
                    self.is_end_marker = True
                else:
                    # Check the MSB bit (bit 7) of the byte
                    self.msb_flag = (msb_byte >> 7) & 1
                    self.is_continuation = self.msb_flag == 1
                    self.is_end_marker = self.msb_flag == 0
                    
                # Store the MSB byte for analysis
                self.msb_byte = msb_byte
            else:
                # Short frame - use default
                self.msb_flag = 0
                self.is_continuation = False
                self.is_end_marker = True
                self.msb_byte = 0
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
        """Get the actual payload data including MSB byte for analysis"""
        # For Iskra AM550 frames, return the MSB byte + following data for analysis
        if hasattr(self, 'msb_byte') and len(self.variable_data) > 0:
            # Return MSB byte as first byte of payload for compatibility with analysis code
            return bytes([self.msb_byte]) + (self.variable_data[1:] if len(self.variable_data) > 1 else b'')
        elif len(self.variable_data) > 0:
            return self.variable_data
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
        
        # DLMS/COSEM AES-GCM Configuration according to IEC 62056-5-3 Ed.3
        # Default key from specification - should be replaced with actual meter key
        self.aes_key = bytes.fromhex("A78F4624621DE5EB8A96DA779E08109C")  # 128-bit AES key
        self.enable_decryption = True  # Enable when proper key is available
        self.logger = logging.getLogger(__name__)
    
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
        """
        Parse HDLC frames from byte data using continuous buffer processing
        Matches the improved C code logic for proper frame boundary detection
        """
        frames = []
        continuous_buffer = bytearray(data)
        continuous_pos = len(data)
        
        # Process complete frames from continuous buffer - matching C logic
        search_start = 0
        while search_start < continuous_pos:
            # Look for frame start (0x7E)
            frame_start_idx = search_start
            found_start = False
            
            for i in range(search_start, continuous_pos):
                if continuous_buffer[i] == 0x7E:
                    frame_start_idx = i
                    found_start = True
                    break
            
            if not found_start:
                # No more frame starts found
                break
            
            # Look for frame end (next 0x7E after start)
            frame_end_idx = 0
            found_end = False
            
            for i in range(frame_start_idx + 1, continuous_pos):
                if continuous_buffer[i] == 0x7E:
                    frame_end_idx = i
                    found_end = True
                    break
            
            if not found_end:
                # Incomplete frame - would wait for more data in real-time scenario
                break
            
            # Extract complete frame (including both 0x7E markers)
            frame_length = frame_end_idx - frame_start_idx + 1
            
            # Validate minimum frame size (matching C validation) 
            if frame_length >= 27:  # Iskra AM550 frames should be at least 27 bytes (like in test data)
                if frame_length <= 256:  # Reasonable frame size limit
                    # Extract frame including flags
                    complete_frame_data = bytes(continuous_buffer[frame_start_idx:frame_end_idx + 1])
                    
                    # Validate DLMS frame structure
                    if self._validate_dlms_frame(complete_frame_data):
                        # Create frame object with data between flags for processing
                        frame_data = complete_frame_data[1:-1]  # Remove flags for SmartMeterFrame
                        frame = SmartMeterFrame(frame_data, frame_start_idx, frame_end_idx, complete_frame_data)
                        
                        # Filter out duplicate frames (check if this is identical to the last frame)
                        if not frames or complete_frame_data != frames[-1].complete_frame_data:
                            frames.append(frame)
                            
                            # Analyze MSB pattern for debugging (matching C output)
                            self._analyze_msb_pattern(complete_frame_data)
                            
                            print(f"Parsed valid frame: {frame}")
                        else:
                            print(f"⚠️  Duplicate frame - skipping")
                    else:
                        print(f"⚠️  Invalid frame structure - skipping {frame_length} bytes")
                else:
                    print(f"⚠️  Frame too large ({frame_length} bytes) - skipping")
            else:
                print(f"⚠️  Frame too small ({frame_length} bytes) - skipping")
            
            # Move search position past this frame
            search_start = frame_end_idx + 1
        
        print(f"📊 Frame extraction complete: {len(frames)} valid frames found")
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
        """Process a single-frame data block with optional decryption"""
        raw_payload = frame.get_payload_data()
        
        # Apply decryption if enabled
        decrypted_data = raw_payload
        decryption_status = "raw_data"
        
        if self.enable_decryption and len(raw_payload) > 0:
            try:
                decrypted_data = self._decrypt_dlms_apdu(raw_payload)
                decryption_status = "decrypted"
                print(f"  ✅ Single frame AES-GCM decryption successful")
            except Exception as e:
                self.logger.warning(f"Single frame decryption failed: {e}")
                decryption_status = f"decryption_failed: {str(e)}"
                print(f"  ❌ Single frame decryption failed: {e}")
        
        block_data = {
            'block_id': len(self.complete_blocks) + 1,
            'frame_count': 1,
            'total_size': len(raw_payload),
            'decrypted_size': len(decrypted_data),
            'raw_data': raw_payload.hex(),
            'decrypted_data': decrypted_data.hex() if decrypted_data != raw_payload else None,
            'session_context': frame.fixed_header.hex(),
            'type': 'single_frame',
            'decryption_status': decryption_status
        }
        
        # Parse the data (decrypted if available, raw otherwise)
        parsed_data = self._parse_block_data(decrypted_data)
        block_data.update(parsed_data)
        
        self.complete_blocks.append(block_data)
        print(f"  → Single frame block complete: {len(raw_payload)} bytes ({decryption_status})")
    
    def _process_control_frame(self, frame: SmartMeterFrame):
        """Process a control frame (consecutive end markers) with optional decryption"""
        raw_payload = frame.get_payload_data()
        
        # Apply decryption if enabled (control frames are usually not encrypted)
        decrypted_data = raw_payload
        decryption_status = "raw_data"
        
        if self.enable_decryption and len(raw_payload) > 16:  # Only try if likely encrypted
            try:
                decrypted_data = self._decrypt_dlms_apdu(raw_payload)
                decryption_status = "decrypted"
                print(f"  ✅ Control frame AES-GCM decryption successful")
            except Exception as e:
                # Control frames are often unencrypted, so this is expected
                decryption_status = "unencrypted_control"
                print(f"  ℹ️  Control frame appears unencrypted (normal)")
        
        block_data = {
            'block_id': len(self.complete_blocks) + 1,
            'frame_count': 1,
            'total_size': len(raw_payload),
            'decrypted_size': len(decrypted_data),
            'raw_data': raw_payload.hex(),
            'decrypted_data': decrypted_data.hex() if decrypted_data != raw_payload else None,
            'session_context': frame.fixed_header.hex(),
            'type': 'control_frame',
            'decryption_status': decryption_status
        }
        
        # Parse the data (decrypted if available, raw otherwise)
        parsed_data = self._parse_block_data(decrypted_data)
        block_data.update(parsed_data)
        
        self.complete_blocks.append(block_data)
        print(f"  → Control frame processed: {len(raw_payload)} bytes ({decryption_status})")
    
    def _finalize_current_block(self):
        """
        Finalize the current data block buffer with DLMS/COSEM decryption
        According to IEC 62056-5-3 Ed.3 and NIST SP 800-38D
        """
        if not self.current_block_buffer:
            return
        
        # Step 1: Concatenate all payload data (APDU assembly)
        concatenated_data = b''.join(self.current_block_buffer)
        
        # Step 2: Apply DLMS/COSEM decryption if enabled
        decrypted_data = concatenated_data
        decryption_status = "raw_data"
        
        if self.enable_decryption and len(concatenated_data) > 0:
            try:
                decrypted_data = self._decrypt_dlms_apdu(concatenated_data)
                decryption_status = "decrypted"
                print(f"  ✅ AES-GCM decryption successful: {len(decrypted_data)} bytes")
            except Exception as e:
                self.logger.warning(f"Decryption failed: {e}")
                decryption_status = f"decryption_failed: {str(e)}"
                print(f"  ❌ Decryption failed: {e}")
        
        block_data = {
            'block_id': len(self.complete_blocks) + 1,
            'frame_count': len(self.current_block_buffer),
            'total_size': len(concatenated_data),
            'decrypted_size': len(decrypted_data),
            'raw_data': concatenated_data.hex(),
            'decrypted_data': decrypted_data.hex() if decrypted_data != concatenated_data else None,
            'session_context': self.session_context.hex() if self.session_context else '',
            'type': 'multi_frame',
            'decryption_status': decryption_status
        }
        
        # Step 3: Parse the data (decrypted if available, raw otherwise)
        parsed_data = self._parse_block_data(decrypted_data)
        block_data.update(parsed_data)
        
        self.complete_blocks.append(block_data)
        self.current_block_buffer = []
        
        print(f"  → Multi-frame block complete: {len(concatenated_data)} bytes from {block_data['frame_count']} frames ({decryption_status})")
    
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
    
    def _validate_dlms_frame(self, frame_data: bytes) -> bool:
        """
        Validate DLMS frame structure - matches C code validate_dlms_frame()
        """
        frame_len = len(frame_data)
        
        if frame_len < 3:
            return False  # Minimum frame size
        if frame_data[0] != 0x7E or frame_data[frame_len-1] != 0x7E:
            return False  # Flag validation
        
        # Basic HDLC structure validation
        if frame_len < 6:
            return False  # Need at least: flag + format + address + control + fcs + flag
        
        # Extract format field 
        format_byte = frame_data[1]
        
        # Check if this is a DLMS HDLC frame (0xA0) or encrypted response (0x3B, etc.)
        if (format_byte & 0xF0) == 0xA0:
            # Standard DLMS HDLC frame - validate length
            declared_length = ((format_byte & 0x07) << 8) | frame_data[2]
            if declared_length != frame_len - 2:  # -2 for the flags
                print(f"🔍 Length mismatch: declared {declared_length}, actual {frame_len - 2}")
                return False
            return True
        elif format_byte == 0x3B:
            # Encrypted DLMS response frame - Iskra AM550 specific format
            print(f"🔐 Encrypted DLMS frame detected: format=0x{format_byte:02X}")
            
            # Additional validation for encrypted frames
            if frame_len >= 21:
                # Check for expected header pattern in Iskra AM550
                # Bytes 2-17 should contain the standard header
                expected_header = bytes([0x3D, 0x02, 0xA4, 0xB4, 0xF1, 0xDE, 0x00, 0x3B, 
                                       0x28, 0x4D, 0x4B, 0x5A, 0x57, 0x75, 0x03, 0x4F, 0x02])
                
                header_match = True
                for i in range(len(expected_header)):
                    if frame_data[2 + i] != expected_header[i]:
                        header_match = False
                        break
                
                if header_match:
                    print(f"✅ Valid Iskra AM550 encrypted frame header")
                    
                    # Check MSB/encryption flags
                    msb_byte = frame_data[19]
                    if msb_byte == 0x95:
                        print(f"🔐 AES-GCM encrypted payload detected (MSB=0x95)")
                    else:
                        print(f"📝 MSB pattern: 0x{msb_byte:02X}")
                    return True
                else:
                    print(f"⚠️  Non-standard header in 0x3B frame")
                    return True  # Still accept, but flag as unusual
            return True
        else:
            # Other frame types (identification response, etc.)
            print(f"📄 Non-DLMS frame detected: format=0x{format_byte:02X}")
            return True
    
    def _analyze_msb_pattern(self, frame_data: bytes):
        """
        Analyze MSB patterns in Iskra AM550 frames - matches C code analyze_msb_pattern()
        """
        frame_len = len(frame_data)
        
        if frame_len < 21 or frame_data[1] != 0x3B:
            return  # Only analyze 0x3B frames with sufficient length
        
        msb_byte = frame_data[19]  # MSB at position 19 for 0x3B frames
        control_byte = frame_data[20]  # Control byte follows MSB
        
        print(f"🔍 Frame Analysis:")
        # Convert to binary string for display
        binary_str = format(msb_byte, '08b')
        binary_display = f"{binary_str[:4]} {binary_str[4:]}"
        print(f"   MSB byte: 0x{msb_byte:02X} ({binary_display})")
        print(f"   Control: 0x{control_byte:02X}")
        
        # Interpret MSB flags according to DLMS/COSEM
        if (msb_byte >> 7) & 1:
            print(f"   🔄 Continuation frame (MSB bit 7 = 1)")
        else:
            print(f"   🏁 End frame (MSB bit 7 = 0)")
        
        if (msb_byte >> 4) & 1:
            print(f"   🔐 Encryption enabled (bit 4 = 1)")
            print(f"   📋 Security Suite: DLMS Security Suite 1 (AES-GCM-128)")
        else:
            print(f"   📝 No encryption (bit 4 = 0)")
        
        # Specific pattern analysis
        if msb_byte == 0x95:
            print(f"   🎯 CRITICAL: This is encrypted DLMS data!")
            print(f"   🔑 Requires AES-GCM decryption with correct keys")
            print(f"   📊 Pattern: 10010101 = Continuation + Encryption active")
        elif msb_byte == 0x03:
            print(f"   📄 This appears to be plaintext DLMS data")
        else:
            print(f"   ❓ Unknown MSB pattern - investigate further")
    
    def _decrypt_dlms_apdu(self, encrypted_data: bytes) -> bytes:
        """
        Decrypt DLMS/COSEM APDU using AES-GCM according to IEC 62056-5-3 Ed.3
        and NIST SP 800-38D 8.2.1
        
        Enhanced version with multiple parsing strategies to handle different DLMS implementations
        """
        print(f"  🔍 MAC Verification Failure Analysis:")
        print(f"     Data length: {len(encrypted_data)} bytes")
        print(f"     Raw data: {encrypted_data.hex()}")
        
        # First, check if this data is actually encrypted
        #if not self._looks_like_encrypted_dlms(encrypted_data):
        #    print(f"     ⚠️  Data doesn't look like encrypted DLMS - trying as plaintext")
        #    return encrypted_data

        if len(encrypted_data) < 17:  # Minimum: 1 + 4 + 0 + 12
            raise ValueError(f"Encrypted data too short: {len(encrypted_data)} bytes")
        
        # Try multiple DLMS parsing strategies with detailed analysis
        strategies = [
            ("Standard DLMS", self._try_standard_dlms_decrypt),
            ("Iskra Specific", self._try_iskra_specific_decrypt),
            ("Alternative Header", self._try_alternative_header_decrypt),
            ("No AAD", self._try_no_aad_decrypt),
            ("Different IV", self._try_different_iv_decrypt),
            ("Non-Standard Structure", self._try_nonstandard_structure_decrypt),
            ("CTR Mode Fallback", self._try_ctr_mode_decrypt)
        ]
        
        for strategy_name, strategy_func in strategies:
            try:
                print(f"     Trying {strategy_name}...")
                result = strategy_func(encrypted_data)
                print(f"     ✅ {strategy_name} successful: {len(result)} bytes")
                return result
            except Exception as e:
                print(f"     ❌ {strategy_name} failed: {str(e)[:80]}...")
                continue
        
        # If all strategies fail, try to provide more insight
        self._deep_analyze_encryption_failure(encrypted_data)
        raise ValueError("All DLMS decryption strategies failed - data may not be AES-GCM encrypted")
    
    def _try_standard_dlms_decrypt(self, encrypted_data: bytes) -> bytes:
        """Standard DLMS/COSEM decryption strategy"""
        security_control = encrypted_data[0]
        frame_counter = struct.unpack('>I', encrypted_data[1:5])[0]
        ciphertext = encrypted_data[5:-12]
        auth_tag = encrypted_data[-12:]
        
        print(f"       Security Control: 0x{security_control:02X}")
        print(f"       Frame Counter: {frame_counter}")
        print(f"       Ciphertext: {len(ciphertext)} bytes")
        print(f"       Auth Tag: {auth_tag.hex()}")
        
        iv = self._construct_dlms_iv(frame_counter, security_control)
        aad = self._construct_dlms_aad(security_control, frame_counter)
        
        print(f"       IV: {iv.hex()}")
        print(f"       AAD: {aad.hex()}")
        
        cipher = AES.new(self.aes_key, AES.MODE_GCM, nonce=iv)
        cipher.update(aad)
        return cipher.decrypt_and_verify(ciphertext, auth_tag)
    
    def _try_alternative_header_decrypt(self, encrypted_data: bytes) -> bytes:
        """Alternative header parsing - some meters use different structures"""
        # Try parsing without security control byte
        frame_counter = struct.unpack('>I', encrypted_data[0:4])[0]
        ciphertext = encrypted_data[4:-12]
        auth_tag = encrypted_data[-12:]
        
        iv = self._construct_dlms_iv(frame_counter, 0x30)  # Default security control
        aad = struct.pack('>I', frame_counter)  # Only frame counter in AAD
        
        cipher = AES.new(self.aes_key, AES.MODE_GCM, nonce=iv)
        cipher.update(aad)
        return cipher.decrypt_and_verify(ciphertext, auth_tag)
    
    def _try_no_aad_decrypt(self, encrypted_data: bytes) -> bytes:
        """Try decryption without AAD - some implementations don't use it"""
        security_control = encrypted_data[0]
        frame_counter = struct.unpack('>I', encrypted_data[1:5])[0]
        ciphertext = encrypted_data[5:-12]
        auth_tag = encrypted_data[-12:]
        
        iv = self._construct_dlms_iv(frame_counter, security_control)
        
        cipher = AES.new(self.aes_key, AES.MODE_GCM, nonce=iv)
        # No AAD update
        return cipher.decrypt_and_verify(ciphertext, auth_tag)
    
    def _try_different_iv_decrypt(self, encrypted_data: bytes) -> bytes:
        """Try with different IV construction - some meters use variations"""
        security_control = encrypted_data[0]
        frame_counter = struct.unpack('>I', encrypted_data[1:5])[0]
        ciphertext = encrypted_data[5:-12]
        auth_tag = encrypted_data[-12:]
        
        # Alternative IV: Frame Counter + System Title (reversed order)
        system_title = b'\x49\x53\x4B\x52\x41\x41\x4D\x35'
        iv = struct.pack('>I', frame_counter) + system_title
        
        aad = self._construct_dlms_aad(security_control, frame_counter)
        
        cipher = AES.new(self.aes_key, AES.MODE_GCM, nonce=iv)
        cipher.update(aad)
        return cipher.decrypt_and_verify(ciphertext, auth_tag)
    
    def _try_iskra_specific_decrypt(self, encrypted_data: bytes) -> bytes:
        """Try Iskra AM550 specific variations"""
        # Some Iskra meters use different structures
        if len(encrypted_data) >= 20:
            # Try with different auth tag length (16 bytes instead of 12)
            ciphertext = encrypted_data[5:-16]
            auth_tag = encrypted_data[-16:]
            
            security_control = encrypted_data[0]
            frame_counter = struct.unpack('>I', encrypted_data[1:5])[0]
            
            iv = self._construct_dlms_iv(frame_counter, security_control)
            aad = self._construct_dlms_aad(security_control, frame_counter)
            
            cipher = AES.new(self.aes_key, AES.MODE_GCM, nonce=iv)
            cipher.update(aad)
            return cipher.decrypt_and_verify(ciphertext, auth_tag)
        
        raise ValueError("Not enough data for Iskra specific format")
    
    def _try_nonstandard_structure_decrypt(self, encrypted_data: bytes) -> bytes:
        """Try non-standard DLMS structure variations"""
        # Try interpreting data without security header
        if len(encrypted_data) >= 16:
            ciphertext = encrypted_data[:-12]
            auth_tag = encrypted_data[-12:]
            
            # Use fixed IV based on known patterns
            iv = b'\x00\x00\x00\x00' + self.aes_key[:8]  # Simplified IV
            
            cipher = AES.new(self.aes_key, AES.MODE_GCM, nonce=iv)
            # No AAD
            return cipher.decrypt_and_verify(ciphertext, auth_tag)
        
        raise ValueError("Not enough data for non-standard format")
    
    def _try_ctr_mode_decrypt(self, encrypted_data: bytes) -> bytes:
        """Fallback: Try AES-CTR if GCM fails (some meters use CTR)"""
        # Remove potential auth tag
        ciphertext = encrypted_data[5:-12] if len(encrypted_data) > 17 else encrypted_data[5:]
        
        # Use frame counter as IV
        if len(encrypted_data) >= 5:
            frame_counter = struct.unpack('>I', encrypted_data[1:5])[0]
            # Create CTR IV: frame counter + padding
            iv = struct.pack('>I', frame_counter) + b'\x00' * 12
            
            # Try AES-CTR
            cipher = AES.new(self.aes_key, AES.MODE_CTR, nonce=iv[:16])
            decrypted = cipher.decrypt(ciphertext)
            
            # Validate result looks reasonable
            if self._validate_decrypted_data(decrypted):
                return decrypted
        
        raise ValueError("CTR mode decryption failed or produced invalid data")
    
    def _looks_like_encrypted_dlms(self, data: bytes) -> bool:
        """Check if data looks like it could be encrypted DLMS"""
        if len(data) < 17:
            return False
        
        # Check for patterns that suggest encryption
        entropy = self._calculate_entropy(data)
        
        # Encrypted data should have high entropy (> 7.0)
        if entropy < 6.0:
            return False
        
        # Check if first bytes look like DLMS security header
        security_control = data[0]
        if not (0x10 <= security_control <= 0x3F):
            return False
        
        # Check frame counter is reasonable
        if len(data) >= 5:
            frame_counter = struct.unpack('>I', data[1:5])[0]
            if frame_counter == 0 or frame_counter > 0xFFFFFF:  # Very high values unlikely
                return False
        
        return True
    
    def _calculate_entropy(self, data: bytes) -> float:
        """Calculate Shannon entropy of data"""
        if not data:
            return 0.0
        
        freq = [0] * 256
        for byte in data:
            freq[byte] += 1
        
        entropy = 0.0
        data_len = len(data)
        for count in freq:
            if count > 0:
                p = count / data_len
                entropy -= p * self._log2(p)  # Use existing log2 method
        
        return entropy
    
    def _validate_decrypted_data(self, data: bytes) -> bool:
        """Check if decrypted data looks valid"""
        if not data:
            return False
        
        # Check for DLMS/COSEM patterns
        # Look for common DLMS tags
        dlms_tags = {0x01, 0x02, 0x06, 0x09, 0x0A, 0x0C, 0x10, 0x11, 0x12, 0x13, 0x14, 0x15}
        
        # At least some bytes should be DLMS tags
        tag_count = sum(1 for b in data[:20] if b in dlms_tags)
        
        # Or check for ASCII patterns (OBIS codes)
        ascii_count = sum(1 for b in data if 32 <= b <= 126)
        
        return tag_count > 0 or ascii_count > len(data) * 0.3
    
    def _deep_analyze_encryption_failure(self, data: bytes):
        """Provide deep analysis of why decryption is failing"""
        print(f"\n     🔬 Deep Analysis of Encryption Failure:")
        print(f"        Data entropy: {self._calculate_entropy(data):.2f} (encrypted usually >7.0)")
        
        if len(data) >= 5:
            security_control = data[0]
            frame_counter = struct.unpack('>I', data[1:5])[0]
            print(f"        Security control: 0x{security_control:02X}")
            print(f"        Frame counter: {frame_counter} (0x{frame_counter:08X})")
        
        # Check for common patterns
        repeating_bytes = {}
        for b in data:
            repeating_bytes[b] = repeating_bytes.get(b, 0) + 1
        
        most_common = max(repeating_bytes.items(), key=lambda x: x[1])
        print(f"        Most common byte: 0x{most_common[0]:02X} appears {most_common[1]} times")
        
        # Check if it might be plaintext
        printable = sum(1 for b in data if 32 <= b <= 126)
        print(f"        Printable ASCII: {printable}/{len(data)} ({100*printable/len(data):.1f}%)")
        
        if printable > len(data) * 0.5:
            print(f"        💡 Suggestion: Data might be plaintext, not encrypted")
        
        # Look for OBIS-like patterns
        try:
            text = data.decode('ascii', errors='ignore')
            if '-' in text and ':' in text and '.' in text:
                print(f"        💡 Suggestion: Contains OBIS-like patterns, likely plaintext")
        except:
            pass
    
    def _construct_dlms_iv(self, frame_counter: int, security_control: int) -> bytes:
        """
        Construct DLMS/COSEM Initialization Vector according to IEC 62056-5-3 Ed.3
        IV structure (12 bytes):
        - System Title (8 bytes) - typically from meter ID
        - Frame Counter (4 bytes, big endian)
        """
        # Use configured system title or default
        system_title = getattr(self, 'system_title', b'\x49\x53\x4B\x52\x41\x41\x4D\x35')
        
        # Construct IV: System Title (8) + Frame Counter (4)
        iv = system_title + struct.pack('>I', frame_counter)
        
        return iv
    
    def _construct_dlms_aad(self, security_control: int, frame_counter: int) -> bytes:
        """
        Construct Additional Authenticated Data for DLMS/COSEM AES-GCM
        AAD ensures integrity of unencrypted header fields
        """
        # AAD typically includes security control and frame counter
        aad = struct.pack('B', security_control) + struct.pack('>I', frame_counter)
        
        return aad
    
    def set_aes_key(self, key: str):
        """
        Set the AES encryption key for DLMS/COSEM decryption
        
        Args:
            key: Hex string of the 128-bit AES key (32 hex characters)
        """
        try:
            self.aes_key = bytes.fromhex(key)
            if len(self.aes_key) != 16:
                raise ValueError(f"AES key must be 128 bits (16 bytes), got {len(self.aes_key)}")
            
            self.enable_decryption = True
            print(f"✅ AES key configured: {key}")
            
        except ValueError as e:
            self.logger.error(f"Invalid AES key: {e}")
            raise
    
    def set_system_title(self, system_title: str):
        """
        Set the system title for IV construction
        
        Args:
            system_title: Hex string of the 8-byte system title (16 hex characters)
        """
        try:
            self.system_title = bytes.fromhex(system_title)
            if len(self.system_title) != 8:
                raise ValueError(f"System title must be 8 bytes, got {len(self.system_title)}")
            
            print(f"✅ System title configured: {system_title}")
            
        except ValueError as e:
            self.logger.error(f"Invalid system title: {e}")
            raise
    
    def diagnose_decryption_failure(self, encrypted_data: bytes) -> Dict:
        """
        Diagnose why decryption might be failing
        Returns diagnostic information to help troubleshoot
        """
        diagnosis = {
            'data_length': len(encrypted_data),
            'data_hex': encrypted_data.hex(),
            'checks': [],
            'recommendations': []
        }
        
        # Check data length
        if len(encrypted_data) < 17:
            diagnosis['checks'].append(f"❌ Data too short: {len(encrypted_data)} bytes (need ≥17)")
            diagnosis['recommendations'].append("Check if data contains full DLMS security header")
        else:
            diagnosis['checks'].append(f"✅ Data length OK: {len(encrypted_data)} bytes")
        
        # Analyze structure
        if len(encrypted_data) >= 5:
            security_control = encrypted_data[0]
            frame_counter = struct.unpack('>I', encrypted_data[1:5])[0]
            
            diagnosis['security_control'] = f"0x{security_control:02X}"
            diagnosis['frame_counter'] = frame_counter
            
            # Check for reasonable values
            if 0x10 <= security_control <= 0x3F:
                diagnosis['checks'].append(f"✅ Security control looks valid: 0x{security_control:02X}")
            else:
                diagnosis['checks'].append(f"⚠️  Security control unusual: 0x{security_control:02X}")
                diagnosis['recommendations'].append("Verify security control byte position")
            
            if 0 < frame_counter < 0xFFFFFFFF:
                diagnosis['checks'].append(f"✅ Frame counter looks valid: {frame_counter}")
            else:
                diagnosis['checks'].append(f"⚠️  Frame counter unusual: {frame_counter}")
                diagnosis['recommendations'].append("Check frame counter endianness or position")
        
        # Check for common issues
        auth_tag = encrypted_data[-12:] if len(encrypted_data) >= 12 else b''
        if len(auth_tag) == 12:
            diagnosis['auth_tag'] = auth_tag.hex()
            if auth_tag == b'\x00' * 12:
                diagnosis['checks'].append("❌ Auth tag is all zeros - data might not be encrypted")
                diagnosis['recommendations'].append("Check if this data block actually contains encrypted content")
            else:
                diagnosis['checks'].append("✅ Auth tag has non-zero values")
        
        # Key and configuration checks
        diagnosis['aes_key'] = self.aes_key.hex()
        diagnosis['system_title'] = getattr(self, 'system_title', b'\x49\x53\x4B\x52\x41\x41\x4D\x35').hex()
        
        if not hasattr(self, 'system_title'):
            diagnosis['recommendations'].append("Consider setting specific system title with set_system_title()")
        
        diagnosis['recommendations'].extend([
            "Verify AES key is correct for this specific meter",
            "Check if meter uses standard DLMS/COSEM encryption",
            "Some meters may use proprietary encryption schemes"
        ])
        
        return diagnosis
    
    def try_decrypt_without_verification(self, encrypted_data: bytes) -> bytes:
        """
        Try to decrypt without MAC verification to isolate the issue.
        WARNING: This bypasses authentication and should only be used for debugging!
        """
        print(f"  ⚠️  Attempting decryption WITHOUT MAC verification (debug only)")
        
        if len(encrypted_data) < 17:
            raise ValueError(f"Data too short: {len(encrypted_data)} bytes")
        
        try:
            security_control = encrypted_data[0]
            frame_counter = struct.unpack('>I', encrypted_data[1:5])[0]
            ciphertext = encrypted_data[5:-12]
            
            print(f"     Security Control: 0x{security_control:02X}")
            print(f"     Frame Counter: {frame_counter}")
            print(f"     Ciphertext length: {len(ciphertext)} bytes")
            
            iv = self._construct_dlms_iv(frame_counter, security_control)
            print(f"     IV: {iv.hex()}")
            
            # Try GCM mode but only decrypt (no verification)
            cipher = AES.new(self.aes_key, AES.MODE_GCM, nonce=iv)
            decrypted = cipher.decrypt(ciphertext)
            
            print(f"     🔓 Decryption (no verify): {len(decrypted)} bytes")
            print(f"     Result preview: {decrypted[:50].hex()}...")
            
            # Check if result looks valid
            if self._validate_decrypted_data(decrypted):
                print(f"     ✅ Decrypted data looks valid - MAC/AAD issue likely")
            else:
                print(f"     ❌ Decrypted data looks invalid - key/IV issue likely")
            
            return decrypted
            
        except Exception as e:
            print(f"     ❌ Even decrypt-only failed: {e}")
            raise
    
    def enable_dlms_decryption(self, enable: bool = True):
        """Enable or disable DLMS/COSEM AES-GCM decryption"""
        self.enable_decryption = enable
        status = "enabled" if enable else "disabled"
        print(f"🔒 DLMS decryption {status}")
    
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
