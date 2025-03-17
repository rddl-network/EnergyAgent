from dataclasses import dataclass
from typing import Dict, Optional, List, Any
from datetime import datetime
import struct


@dataclass
class DSMRMeasurement:
    identifier: str
    value: float
    unit: str
    raw_bytes: bytes


class DSMRParser:
    def __init__(self):
        # DSMR object definitions
        self.DSMR_OBJECTS = {
            "1-0:1.8.1": ("Electricity delivered to client (tariff 1)", "kWh"),
            "1-0:1.8.2": ("Electricity delivered to client (tariff 2)", "kWh"),
            "1-0:2.8.1": ("Electricity delivered by client (tariff 1)", "kWh"),
            "1-0:2.8.2": ("Electricity delivered by client (tariff 2)", "kWh"),
            "1-0:1.7.0": ("Actual electricity power delivered", "kW"),
            "1-0:2.7.0": ("Actual electricity power received", "kW"),
            "1-0:32.7.0": ("Voltage L1", "V"),
            "1-0:52.7.0": ("Voltage L2", "V"),
            "1-0:72.7.0": ("Voltage L3", "V"),
            "1-0:31.7.0": ("Current L1", "A"),
            "1-0:51.7.0": ("Current L2", "A"),
            "1-0:71.7.0": ("Current L3", "A"),
            "0-0:96.14.0": ("Tariff indicator", None),
            "1-0:99.97.0": ("Power failure event log", None),
        }

        # Typical value ranges for validation
        self.VALUE_RANGES = {
            "VOLTAGE": (180, 260),  # 180V to 260V
            "CURRENT": (0, 100),  # 0 to 100A
            "POWER": (-10000, 10000),  # -10kW to 10kW
        }

    def parse_frame(self, hex_frame: str) -> Dict[str, Any]:
        """Parse DSMR frame from hex string."""
        frame_bytes = bytes.fromhex(hex_frame)

        # Extract frame components (similar to DLMS but interpret differently)
        header = frame_bytes[:2]
        system_title = frame_bytes[2:10]
        frame_counter = frame_bytes[10:14]
        payload = frame_bytes[14:-12]
        auth_tag = frame_bytes[-12:]

        # Parse the payload as DSMR data
        measurements = self._parse_dsmr_payload(payload)

        return {
            "header": {
                "security_control": header[1],
                "system_title": system_title.hex(),
                "frame_counter": frame_counter.hex(),
                "auth_tag": auth_tag.hex(),
            },
            "measurements": measurements,
            "raw": {"payload": payload.hex()},
        }

    def _parse_dsmr_payload(self, payload: bytes) -> Dict[str, DSMRMeasurement]:
        """Parse DSMR-encoded payload."""
        measurements = {}
        pos = 0

        # Check for DSMR data indicator
        if payload and payload[0] == 0x8D:
            pos = 1  # Skip indicator

        # Look for DSMR patterns in the data
        while pos < len(payload) - 4:
            # Try to identify DSMR blocks
            measurement = self._identify_dsmr_block(payload[pos:])
            if measurement:
                measurements[measurement.identifier] = measurement
                pos += len(measurement.raw_bytes)
            else:
                pos += 1

        return measurements

    def _identify_dsmr_block(self, data: bytes) -> Optional[DSMRMeasurement]:
        """Identify and parse DSMR data block."""
        if len(data) < 4:
            return None

        # Look for common DSMR patterns
        patterns = [
            self._try_parse_power_block,
            self._try_parse_voltage_block,
            self._try_parse_current_block,
            self._try_parse_energy_block,
        ]

        for parser in patterns:
            result = parser(data)
            if result:
                return result

        return None

    def _try_parse_power_block(self, data: bytes) -> Optional[DSMRMeasurement]:
        """Try to parse as power measurement."""
        # Power values are typically 32-bit values with scaling
        if len(data) >= 5 and data[0] in [0x02, 0x06]:
            try:
                value = int.from_bytes(data[1:5], byteorder="big")
                if self._is_valid_value(value * 0.001, "POWER"):  # Convert to kW
                    return DSMRMeasurement(
                        identifier="1-0:1.7.0",  # Active power
                        value=value * 0.001,  # Convert to kW
                        unit="kW",
                        raw_bytes=data[:5],
                    )
            except Exception:
                pass
        return None

    def _try_parse_voltage_block(self, data: bytes) -> Optional[DSMRMeasurement]:
        """Try to parse as voltage measurement."""
        # Voltage values are typically 16-bit values
        if len(data) >= 3 and data[0] == 0x12:
            try:
                value = int.from_bytes(data[1:3], byteorder="big")
                if self._is_valid_value(value * 0.1, "VOLTAGE"):  # Convert to V
                    return DSMRMeasurement(
                        identifier="1-0:32.7.0",  # Voltage L1
                        value=value * 0.1,  # Convert to V
                        unit="V",
                        raw_bytes=data[:3],
                    )
            except Exception:
                pass
        return None

    def _try_parse_current_block(self, data: bytes) -> Optional[DSMRMeasurement]:
        """Try to parse as current measurement."""
        # Current values are typically 32-bit values with scaling
        if len(data) >= 5 and data[0] == 0x06:
            try:
                value = int.from_bytes(data[1:5], byteorder="big")
                if self._is_valid_value(value * 0.001, "CURRENT"):  # Convert to A
                    return DSMRMeasurement(
                        identifier="1-0:31.7.0",  # Current L1
                        value=value * 0.001,  # Convert to A
                        unit="A",
                        raw_bytes=data[:5],
                    )
            except Exception:
                pass
        return None

    def _try_parse_energy_block(self, data: bytes) -> Optional[DSMRMeasurement]:
        """Try to parse as energy measurement."""
        # Energy values are typically 32-bit values with scaling
        if len(data) >= 5 and data[0] == 0x06:
            try:
                value = int.from_bytes(data[1:5], byteorder="big")
                # Energy values are typically in Wh, convert to kWh
                energy_value = value * 0.001
                return DSMRMeasurement(
                    identifier="1-0:1.8.1",  # Energy delivered tariff 1
                    value=energy_value,  # Convert to kWh
                    unit="kWh",
                    raw_bytes=data[:5],
                )
            except Exception:
                pass
        return None

    def _is_valid_value(self, value: float, measurement_type: str) -> bool:
        """Validate if value is within expected range."""
        if measurement_type in self.VALUE_RANGES:
            min_val, max_val = self.VALUE_RANGES[measurement_type]
            return min_val <= value <= max_val
        return True

    def print_parsed_data(self, parsed_data: Dict[str, Any]):
        """Print parsed data in a readable format."""
        print("Frame Header:")
        print(f"Security Control: 0x{parsed_data['header']['security_control']:02x}")
        print(f"System Title: {parsed_data['header']['system_title']}")
        print(f"Frame Counter: {parsed_data['header']['frame_counter']}")

        print("\nMeasurements:")
        for key, measurement in parsed_data["measurements"].items():
            print(f"\n{key}:")
            print(f"  Value: {measurement.value:.3f} {measurement.unit}")
            print(f"  Raw bytes: {measurement.raw_bytes.hex()}")
