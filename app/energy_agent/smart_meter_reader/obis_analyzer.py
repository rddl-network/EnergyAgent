#!/usr/bin/env python3
"""
OBIS Code and Smart Meter Data Analyzer
Analyzes extracted blocks from Iskra AM550 for DLMS/COSEM structures and energy measurements
"""

import struct
from typing import List, Dict, Tuple, Optional
import re
from datetime import datetime

class OBISAnalyzer:
    """
    Analyzes smart meter data blocks for OBIS codes and energy measurements.
    OBIS format: A-B:C.D.E*F where:
    A = Medium (0=abstract, 1=electricity, 6=heat, 7=gas, 8=water)
    B = Channel (0=no channel)
    C = Physical value (1=active power+, 2=active power-, etc.)
    D = Measurement type (8=cumulative energy, 7=instantaneous)
    E = Tariff (0=total, 1=tariff 1, 2=tariff 2)
    F = Billing period (typically omitted for current values)
    
    Supports DLMS/COSEM according to IEC 62056-5-3 Ed.3
    """
    
    def __init__(self):
        # DLMS/COSEM Initialization Vector according to NIST SP 800-38D 8.2.1
        # and IEC 62056-5-3 Ed.3 - 5.3.3.7.3
        self.DECRYPTION_KEY = "A78F4624621DE5EB8A96DA779E08109C"
        # TODO: Implement AES decryption according to NIST SP 800-38D
        # self.decryptor = AESDecryptor(DECRYPTION_KEY) 
        
        # Extended OBIS codes based on DLMS/COSEM specification
        self.known_obis_codes = {
            # Time and Date
            '0-0:1.0.0': 'Uhrzeit und Datum',  # Date/Time - OctetString[12]
            
            # Active Energy Import/Export (Wirkenergie)
            '1-0:1.8.0': 'Wirkenergie +A (Total)',      # Unsigned32
            '1-0:2.8.0': 'Wirkenergie -A (Total)',      # Unsigned32
            
            # Reactive Energy Import/Export (Blindenergie)
            '1-0:3.8.0': 'Blindenergie +R (Total)',     # Unsigned32
            '1-0:4.8.0': 'Blindenergie -R (Total)',     # Unsigned32
            
            # Instantaneous Power Values (Momentanleistung)
            '1-0:1.7.0': 'Momentanleistung +P (W)',     # Unsigned32
            '1-0:2.7.0': 'Momentanleistung -P (W)',     # Unsigned32
            '1-0:3.7.0': 'Momentanleistung +Q (var)',   # Unsigned32
            '1-0:4.7.0': 'Momentanleistung -Q (var)',   # Unsigned32
            
            # Additional common OBIS codes
            '1-0:1.8.1': 'Active Energy Import Tariff 1 (kWh)', 
            '1-0:1.8.2': 'Active Energy Import Tariff 2 (kWh)',
            '1-0:2.8.1': 'Active Energy Export Tariff 1 (kWh)',
            '1-0:2.8.2': 'Active Energy Export Tariff 2 (kWh)',
            '1-0:32.7.0': 'Instantaneous Voltage L1 (V)',
            '1-0:52.7.0': 'Instantaneous Voltage L2 (V)', 
            '1-0:72.7.0': 'Instantaneous Voltage L3 (V)',
            '1-0:31.7.0': 'Instantaneous Current L1 (A)',
            '1-0:51.7.0': 'Instantaneous Current L2 (A)',
            '1-0:71.7.0': 'Instantaneous Current L3 (A)',
            '1-0:14.7.0': 'Supply Frequency (Hz)',
            '0-0:96.1.1': 'Meter Serial Number',
            '0-0:96.14.0': 'Current Tariff',
        }
        
        # DLMS data type mapping according to IEC 62056-5-3
        self.dlms_data_types = {
            0x00: {'name': 'null-data', 'parser': self._parse_null},
            0x01: {'name': 'boolean', 'parser': self._parse_boolean},
            0x02: {'name': 'bit-string', 'parser': self._parse_bit_string},
            0x03: {'name': 'double-long', 'parser': self._parse_double_long},
            0x04: {'name': 'double-long-unsigned', 'parser': self._parse_double_long_unsigned},
            0x05: {'name': 'floating-point', 'parser': self._parse_floating_point},
            0x06: {'name': 'octet-string', 'parser': self._parse_octet_string},
            0x09: {'name': 'visible-string', 'parser': self._parse_visible_string},
            0x0A: {'name': 'utf8-string', 'parser': self._parse_utf8_string},
            0x0C: {'name': 'date-time', 'parser': self._parse_dlms_datetime_extended},  # OctetString[12]
            0x0F: {'name': 'long', 'parser': self._parse_long},
            0x10: {'name': 'unsigned', 'parser': self._parse_unsigned},
            0x11: {'name': 'long-unsigned', 'parser': self._parse_long_unsigned},
            0x12: {'name': 'compact-array', 'parser': self._parse_compact_array},
            0x13: {'name': 'array', 'parser': self._parse_array},
            0x14: {'name': 'structure', 'parser': self._parse_structure},
            0x15: {'name': 'enum', 'parser': self._parse_enum},
        }
    
    def analyze_block(self, block: bytes) -> Dict:
        """
        Analyze a single raw block for OBIS codes and energy data
        
        Args:
            block: Raw bytes data from smart meter
            
        Returns:
            Dict containing analysis results for the single block
        """
        results = {
            'block_size': len(block),
            'obis_codes': self._find_obis_codes(block),
            'dlms_structures': self._analyze_dlms_structure(block),
            'energy_values': self._extract_energy_values(block),
            'timestamps': self._find_timestamps(block),
            'ascii_strings': self._find_ascii_strings(block),
            'numeric_patterns': self._analyze_numeric_patterns(block),
            'hex_analysis': self._analyze_hex_patterns(block),
            'encryption_info': self._analyze_encryption_status(block),
            'summary': {}
        }
        
        # Generate summary for this single block
        results['summary'] = {
            'obis_codes_found': len(results['obis_codes']),
            'energy_measurements_found': len(results['energy_values']),
            'dlms_structures_found': len(results['dlms_structures']),
            'ascii_strings_found': len(results['ascii_strings']),
            'is_encrypted': results['encryption_info']['is_encrypted'],
            'analysis_confidence': self._calculate_confidence(results)
        }
        
        return results

    def analyze_blocks(self, blocks_data: List[Dict]) -> Dict:
        """Analyze all extracted blocks for OBIS codes and energy data"""
        results = {
            'total_blocks': len(blocks_data),
            'analyzed_blocks': [],
            'found_obis_codes': [],
            'energy_measurements': [],
            'potential_values': [],
            'dlms_structures': [],
            'summary': {}
        }
        
        for block in blocks_data:
            print(f"\n=== Analyzing Block {block} ===")
            print(f"Type: {block['type']}, Size: {block['total_size']} bytes")
            
            # Convert hex back to bytes for analysis
            raw_data = bytes.fromhex(block['raw_data'])
            
            block_analysis = {
                'block_id': block['block_id'],
                'type': block['type'],
                'size': block['total_size'],
                'obis_codes': self._find_obis_codes(raw_data),
                'dlms_structures': self._analyze_dlms_structure(raw_data),
                'energy_values': self._extract_energy_values(raw_data),
                'timestamps': self._find_timestamps(raw_data),
                'ascii_strings': self._find_ascii_strings(raw_data),
                'numeric_patterns': self._analyze_numeric_patterns(raw_data),
                'hex_analysis': self._analyze_hex_patterns(raw_data)
            }
            
            results['analyzed_blocks'].append(block_analysis)
            
            # Collect findings
            if block_analysis['obis_codes']:
                results['found_obis_codes'].extend(block_analysis['obis_codes'])
            
            if block_analysis['energy_values']:
                results['energy_measurements'].extend(block_analysis['energy_values'])
        
        # Generate summary
        results['summary'] = self._generate_summary(results)
        
        return results
    
    def _find_obis_codes(self, data: bytes) -> List[Dict]:
        """Look for OBIS code patterns in various encodings"""
        obis_found = []
        
        # Method 1: ASCII text search
        try:
            text = data.decode('ascii', errors='ignore')
            
            # Standard OBIS pattern: A-B:C.D.E(*F)
            patterns = [
                r'(\d+-\d+:\d+\.\d+\.\d+(?:\*\d+)?)',  # Standard format
                r'(\d+\.\d+\.\d+\.\d+\.\d+)',          # Dot-separated
                r'(\d{1,2}-\d{1,2}:\d{1,2}\.\d{1,2}\.\d{1,2})', # Strict format
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    obis_info = {
                        'code': match,
                        'description': self.known_obis_codes.get(match, 'Unknown OBIS code'),
                        'encoding': 'ascii',
                        'position': text.find(match)
                    }
                    obis_found.append(obis_info)
                    print(f"  Found OBIS (ASCII): {match} - {obis_info['description']}")
        
        except:
            pass
        
        # Method 2: Binary encoded OBIS (common in DLMS)
        obis_binary = self._find_binary_obis(data)
        obis_found.extend(obis_binary)
        
        return obis_found
    
    def _find_binary_obis(self, data: bytes) -> List[Dict]:
        """Look for binary-encoded OBIS codes in DLMS format"""
        obis_found = []
        
        # DLMS often encodes OBIS as 6 bytes: A.B.C.D.E.F
        for i in range(len(data) - 5):
            # Check for typical OBIS patterns
            if data[i] in [0, 1] and data[i+1] == 0:  # Medium 0 or 1, Channel 0
                a, b, c, d, e, f = data[i:i+6]
                
                # Skip all-zero patterns (padding) and improve validation
                if all(x == 0 for x in [a, b, c, d, e, f]):
                    continue
                
                # Validate ranges with more realistic constraints
                if (a <= 8 and b <= 64 and c <= 128 and d <= 255 and e <= 255 and f <= 255 and
                    not (c == 0 and d == 0 and e == 0)):  # Skip trivial patterns
                    
                    obis_code = f"{a}-{b}:{c}.{d}.{e}"
                    if f != 255 and f != 0:  # 255 or 0 often means "not used"
                        obis_code += f"*{f}"
                    
                    # Only add if it's a known OBIS code or has realistic values
                    if (obis_code in self.known_obis_codes or 
                        c in [1, 2, 3, 4, 14, 31, 32, 51, 52, 71, 72, 96]):  # Common OBIS C values
                        
                        obis_info = {
                            'code': obis_code,
                            'description': self.known_obis_codes.get(obis_code, 'Unknown OBIS code'),
                            'encoding': 'binary',
                            'position': i,
                            'raw_bytes': data[i:i+6].hex()
                        }
                        obis_found.append(obis_info)
                        print(f"  Found OBIS (Binary): {obis_code} at pos {i} - {obis_info['description']}")
        
        return obis_found
    
    def _analyze_dlms_structure(self, data: bytes) -> List[Dict]:
        """Analyze for DLMS/COSEM data structures (TLV encoding)"""
        structures = []
        
        i = 0
        while i < len(data) - 1:
            # Look for DLMS data type tags
            tag = data[i]
            
            # Common DLMS data types
            dlms_types = {
                0x00: 'null-data',
                0x01: 'boolean',
                0x02: 'bit-string', 
                0x03: 'double-long',
                0x04: 'double-long-unsigned',
                0x05: 'floating-point',
                0x06: 'octet-string',
                0x09: 'visible-string',
                0x0A: 'utf8-string',
                0x0C: 'date-time',
                0x0F: 'long',
                0x10: 'unsigned',
                0x11: 'long-unsigned',
                0x12: 'compact-array',
                0x13: 'array',
                0x14: 'structure',
                0x15: 'enum',
            }
            
            if tag in dlms_types:
                length = 0
                value_start = i + 1
                
                # Parse length encoding
                if i + 1 < len(data):
                    length_byte = data[i + 1]
                    if length_byte < 0x80:  # Short form
                        length = length_byte
                        value_start = i + 2
                    elif length_byte == 0x81 and i + 2 < len(data):  # Long form, 1 byte
                        length = data[i + 2]
                        value_start = i + 3
                    elif length_byte == 0x82 and i + 3 < len(data):  # Long form, 2 bytes
                        length = (data[i + 2] << 8) | data[i + 3]
                        value_start = i + 4
                
                if length > 0 and value_start + length <= len(data):
                    value_data = data[value_start:value_start + length]
                    
                    structure = {
                        'type': dlms_types[tag],
                        'tag': f"0x{tag:02X}",
                        'position': i,
                        'length': length,
                        'raw_value': value_data.hex(),
                        'parsed_value': self._parse_dlms_value(tag, value_data)
                    }
                    structures.append(structure)
                    print(f"  Found DLMS structure: {dlms_types[tag]} at pos {i}, length {length}")
                    
                    i = value_start + length
                else:
                    i += 1
            else:
                i += 1
        
        return structures
    
    def _parse_dlms_value(self, tag: int, data: bytes) -> str:
        """Enhanced DLMS value parser using the type mapping"""
        if tag in self.dlms_data_types:
            parser = self.dlms_data_types[tag]['parser']
            return parser(data)
        
        return data.hex()
    
    def _parse_dlms_datetime_extended(self, data: bytes) -> str:
        """
        Parse DLMS date-time format according to IEC 62056-5-3
        OctetString[12] format for date/time (0-0:1.0.0)
        """
        if len(data) < 12:
            return f"Invalid DateTime length: {len(data)}, expected 12"
        
        try:
            # DLMS DateTime structure (12 bytes):
            # Bytes 0-1: Year (big endian)
            # Byte 2: Month (1-12)
            # Byte 3: Day of Month (1-31)
            # Byte 4: Day of Week (1=Monday, 7=Sunday, 0xFF=not specified)
            # Byte 5: Hour (0-23)
            # Byte 6: Minute (0-59)
            # Byte 7: Second (0-59)
            # Byte 8: Hundredths of second (0-99)
            # Bytes 9-10: Deviation (timezone offset in minutes, big endian, signed)
            # Byte 11: Clock status
            
            year = struct.unpack('>H', data[0:2])[0]
            month = data[2]
            day = data[3]
            day_of_week = data[4]
            hour = data[5]
            minute = data[6]
            second = data[7]
            hundredths = data[8]
            deviation = struct.unpack('>h', data[9:11])[0]  # signed 16-bit
            clock_status = data[11]
            
            # Validate date/time values
            if not (2000 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31 and
                    0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59):
                return f"Invalid DateTime values: {data.hex()}"
            
            # Format the datetime string
            dt_str = f"{year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}"
            
            if hundredths != 0xFF:  # 0xFF means not specified
                dt_str += f".{hundredths:02d}"
            
            # Add timezone info if specified
            if deviation != 0x8000:  # 0x8000 means not specified
                sign = '+' if deviation >= 0 else '-'
                tz_hours = abs(deviation) // 60
                tz_minutes = abs(deviation) % 60
                dt_str += f" {sign}{tz_hours:02d}:{tz_minutes:02d}"
            
            # Add day of week if specified
            day_names = ["", "Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
            if 1 <= day_of_week <= 7:
                dt_str += f" ({day_names[day_of_week]})"
            
            # Add clock status info
            status_info = []
            if clock_status & 0x01:
                status_info.append("invalid")
            if clock_status & 0x02:
                status_info.append("doubtful")
            if clock_status & 0x04:
                status_info.append("different_base")
            if clock_status & 0x80:
                status_info.append("dst")
            
            if status_info:
                dt_str += f" [Status: {', '.join(status_info)}]"
                
            return dt_str
            
        except Exception as e:
            return f"DateTime parse error: {e}, raw: {data.hex()}"
    
    def _extract_energy_values(self, data: bytes) -> List[Dict]:
        """Extract potential energy measurement values"""
        values = []
        
        # Look for floating-point values in typical energy ranges
        for i in range(len(data) - 3):
            try:
                # Try as 32-bit float (big endian - common in DLMS)
                value = struct.unpack('>f', data[i:i+4])[0]
                if self._is_plausible_energy_value(value):
                    values.append({
                        'position': i,
                        'value': round(value, 3),
                        'type': 'float32_be',
                        'unit_guess': self._guess_unit(value),
                        'raw_hex': data[i:i+4].hex()
                    })
                
                # Try as 32-bit float (little endian)
                value = struct.unpack('<f', data[i:i+4])[0]
                if self._is_plausible_energy_value(value):
                    values.append({
                        'position': i,
                        'value': round(value, 3),
                        'type': 'float32_le', 
                        'unit_guess': self._guess_unit(value),
                        'raw_hex': data[i:i+4].hex()
                    })
                    
            except:
                pass
            
            # Try as integers
            try:
                # 32-bit unsigned (big endian)
                value = struct.unpack('>I', data[i:i+4])[0]
                if self._is_plausible_energy_value(value):
                    values.append({
                        'position': i,
                        'value': value,
                        'type': 'uint32_be',
                        'unit_guess': self._guess_unit(value),
                        'raw_hex': data[i:i+4].hex()
                    })
            except:
                pass
        
        return values[:20]  # Limit results
    
    def _is_plausible_energy_value(self, value: float) -> bool:
        """Check if a value could be an energy measurement"""
        if value != value:  # NaN check
            return False
        
        # Reasonable ranges for energy values
        abs_val = abs(value)
        return (
            (0.001 <= abs_val <= 999999) or  # kWh, Wh ranges
            (100 <= abs_val <= 400) or      # Voltage ranges
            (0.1 <= abs_val <= 1000) or     # Current ranges
            (45 <= abs_val <= 65)           # Frequency range
        )
    
    def _guess_unit(self, value: float) -> str:
        """Guess the unit based on value magnitude"""
        abs_val = abs(value)
        
        if 200 <= abs_val <= 250:
            return "V (Voltage)"
        elif 45 <= abs_val <= 65:
            return "Hz (Frequency)"
        elif 0.1 <= abs_val <= 100:
            return "A (Current)"
        elif 0.001 <= abs_val <= 10000:
            return "kWh (Energy)"
        elif 100 <= abs_val <= 100000:
            return "W (Power)"
        else:
            return "Unknown"
    
    def _find_timestamps(self, data: bytes) -> List[str]:
        """Look for timestamp patterns"""
        timestamps = []
        
        # Look for UNIX timestamp patterns
        for i in range(len(data) - 3):
            try:
                timestamp = struct.unpack('>I', data[i:i+4])[0]
                # Check if it's a reasonable timestamp (2020-2030)
                if 1577836800 <= timestamp <= 1893456000:  # 2020-2030 range
                    dt = datetime.fromtimestamp(timestamp)
                    timestamps.append(f"Timestamp at {i}: {dt}")
            except:
                pass
        
        return timestamps
    
    def _find_ascii_strings(self, data: bytes) -> List[str]:
        """Find readable ASCII strings in the data"""
        strings = []
        current_string = ""
        start_pos = 0
        
        for i, byte in enumerate(data):
            if 32 <= byte <= 126:  # Printable ASCII
                if not current_string:
                    start_pos = i
                current_string += chr(byte)
            else:
                if len(current_string) >= 4:  # Minimum string length
                    strings.append(f"String at {start_pos}: '{current_string}'")
                current_string = ""
        
        if len(current_string) >= 4:
            strings.append(f"String at {start_pos}: '{current_string}'")
        
        return strings
    
    def _analyze_numeric_patterns(self, data: bytes) -> List[str]:
        """Analyze for numeric patterns that might be energy values"""
        patterns = []
        
        # Look for BCD (Binary Coded Decimal) encoding
        for i in range(len(data) - 3):
            # BCD check: each nibble should be 0-9
            if all((data[j] & 0xF0) >> 4 <= 9 and (data[j] & 0x0F) <= 9 for j in range(i, min(i+4, len(data)))):
                bcd_value = ""
                for j in range(i, min(i+4, len(data))):
                    bcd_value += f"{(data[j] & 0xF0) >> 4}{data[j] & 0x0F}"
                if bcd_value.isdigit() and int(bcd_value) > 0:
                    patterns.append(f"BCD at {i}: {bcd_value}")
        
        return patterns[:10]  # Limit results
    
    def _analyze_hex_patterns(self, data: bytes) -> Dict:
        """Analyze hex patterns for known smart meter signatures"""
        analysis = {
            'repeating_sequences': [],
            'potential_serials': [],
            'checksums': []
        }
        
        # Look for repeating byte sequences
        hex_str = data.hex()
        for length in [4, 6, 8]:  # Check for 2, 3, 4 byte patterns
            for i in range(0, len(hex_str) - length * 2, 2):
                pattern = hex_str[i:i + length * 2]
                count = hex_str.count(pattern)
                if count > 1:
                    analysis['repeating_sequences'].append(f"Pattern '{pattern}' repeats {count} times")
        
        return analysis

    # Additional parser methods for DLMS data types
    def _parse_null(self, data: bytes) -> str:
        return "null"

    def _parse_boolean(self, data: bytes) -> str:
        return 'True' if data[0] else 'False' if len(data) > 0 else 'Invalid'

    def _parse_bit_string(self, data: bytes) -> str:
        return f"BitString: {data.hex()}"

    def _parse_double_long(self, data: bytes) -> str:
        """Parse signed 32-bit integer"""
        if len(data) < 4:
            return f"Invalid Int32 length: {len(data)}"
        try:
            value = struct.unpack('>i', data[:4])[0]
            return str(value)
        except:
            return f"Int32 parse error: {data.hex()}"

    def _parse_double_long_unsigned(self, data: bytes) -> str:
        """Parse Unsigned32 values (for power measurements like 1.7.0, 2.7.0)"""
        if len(data) < 4:
            return f"Invalid Unsigned32 length: {len(data)}"
        
        try:
            value = struct.unpack('>I', data[:4])[0]  # Big endian unsigned 32-bit
            return str(value)
        except Exception as e:
            return f"Unsigned32 parse error: {e}"

    def _parse_floating_point(self, data: bytes) -> str:
        if len(data) < 4:
            return f"Invalid Float length: {len(data)}"
        try:
            value = struct.unpack('>f', data[:4])[0]
            return f"{value:.6g}"
        except:
            return f"Float parse error: {data.hex()}"

    def _parse_octet_string(self, data: bytes) -> str:
        """Parse octet string - could be datetime or other binary data"""
        if len(data) == 12:
            # Try parsing as DLMS datetime first
            return self._parse_dlms_datetime_extended(data)
        
        # For other octet strings, try to decode as text or return hex
        try:
            decoded = data.decode('utf-8', errors='ignore')
            if decoded.isprintable():
                return f"'{decoded}'"
        except:
            pass
        
        return data.hex()

    def _parse_visible_string(self, data: bytes) -> str:
        try:
            return f"'{data.decode('ascii', errors='ignore')}'"
        except:
            return data.hex()

    def _parse_utf8_string(self, data: bytes) -> str:
        try:
            return f"'{data.decode('utf-8', errors='ignore')}'"
        except:
            return data.hex()

    def _parse_long(self, data: bytes) -> str:
        if len(data) < 2:
            return f"Invalid Int16 length: {len(data)}"
        try:
            value = struct.unpack('>h', data[:2])[0]
            return str(value)
        except:
            return f"Int16 parse error: {data.hex()}"

    def _parse_unsigned(self, data: bytes) -> str:
        if len(data) < 1:
            return "Invalid Uint8 length"
        return str(data[0])

    def _parse_long_unsigned(self, data: bytes) -> str:
        if len(data) < 2:
            return f"Invalid Uint16 length: {len(data)}"
        try:
            value = struct.unpack('>H', data[:2])[0]
            return str(value)
        except:
            return f"Uint16 parse error: {data.hex()}"

    def _parse_compact_array(self, data: bytes) -> str:
        return f"CompactArray: {data.hex()}"

    def _parse_array(self, data: bytes) -> str:
        return f"Array: {data.hex()}"

    def _parse_structure(self, data: bytes) -> str:
        return f"Structure: {data.hex()}"

    def _parse_enum(self, data: bytes) -> str:
        if len(data) > 0:
            return f"Enum: {data[0]}"
        return "Invalid Enum"

    def analyze_dlms_customer_interface(self, raw_data: bytes) -> Dict:
        """
        Analyze raw data from customer interface according to DLMS/COSEM spec
        Focus on OctetString[12] for datetime and Unsigned32 for power values
        """
        results = {
            'datetime_entries': [],
            'power_measurements': [],
            'obis_mappings': [],
            'dlms_structures': []
        }
        
        # Look for DLMS structures with focus on customer interface data
        structures = self._analyze_dlms_structure(raw_data)
        
        for struct in structures:
            if struct['type'] == 'date-time':
                results['datetime_entries'].append({
                    'position': struct['position'],
                    'parsed_value': struct['parsed_value'],
                    'likely_obis': '0-0:1.0.0'
                })
            
            elif struct['type'] == 'double-long-unsigned':
                # These are likely power measurements (1.7.0, 2.7.0, etc.)
                results['power_measurements'].append({
                    'position': struct['position'],
                    'value': struct['parsed_value'],
                    'unit': 'W or var',
                    'possible_obis': ['1-0:1.7.0', '1-0:2.7.0', '1-0:3.7.0', '1-0:4.7.0']
                })
        
        return results
    
    def _analyze_encryption_status(self, data: bytes) -> Dict:
        """Analyze if the block appears to be encrypted"""
        encryption_info = {
            'is_encrypted': False,
            'encryption_indicators': [],
            'dlms_aes_gcm': False,
            'randomness_score': 0.0
        }
        
        if len(data) == 0:
            return encryption_info
        
        # Check for DLMS AES-GCM encryption (MSB = 0x95)
        if data[0] == 0x95:
            encryption_info['is_encrypted'] = True
            encryption_info['dlms_aes_gcm'] = True
            encryption_info['encryption_indicators'].append("DLMS AES-GCM pattern (MSB=0x95)")
        
        # Calculate entropy/randomness
        byte_counts = [0] * 256
        for byte in data:
            byte_counts[byte] += 1
        
        # Calculate Shannon entropy
        import math
        total_bytes = len(data)
        entropy = 0.0
        for count in byte_counts:
            if count > 0:
                probability = count / total_bytes
                entropy -= probability * math.log2(probability)
        
        encryption_info['randomness_score'] = entropy / 8.0  # Normalize to 0-1
        
        # High entropy suggests encryption
        if encryption_info['randomness_score'] > 0.85:
            encryption_info['is_encrypted'] = True
            encryption_info['encryption_indicators'].append(f"High entropy: {encryption_info['randomness_score']:.3f}")
        
        # Check for low ASCII content (encrypted data has little readable text)
        ascii_count = sum(1 for b in data if 32 <= b <= 126)
        ascii_ratio = ascii_count / len(data)
        
        if ascii_ratio < 0.1:  # Less than 10% printable ASCII
            encryption_info['encryption_indicators'].append(f"Low ASCII content: {ascii_ratio:.1%}")
            if ascii_ratio < 0.05:
                encryption_info['is_encrypted'] = True
        
        return encryption_info

    def _calculate_confidence(self, results: Dict) -> str:
        """Calculate confidence level of the analysis"""
        confidence_score = 0
        max_score = 10
        
        # Points for finding structured data
        if results['obis_codes']:
            confidence_score += 3
        if results['dlms_structures']:
            confidence_score += 2
        if results['energy_values']:
            confidence_score += 2
        if results['timestamps']:
            confidence_score += 1
        if results['ascii_strings']:
            confidence_score += 1
        
        # Bonus for encryption detection
        if results['encryption_info']['is_encrypted']:
            confidence_score += 1
        
        confidence_ratio = confidence_score / max_score
        
        if confidence_ratio >= 0.8:
            return "High"
        elif confidence_ratio >= 0.5:
            return "Medium"
        elif confidence_ratio >= 0.2:
            return "Low"
        else:
            return "Very Low"

    def _generate_summary(self, results: Dict) -> Dict:
        """Generate a summary of all findings"""
        summary = {
            'obis_codes_found': len(results['found_obis_codes']),
            'energy_measurements_found': len(results['energy_measurements']),
            'unique_obis_codes': list(set(code['code'] for code in results['found_obis_codes'])),
            'value_ranges': {},
            'recommended_next_steps': []
        }
        
        # Analyze value ranges
        if results['energy_measurements']:
            values = [m['value'] for m in results['energy_measurements']]
            summary['value_ranges'] = {
                'min': min(values),
                'max': max(values),
                'count': len(values)
            }
        
        # Recommendations
        if summary['obis_codes_found'] > 0:
            summary['recommended_next_steps'].append("OBIS codes found - implement DLMS client")
        if summary['energy_measurements_found'] > 0:
            summary['recommended_next_steps'].append("Energy values detected - validate against meter display")
        if summary['obis_codes_found'] == 0:
            summary['recommended_next_steps'].append("No standard OBIS codes found - may need proprietary decoding")
        
        return summary
    
    def analyze_encrypted_frame(self, frame_hex: str, decryption_key: str = None) -> Dict:
        """
        Analyze an encrypted DLMS frame and provide decryption guidance
        
        Args:
            frame_hex: Hex string of the encrypted frame
            decryption_key: Optional AES key in hex format
            
        Returns:
            Dict with frame analysis and decryption information
        """
        frame_bytes = bytes.fromhex(frame_hex)
        
        if len(frame_bytes) < 26:  # Minimum: 1 byte security + 8 system title + 4 frame counter + 12 auth tag
            return {"error": "Frame too short for encrypted DLMS"}
        
        security_control = frame_bytes[0]
        system_title = frame_bytes[1:9]
        frame_counter = frame_bytes[9:13]
        auth_tag = frame_bytes[-12:]
        encrypted_payload = frame_bytes[13:-12]
        
        analysis = {
            "frame_info": {
                "total_size": len(frame_bytes),
                "security_control": f"0x{security_control:02x}",
                "system_title": system_title.hex(),
                "frame_counter": frame_counter.hex(),
                "encrypted_payload_size": len(encrypted_payload),
                "authentication_tag": auth_tag.hex(),
                "is_aes_gcm_encrypted": security_control == 0x95
            },
            "decryption_info": {
                "algorithm": "AES-GCM" if security_control == 0x95 else "Unknown",
                "key_needed": True,
                "iv_construction": "system_title + frame_counter",
                "aad_construction": "security_control + system_title + frame_counter",
                "provided_key": decryption_key[:8] + "..." if decryption_key else None
            },
            "next_steps": []
        }
        
        if security_control == 0x95:
            # Construct IV and AAD as per DLMS specification
            iv = system_title + frame_counter  # 12 bytes total
            aad = bytes([security_control]) + system_title + frame_counter  # 13 bytes total
            
            analysis["decryption_info"].update({
                "initialization_vector": iv.hex(),
                "additional_authenticated_data": aad.hex(),
                "iv_size": len(iv),
                "aad_size": len(aad)
            })
            
            analysis["next_steps"] = [
                "1. Obtain the correct AES-128 key from your energy provider",
                "2. Use AES-GCM decryption with:",
                f"   - Key: [your 32-character hex key]",
                f"   - IV: {iv.hex()}",
                f"   - AAD: {aad.hex()}",
                f"   - Ciphertext: {encrypted_payload.hex()[:64]}...",
                f"   - Auth Tag: {auth_tag.hex()}",
                "3. After decryption, re-run DLMS structure analysis",
                "4. Parse OBIS codes for energy measurements"
            ]
            
            # If a key is provided, show how to use it (but don't actually decrypt)
            if decryption_key:
                analysis["decryption_ready"] = True
                analysis["next_steps"].insert(0, "✅ Decryption key provided - ready to decrypt!")
            else:
                analysis["decryption_ready"] = False
                analysis["next_steps"].insert(0, "❌ No decryption key provided")
        
        else:
            analysis["next_steps"] = [
                f"Unknown security control: 0x{security_control:02x}",
                "This may not be a standard DLMS AES-GCM encrypted frame"
            ]
        
        return analysis
    
    def decrypt_dlms_frame(self, frame_hex: str, key_hex: str) -> Dict:
        """
        Attempt to decrypt a DLMS AES-GCM frame (requires pycryptodome)
        
        Args:
            frame_hex: Hex string of encrypted frame
            key_hex: AES key in hex format
            
        Returns:
            Dict with decryption result and analysis
        """
        try:
            from Crypto.Cipher import AES
        except ImportError:
            return {
                "error": "pycryptodome not installed",
                "solution": "Install with: pip install pycryptodome",
                "manual_decryption": self.analyze_encrypted_frame(frame_hex, key_hex)
            }
        
        try:
            frame_bytes = bytes.fromhex(frame_hex)
            key_bytes = bytes.fromhex(key_hex)
            
            if len(key_bytes) != 16:
                return {"error": f"Invalid key length: {len(key_bytes)} bytes (expected 16)"}
            
            # Extract frame components
            security_control = frame_bytes[0]
            system_title = frame_bytes[1:9]
            frame_counter = frame_bytes[9:13]
            encrypted_payload = frame_bytes[13:-12]
            auth_tag = frame_bytes[-12:]
            
            # Construct IV and AAD
            iv = system_title + frame_counter
            aad = bytes([security_control]) + system_title + frame_counter
            
            # Decrypt
            cipher = AES.new(key_bytes, AES.MODE_GCM, nonce=iv)
            cipher.update(aad)
            decrypted_payload = cipher.decrypt_and_verify(encrypted_payload, auth_tag)
            
            # Analyze decrypted payload
            decrypted_analysis = self.analyze_block(decrypted_payload)
            
            return {
                "success": True,
                "decrypted_payload": decrypted_payload.hex(),
                "decrypted_size": len(decrypted_payload),
                "dlms_analysis": decrypted_analysis
            }
            
        except Exception as e:
            return {
                "error": f"Decryption failed: {str(e)}",
                "possible_causes": [
                    "Incorrect decryption key",
                    "Corrupted frame data",
                    "Wrong frame format",
                    "Authentication tag verification failed"
                ]
            }
