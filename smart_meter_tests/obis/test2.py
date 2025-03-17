from binascii import unhexlify

# Raw data as a hex string
raw_data_hex = "0f00bec1100c07e70b1e040f2b2dff80000002120112020412002809060008190900ff0f02120000020412002809060008190900ff0f01120000020412000109060000600100ff0f02120000020412000809060000010000ff0f02120000020412000309060100010700ff0f02120000020412000309060100020700ff0f02120000020412000309060100010800ff0f02120000020412000309060100020800ff0f02120000020412000309060100030700ff0f02120000020412000309060100040700ff0f02120000020412000309060100030800ff0f02120000020412000309060100040800ff0f021200000204120003090601001f0700ff0f02120000020412000309060100330700ff0f02120000020412000309060100470700ff0f02120000020412000309060100200700ff0f02120000020412000309060100340700ff0f02120000020412000309060100480700ff0f0212000009060008190900ff09083536383135393330090c07e70b1e040f2b2dff80000106000000050600000000060000c2a50600000000060000000006000000000600001259060000e39b1200041200001200001200e9120000120000"

# Convert hex string to bytes
data = unhexlify(raw_data_hex)

# OBIS code mappings (simplified)
obis_mapping = {
    "1.0.0.1.0.255": "Clock",
    "1.0.0.1.8.255": "Time integral",
    "0.0.96.1.0.255": "Device ID",
    "0.0.1.0.0.255": "Meter serial number",
    "1.0.1.7.0.255": "Active power + (W)",
    "1.0.2.7.0.255": "Active power - (W)",
    "1.0.1.8.0.255": "Active energy + (Wh) total",
    "1.0.2.8.0.255": "Active energy - (Wh) total",
    "1.0.3.7.0.255": "Reactive power + (var)",
    "1.0.4.7.0.255": "Reactive power - (var)",
    "1.0.3.8.0.255": "Reactive energy + (varh)",
    "1.0.4.8.0.255": "Reactive energy - (varh)",
    "1.0.31.7.0.255": "Current L1 (A)",
    "1.0.51.7.0.255": "Current L2 (A)",
    "1.0.71.7.0.255": "Current L3 (A)",
    "1.0.32.7.0.255": "Voltage L1 (V)",
    "1.0.52.7.0.255": "Voltage L2 (V)",
    "1.0.72.7.0.255": "Voltage L3 (V)",
}


# Function to parse OBIS code from bytes
def parse_obis_code(data, index):
    if data[index] != 0x09:  # Expecting octet-string tag
        return None, index
    length = data[index + 1]
    obis_bytes = data[index + 2 : index + 2 + length]
    obis = ".".join(map(str, obis_bytes))
    return obis, index + 2 + length


# Function to parse value (assuming unsigned32 for energy)
def parse_value(data, index):
    if data[index] != 0x06:  # Expecting unsigned32 tag
        return None, index
    value = int.from_bytes(data[index + 1 : index + 5], byteorder="big")
    return value, index + 5


# Main decoding function
def decode_dlms_data(data):
    index = 0
    results = {}

    while index < len(data) - 1:
        # Look for OBIS code (tag 0x09)
        if data[index] == 0x09:
            obis, new_index = parse_obis_code(data, index)
            if obis:
                # Map OBIS to description
                description = obis_mapping.get(obis, "Unknown")

                # Look for value (tag 0x06 for unsigned32, 0x09 for string)
                index = new_index
                if index < len(data) and data[index] == 0x06:
                    value, index = parse_value(data, index)
                    results[obis] = {"description": description, "value": value}
                elif index < len(data) and data[index] == 0x09:  # String (e.g., serial number)
                    length = data[index + 1]
                    value = data[index + 2 : index + 2 + length].decode("ascii", errors="ignore")
                    index = index + 2 + length
                    results[obis] = {"description": description, "value": value}
                else:
                    index = new_index
            else:
                index += 1
        else:
            index += 1

    return results


# Decode the data
decoded_data = decode_dlms_data(data)

# Print results
for obis, info in decoded_data.items():
    print(f"OBIS: {obis}")
    print(f"Description: {info['description']}")
    print(f"Value: {info['value']}")
    print()

# Specifically extract active energy
active_energy_obis = "1.0.1.8.0.255"
if active_energy_obis in decoded_data:
    energy_value = decoded_data[active_energy_obis]["value"]
    print(f"Total Active Energy Imported: {energy_value} Wh ({energy_value / 1000} kWh)")
