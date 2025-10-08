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
    """
    
    def __init__(self):
        DECRYPTION_KEY = "A78F4624621DE5EB8A96DA779E08109C"
        self.decryptor = AESDecryptor(DECRYPTION_KEY) 
        self.known_obis_codes = {
            # Common electricity meter OBIS codes
            '1-0:1.8.0': 'Total Active Energy Import (kWh)',
            '1-0:1.8.1': 'Active Energy Import Tariff 1 (kWh)', 
            '1-0:1.8.2': 'Active Energy Import Tariff 2 (kWh)',
            '1-0:2.8.0': 'Total Active Energy Export (kWh)',
            '1-0:2.8.1': 'Active Energy Export Tariff 1 (kWh)',
            '1-0:2.8.2': 'Active Energy Export Tariff 2 (kWh)',
            '1-0:1.7.0': 'Instantaneous Active Power Import (W)',
            '1-0:2.7.0': 'Instantaneous Active Power Export (W)',
            '1-0:32.7.0': 'Instantaneous Voltage L1 (V)',
            '1-0:52.7.0': 'Instantaneous Voltage L2 (V)', 
            '1-0:72.7.0': 'Instantaneous Voltage L3 (V)',
            '1-0:31.7.0': 'Instantaneous Current L1 (A)',
            '1-0:51.7.0': 'Instantaneous Current L2 (A)',
            '1-0:71.7.0': 'Instantaneous Current L3 (A)',
            '1-0:14.7.0': 'Supply Frequency (Hz)',
            '1-0:81.7.1': 'Phase Angle L1-L2 (°)',
            '1-0:81.7.2': 'Phase Angle L1-L3 (°)',
            '1-0:81.7.4': 'Phase Angle L2-L3 (°)',
            '0-0:96.1.1': 'Meter Serial Number',
            '0-0:1.0.0': 'Date and Time',
            '1-0:0.2.0': 'Version Information',
            '0-0:96.14.0': 'Current Tariff',
            '1-0:1.6.0': 'Maximum Demand Import (W)',
            '1-0:2.6.0': 'Maximum Demand Export (W)',
        }
    
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
            print(f"\n=== Analyzing Block {block['block_id']} ===")
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
                
                # Validate ranges
                if (a <= 8 and b <= 64 and c <= 128 and d <= 255 and e <= 255 and f <= 255):
                    obis_code = f"{a}-{b}:{c}.{d}.{e}"
                    if f != 255:  # 255 often means "not used"
                        obis_code += f"*{f}"
                    
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
        """Parse DLMS value based on its type"""
        try:
            if tag == 0x01:  # boolean
                return 'True' if data[0] else 'False'
            elif tag == 0x0F:  # long (16-bit signed)
                if len(data) >= 2:
                    return str(struct.unpack('>h', data[:2])[0])
            elif tag == 0x10:  # unsigned (8-bit)
                return str(data[0])
            elif tag == 0x11:  # long-unsigned (16-bit unsigned)
                if len(data) >= 2:
                    return str(struct.unpack('>H', data[:2])[0])
            elif tag == 0x03:  # double-long (32-bit signed)
                if len(data) >= 4:
                    return str(struct.unpack('>i', data[:4])[0])
            elif tag == 0x04:  # double-long-unsigned (32-bit unsigned)
                if len(data) >= 4:
                    return str(struct.unpack('>I', data[:4])[0])
            elif tag == 0x05:  # floating-point
                if len(data) >= 4:
                    return f"{struct.unpack('>f', data[:4])[0]:.3f}"
            elif tag in [0x06, 0x09, 0x0A]:  # strings
                try:
                    return data.decode('utf-8', errors='ignore')
                except:
                    return data.hex()
            elif tag == 0x0C:  # date-time
                return self._parse_dlms_datetime(data)
        except:
            pass
        
        return data.hex()
    
    def _parse_dlms_datetime(self, data: bytes) -> str:
        """Parse DLMS date-time format"""
        if len(data) >= 12:
            try:
                year = struct.unpack('>H', data[0:2])[0]
                month = data[2]
                day = data[3]
                hour = data[5]
                minute = data[6]
                second = data[7]
                
                if 2000 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31:
                    return f"{year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}"
            except:
                pass
        
        return f"DateTime: {data.hex()}"
    
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
