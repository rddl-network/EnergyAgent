#!/usr/bin/env python3
"""
Specialized Parser for Landis+Gyr E450 Smart Meter Data

This script is tailored to the E450 model's data format, focusing on the 
structures and OBIS codes specific to this meter.
"""


def hex_to_bytes(hex_string):
    """Convert a hex string to a list of byte values"""
    return [int(hex_string[i : i + 2], 16) for i in range(0, len(hex_string), 2)]


def extract_obis_code(bytes_data, start_index):
    """Extract and format OBIS code from bytes list"""
    if start_index + 6 > len(bytes_data):
        return None

    return ".".join(str(b) for b in bytes_data[start_index : start_index + 6])


def find_e450_structures(bytes_data):
    """Find E450-specific data structures"""
    # E450 often uses structure 02 04 (structure with 4 elements)
    # followed by specific data types
    structures = []

    for i in range(len(bytes_data) - 10):
        # Look for structure with 4 elements pattern
        if bytes_data[i] == 0x02 and bytes_data[i + 1] == 0x04:
            # Check if it's followed by data type 0x12 (LongUnsigned)
            if i + 2 < len(bytes_data) and bytes_data[i + 2] == 0x12:
                structures.append(
                    {
                        "position": i,
                        "type": "Possible E450 data structure",
                        "data": bytes_data[i : i + 20],  # Capture reasonable chunk
                    }
                )

    return structures


def analyze_e450_frame(bytes_data):
    """Analyze the E450 frame structure specifically"""
    # E450 frames typically start with 0F 00 followed by manufacturer specific data
    if len(bytes_data) < 16:
        return "Frame too short for analysis"

    result = {}

    # Check standard frame header
    if bytes_data[0] == 0x0F and bytes_data[1] == 0x00:
        result["frame_valid"] = True
        result["manufacturer_id"] = f"0x{bytes_data[2]:02x}{bytes_data[3]:02x}"

        # E450 often stores a timestamp after the manufacturer ID
        # Format is typically YY MM DD WD HH MM SS (WD = weekday)
        if len(bytes_data) >= 10:
            try:
                weekday_names = ["", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                year = 2000 + bytes_data[4]
                month = bytes_data[5]
                day = bytes_data[6]
                weekday = weekday_names[bytes_data[7]] if 1 <= bytes_data[7] <= 7 else "Unknown"
                hour = bytes_data[8]
                minute = bytes_data[9]
                second = bytes_data[10] if len(bytes_data) > 10 else 0

                # Validate date (basic check)
                if 1 <= month <= 12 and 1 <= day <= 31 and 0 <= hour <= 23 and 0 <= minute <= 59:
                    result["timestamp"] = {
                        "raw": [
                            bytes_data[4],
                            bytes_data[5],
                            bytes_data[6],
                            bytes_data[7],
                            bytes_data[8],
                            bytes_data[9],
                            bytes_data[10] if len(bytes_data) > 10 else 0,
                        ],
                        "formatted": f"{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d} ({weekday})",
                    }
            except Exception as e:
                result["timestamp_error"] = str(e)
    else:
        result["frame_valid"] = False

    return result


def e450_obis_lookup(obis_code):
    """E450-specific OBIS code interpretations"""
    # E450 specific OBIS codes
    e450_obis = {
        "0.0.1.0.0.255": "Clock",
        "0.0.96.1.0.255": "Device ID Number",
        "0.0.96.1.1.255": "Manufacturing Number",
        "0.0.96.1.2.255": "Firmware Version",
        "0.0.96.240.7.255": "Manufacturer-specific",
        "0.0.97.97.0.255": "Error register",
        "0.8.25.9.0.255": "E450 frame marker",
        "1.0.1.7.0.255": "Active power + (W)",
        "1.0.2.7.0.255": "Active power - (W)",
        "1.0.1.8.0.255": "Active energy + (Wh) total",
        "1.0.1.8.1.255": "Active energy + (Wh) tariff 1",
        "1.0.1.8.2.255": "Active energy + (Wh) tariff 2",
        "1.0.2.8.0.255": "Active energy - (Wh) total",
        "1.0.2.8.1.255": "Active energy - (Wh) tariff 1",
        "1.0.2.8.2.255": "Active energy - (Wh) tariff 2",
        "0.0.96.240.12.255": "Disconnect/reconnect control state",
        "0.0.96.3.10.255": "Disconnect open error",
        "0.0.96.15.0.255": "Current billing period",
    }

    return e450_obis.get(obis_code, None)


def attempt_e450_data_extract(obis_code, data_bytes):
    """Specialized data extraction for E450 meter values"""
    result = {}

    # Energy registers (kWh, etc.)
    if obis_code in [
        "1.0.1.8.0.255",
        "1.0.1.8.1.255",
        "1.0.1.8.2.255",
        "1.0.2.8.0.255",
        "1.0.2.8.1.255",
        "1.0.2.8.2.255",
    ]:
        # Energy readings are often preceded by data type marker 06 (DoubleLongUnsigned)
        for i in range(min(5, len(data_bytes))):
            if data_bytes[i] == 0x06 and i + 5 <= len(data_bytes):
                # Extract 4-byte value
                value = (
                    (data_bytes[i + 1] << 24)
                    | (data_bytes[i + 2] << 16)
                    | (data_bytes[i + 3] << 8)
                    | data_bytes[i + 4]
                )
                # E450 often stores energy in Wh, convert to kWh
                result["value"] = value / 1000.0
                result["unit"] = "kWh"
                break

    # Power values (W)
    elif obis_code in ["1.0.1.7.0.255", "1.0.2.7.0.255"]:
        for i in range(min(5, len(data_bytes))):
            if data_bytes[i] == 0x06 and i + 5 <= len(data_bytes):
                value = (
                    (data_bytes[i + 1] << 24)
                    | (data_bytes[i + 2] << 16)
                    | (data_bytes[i + 3] << 8)
                    | data_bytes[i + 4]
                )
                result["value"] = value
                result["unit"] = "W"
                break

    # Clock/timestamp
    elif obis_code == "0.0.1.0.0.255":
        # Look for octet string marker (09) followed by length (0C = 12 for date-time)
        for i in range(min(5, len(data_bytes))):
            if (
                data_bytes[i] == 0x09
                and data_bytes[i + 1] in [0x0C, 0x08]
                and i + 2 + data_bytes[i + 1] <= len(data_bytes)
            ):
                time_bytes = data_bytes[i + 2 : i + 2 + data_bytes[i + 1]]
                if len(time_bytes) >= 7:
                    year = 2000 + time_bytes[0]
                    month = time_bytes[1]
                    day = time_bytes[2]
                    # Byte 3 is often weekday
                    hour = time_bytes[4]
                    minute = time_bytes[5]
                    second = time_bytes[6]
                    result["timestamp"] = f"{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}"
                break

    # Device ID
    elif obis_code == "0.0.96.1.0.255":
        # Device ID is often stored as octet string (09) or visible string (0A)
        for i in range(min(5, len(data_bytes))):
            if data_bytes[i] in [0x09, 0x0A] and i + 1 < len(data_bytes):
                str_len = data_bytes[i + 1]
                if i + 2 + str_len <= len(data_bytes):
                    # Try ASCII interpretation
                    ascii_str = "".join(chr(b) for b in data_bytes[i + 2 : i + 2 + str_len] if 32 <= b <= 126)
                    if len(ascii_str) > 2:
                        result["id_ascii"] = ascii_str

                    # Also provide hex representation
                    result["id_hex"] = "".join(f"{b:02x}" for b in data_bytes[i + 2 : i + 2 + str_len])
                break

    return result


def parse_e450_meter_data(hex_string):
    """Main function to parse Landis+Gyr E450 data"""
    bytes_data = hex_to_bytes(hex_string)
    results = {
        "data_length": len(bytes_data),
        "frame_info": analyze_e450_frame(bytes_data),
        "structures": [],
        "obis_values": {},
        "raw_analysis": {},
    }

    # Find OBIS codes (pattern 09 06 followed by 6 bytes)
    for i in range(len(bytes_data) - 8):
        if bytes_data[i] == 0x09 and bytes_data[i + 1] == 0x06:
            obis_start = i + 2
            obis_code = extract_obis_code(bytes_data, obis_start)

            if obis_code:
                # Validate code is in expected ranges
                parts = [int(p) for p in obis_code.split(".")]
                valid = (
                    0 <= parts[0] <= 10
                    and 0 <= parts[1] <= 64
                    and 0 <= parts[2] <= 99
                    and 0 <= parts[3] <= 255
                    and 0 <= parts[4] <= 255
                    and 0 <= parts[5] <= 255
                )

                if valid:
                    # Get interpretation
                    interpretation = e450_obis_lookup(obis_code)

                    # Extract following data for analysis
                    data_start = i + 8  # 2 bytes for pattern + 6 for OBIS
                    if data_start < len(bytes_data):
                        following_data = bytes_data[data_start : min(data_start + 32, len(bytes_data))]

                        # Try to extract value based on OBIS type
                        value_data = attempt_e450_data_extract(obis_code, following_data)

                        # Store in results
                        results["obis_values"][obis_code] = {
                            "position": i,
                            "interpretation": interpretation if interpretation else "Unknown",
                            "following_bytes": following_data,
                            "extracted_data": value_data,
                        }

    # Find E450 specific data structures
    e450_structures = find_e450_structures(bytes_data)
    results["structures"] = [{"position": s["position"], "type": s["type"]} for s in e450_structures]

    # Find potential energy consumption values
    # E450 often stores these with specific markers
    energy_markers = []
    for i in range(len(bytes_data) - 6):
        # Look for DoubleLongUnsigned (06) followed by 4 bytes
        if bytes_data[i] == 0x06 and i + 5 < len(bytes_data):
            value = (
                (bytes_data[i + 1] << 24) | (bytes_data[i + 2] << 16) | (bytes_data[i + 3] << 8) | bytes_data[i + 4]
            )
            # Filter for reasonable energy values (avoid false positives)
            if 0 <= value < 10000000:  # Up to 10,000 kWh is reasonable
                energy_markers.append(
                    {"position": i, "value": value / 1000.0, "raw_bytes": bytes_data[i : i + 5]}  # Convert Wh to kWh
                )

    results["potential_energy_values"] = energy_markers

    return results


# Example usage
if __name__ == "__main__":
    # The raw hexadecimal data from the E450 meter
    hex_data = "0f00b1ce270c07e70a0c040e0528ff80000002120112020412002809060008190900ff0f02120000020412002809060008190900ff0f01120000020412000109060000600100ff0f02120000020412000809060000010000ff0f02120000020412000309064c0b7ca80cbbadc4b1061f912b63ee54b092ba19f428024561235a514f6410e6500c47e4b477f93f4a32b3afaec87c3d5efb79aae0b7b3e125736f124eeb1d8a70eb10c3319916d247f783a1b7cd760399025e057ebd96caa6ac601b56ab15eaf55f560dd4ffa781d94e2d327c2e2682fbbb4bf3ee37e27b2da96be3038f6c1e4e601ca21e7762dfe8bfd845f3578faf98f1f5e669001d9ac77f329465146c55c842e0f06ed0c28614f55141d4f431991ea27622544865e9aaf28424ad506dd6757a538dc655b51d8b922f49b7303f5cc235bf01c06125f29921877a145975e25adf43823afc4daeba6db17518ed8a6d3aca1e07d85c5fbd7e777b9eaa49e7e7a2b6ab7c617f94bcba7d5971d4015eed62b3375eb04f5e7f1d95e7b5ca224a26ea3beb540c3d249928af4d3c0569c1d7498d905808e1fc6aeec8402b92c5d2cccabdc1c483ff5e87fb53109353a9995ea94eef"

    # Parse the data
    results = parse_e450_meter_data(hex_data)

    # Print results in a readable format
    import json

    print(json.dumps(results, indent=2))

    # Provide a summary of key findings
    print("\n=== E450 Smart Meter Data Summary ===")
    if "frame_info" in results and "timestamp" in results["frame_info"]:
        print(f"Timestamp: {results['frame_info']['timestamp']['formatted']}")

    print("\nOBIS Values Found:")
    for obis, data in results["obis_values"].items():
        print(f"- {obis}: {data['interpretation']}")
        if data["extracted_data"]:
            for key, value in data["extracted_data"].items():
                print(f"  {key}: {value}")

    print("\nPotential Energy Values:")
    for idx, marker in enumerate(results["potential_energy_values"]):
        print(f"- Value {idx+1}: {marker['value']} kWh (position {marker['position']})")

    print("\nNote: For complete decoding, refer to Landis+Gyr E450 documentation")
