import json
from decimal import Decimal
from datetime import datetime, timezone
from typing import Type, Any

from Crypto.Cipher import AES

from app.dependencies import trust_wallet_instance
from binascii import unhexlify
from gurux_dlms.GXDLMSTranslator import GXDLMSTranslator
import xml.etree.ElementTree as ET

from app.helpers.logs import log, logger
from app.helpers.models import LANDIS_GYR, SAGEMCOM, SmartMeterConfig

# CRC-STUFF BEGIN
CRC_INIT = 0xFFFF
POLYNOMIAL = 0x1021


@log
def byte_mirror(c):
    c = (c & 0xF0) >> 4 | (c & 0x0F) << 4
    c = (c & 0xCC) >> 2 | (c & 0x33) << 2
    c = (c & 0xAA) >> 1 | (c & 0x55) << 1
    return c


@log
def calc_crc16(data):
    crc = CRC_INIT
    for i in range(len(data)):
        c = byte_mirror(data[i]) << 8
        for _ in range(8):
            if (crc ^ c) & 0x8000:
                crc = (crc << 1) ^ POLYNOMIAL
            else:
                crc = crc << 1
            crc = crc % 65536
            c = (c << 1) % 65536
    crc = 0xFFFF - crc
    return 256 * byte_mirror(crc // 256) + byte_mirror(crc % 256)


@log
def verify_crc16(input, skip=0, last=2, cut=0):
    lenn = len(input)
    data = input[skip : lenn - last - cut]
    goal = input[lenn - last - cut : lenn - cut]
    if last == 0:
        return hex(calc_crc16(data))
    elif last == 2:
        return calc_crc16(data) == goal[0] * 256 + goal[1]
    return False


@log
def bytes_to_int(bytes):
    result = 0
    for b in bytes:
        result = result * 256 + b
    return result


OCTET_STRING_VALUES = {
    "0100010800FF": "WirkenergieP",
    "0100020800FF": "WirkenergieN",
    "0100010700FF": "MomentanleistungP",
    "0100020700FF": "MomentanleistungN",
    "0100200700FF": "SpannungL1",
    "0100340700FF": "SpannungL2",
    "0100480700FF": "SpannungL3",
    "01001F0700FF": "StromL1",
    "0100330700FF": "StromL2",
    "0100470700FF": "StromL3",
    "01000D0700FF": "Leistungsfaktor",
}

MBUS_START_SLICE = slice(0, 8)
FRAME_LEN_SLICE = slice(2, 4)
SYSTEM_TITLE_SLICE = slice(22, 38)
FRAME_COUNTER_SLICE = slice(44, 52)


@log
def parse_root_items(root) -> list:

    xml_string = ET.tostring(root, encoding="unicode")
    logger.debug(f"XML Content:\n{xml_string}")

    found_lines, momentan = [], []
    iterator = iter(root.iter())
    current_child, next_child = next(iterator), next(iterator, None)

    while next_child is not None:
        if current_child.tag == "OctetString" and "Value" in current_child.attrib:
            value = current_child.attrib["Value"]
            if value in OCTET_STRING_VALUES:
                next_val = int(next_child.attrib["Value"], 16)
                if value in {"0100010700FF", "0100020700FF"}:
                    momentan.append(next_val)
                found_lines.append({"key": OCTET_STRING_VALUES[value], "value": next_val})

        current_child, next_child = next_child, next(iterator, None)

    return found_lines


@log
def decrypt_device(data_hex, smart_meter_config: SmartMeterConfig):
    keys = trust_wallet_instance.get_planetmint_keys()
    planetmint_address = keys.planetmint_address
    if smart_meter_config.smart_meter_type == LANDIS_GYR:
        dec = decrypt_aes_gcm_landis_and_gyr(
            data_hex,
            bytes.fromhex(smart_meter_config.encryption_key),
            bytes.fromhex(smart_meter_config.authentication_key),
        )
        return transform_to_metrics(dec, planetmint_address)
    elif smart_meter_config.smart_meter_type == SAGEMCOM:
        dec = decrypt_sagemcom(
            data_hex,
            bytes.fromhex(smart_meter_config.encryption_key),
            bytes.fromhex(smart_meter_config.authentication_key),
        )
        return transform_to_metrics(dec, planetmint_address)
    elif smart_meter_config.smart_meter_type == "EVN":
        dec = decrypt_evn_data(data_hex, smart_meter_config.encryption_key)
        return transform_to_metrics(dec, planetmint_address)
    else:
        logger.error(f"Unknown device: {smart_meter_config.smart_meter_type}")


@log
def decrypt_evn_data(data: str, evn_key: str):
    mbus_start = data[MBUS_START_SLICE]
    frame_len = int(data[FRAME_LEN_SLICE], 16)
    system_title = data[SYSTEM_TITLE_SLICE]
    frame_counter = data[FRAME_COUNTER_SLICE]
    frame = data[52 : 12 + frame_len * 2]
    print(
        "Daten ok"
        if mbus_start == "686868" and mbus_start[2:4] == mbus_start[4:6]
        else "wrong M-Bus Start, restarting"
    )

    apdu = evn_decrypt(frame, system_title, frame_counter, evn_key)
    print("apdu: ", apdu)
    if apdu[0:4] != "0f80":
        raise ValueError("wrong apdu start")

    root = ET.fromstring(GXDLMSTranslator().pduToXml(apdu))
    return parse_root_items(root)


@log
def evn_decrypt(frame, system_title, frame_counter, evn_key):
    frame = unhexlify(frame)
    encryption_key = unhexlify(evn_key)
    init_vector = unhexlify(system_title + frame_counter)
    cipher = AES.new(encryption_key, AES.MODE_GCM, nonce=init_vector)
    return cipher.decrypt(frame).hex()


@log
def decrypt_aes_gcm_landis_and_gyr(data_hex, encryption_key=None, authentication_key=None):
    apdu = decrypt_gcm(authentication_key, data_hex, encryption_key)
    return unwrap_apdu(apdu)


def unwrap_apdu(apdu):
    gxdlm = GXDLMSTranslator().pduToXml(apdu)
    root = ET.fromstring(gxdlm)
    return parse_root_items(root)


def unwrap_gxdlm(apdu):
    parsed_data = apdu_to_json(apdu)
    return parsed_data


def parse_apdu(apdu_bytes):
    parsed_data = []
    index = 0

    while index < len(apdu_bytes):
        # Extract 6-byte hex string for OBIS code
        hex_string = apdu_bytes[index : index + 6].hex().upper()
        if hex_string in OCTET_STRING_VALUES:
            key = OCTET_STRING_VALUES[hex_string]
            index += 6

            # Read the next byte for the length of the value
            length = apdu_bytes[index]
            index += 1

            # Extract the value bytes based on the length
            value_bytes = apdu_bytes[index : index + length]

            # Convert the value bytes to an integer (interpreting as hex)
            # This is similar to int(next_child.attrib["Value"], 16) in the XML logic
            value = int.from_bytes(value_bytes, byteorder="big", signed=False)

            index += length

            # Add the parsed item to the list
            parsed_data.append({"key": key, "value": value})

        else:
            index += 1

    return parsed_data


def apdu_to_json(apdu_hex):
    """
    Converts an APDU (in hex string format) to a JSON representation.
    """
    # Convert APDU hex string to bytes
    apdu_bytes = bytes.fromhex(apdu_hex)

    # Parse the APDU
    parsed_apdu = parse_apdu(apdu_bytes)

    # Convert the parsed data to JSON
    apdu_json = json.dumps(parsed_apdu, indent=4)

    return apdu_json


@log
def decrypt_sagemcom(data_hex, encryption_key=None, authentication_key=None):
    apdu = decrypt_gcm(authentication_key, data_hex, encryption_key)
    obis_dict = parse_dsmr_frame(apdu)

    data_list = parse_obis(obis_dict)

    return data_list


def parse_obis(obis_dict: dict):
    return [
        # Energy readings
        {"key": "WirkenergieP", "value": parse_value(obis_dict.get("1-0:1.8.0"))},
        {"key": "WirkenergieN", "value": parse_value(obis_dict.get("1-0:2.8.0"))},
        {"key": "WirkenergieP_T1", "value": parse_value(obis_dict.get("1-0:1.8.1"))},
        {"key": "WirkenergieP_T2", "value": parse_value(obis_dict.get("1-0:1.8.2"))},
        {"key": "WirkenergieN_T1", "value": parse_value(obis_dict.get("1-0:2.8.1"))},
        {"key": "WirkenergieN_T2", "value": parse_value(obis_dict.get("1-0:2.8.2"))},
        {"key": "BlindEnergieP", "value": parse_value(obis_dict.get("1-0:3.8.0"))},
        {"key": "BlindEnergieN", "value": parse_value(obis_dict.get("1-0:4.8.0"))},
        # Power readings
        {"key": "WirkleistungP", "value": parse_value(obis_dict.get("1-0:1.7.0"))},
        {"key": "WirkleistungN", "value": parse_value(obis_dict.get("1-0:2.7.0"))},
        {"key": "BlindleistungP", "value": parse_value(obis_dict.get("1-0:3.7.0"))},
        {"key": "BlindleistungN", "value": parse_value(obis_dict.get("1-0:4.7.0"))},
        # Voltage and current
        {"key": "SpannungL1", "value": parse_value(obis_dict.get("1-0:32.7.0"))},
        {"key": "SpannungL2", "value": parse_value(obis_dict.get("1-0:52.7.0"))},
        {"key": "SpannungL3", "value": parse_value(obis_dict.get("1-0:72.7.0"))},
        {"key": "StromL1", "value": parse_value(obis_dict.get("1-0:31.7.0"))},
        {"key": "StromL2", "value": parse_value(obis_dict.get("1-0:51.7.0"))},
        {"key": "StromL3", "value": parse_value(obis_dict.get("1-0:71.7.0"))},
        # Frequency
        {"key": "Frequenz", "value": parse_value(obis_dict.get("1-0:14.7.0"))},
        # Power factor
        {"key": "Leistungsfaktor", "value": parse_value(obis_dict.get("1-0:13.7.0"), float)},
        # Meter information
        {"key": "Zaehlernummer", "value": obis_dict.get("0-0:96.1.0")},
        {"key": "Zaehlerstand", "value": parse_value(obis_dict.get("0-0:96.14.0"))},
        # Time and date
        {"key": "Zeitstempel", "value": obis_dict.get("0-0:1.0.0")},
    ]


def parse_value(value: Any, value_type: Type = int):
    if value is None:
        return ""
    if value == "":
        return ""
    try:
        return value_type(value)
    except ValueError:
        return f"ERROR: Could not convert '{value}' to {value_type.__name__}"


@log
def decrypt_gcm(authentication_key, cipher_text_str, encryption_key):
    cipher_text = bytes.fromhex(cipher_text_str)
    system_title = cipher_text[2 : 2 + 8]
    initialization_vector = system_title + cipher_text[14 : 14 + 4]
    additional_authenticated_data = cipher_text[13 : 13 + 1] + authentication_key
    cipher = AES.new(encryption_key, AES.MODE_GCM, nonce=initialization_vector)
    cipher.update(additional_authenticated_data)
    plaintext = cipher.decrypt(cipher_text[18 : len(cipher_text) - 12])
    apdu = plaintext.hex()
    return apdu


@log
def parse_dsmr_frame(hex_frame):
    # Decode the hexadecimal string into its string representation
    logger.debug(f"hex_frame: {hex_frame}")
    decoded_frame = bytes.fromhex(hex_frame).decode("utf-8")

    # Split the decoded frame into lines
    lines = decoded_frame.split("\r\n")

    # Dictionary to store parsed data
    data = {}

    for line in lines:
        # Split the line into OBIS code and value, if possible
        parts = line.split("(")

        if len(parts) > 1:
            obis_code = parts[0]

            # Strip any unwanted characters from the value
            value = parts[1].rstrip(")").split("*")[0]

            data[obis_code] = value

    return data


@log
def convert_to_kwh(value) -> float:
    return value / 1000


@log
def transform_to_metrics(data_list, public_key) -> dict:
    now = datetime.now(timezone.utc)
    metric_data = {
        "public_key": public_key,
        "time_stamp": now,
        "type": "absolute_energy",
        "unit": "kWh",
        "absolute_energy_in": 0,
        "absolute_energy_out": 0,
    }

    for data in data_list:
        value = Decimal(data.get("value"))
        if data.get("key") == "WirkenergieP":
            metric_data["absolute_energy_in"] = convert_to_kwh(value)
        elif data.get("key") == "WirkenergieN":
            metric_data["absolute_energy_out"] = convert_to_kwh(value)

    return metric_data
