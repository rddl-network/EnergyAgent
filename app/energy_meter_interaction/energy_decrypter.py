from decimal import Decimal
from datetime import datetime

from Crypto.Cipher import AES

from app.dependencies import config, logger
from binascii import unhexlify
from gurux_dlms.GXDLMSTranslator import GXDLMSTranslator
import xml.etree.ElementTree as ET

from submoudles.submodules.app_mypower_modul.schemas import MetricCreate

# CRC-STUFF BEGIN
CRC_INIT = 0xFFFF
POLYNOMIAL = 0x1021


def byte_mirror(c):
    c = (c & 0xF0) >> 4 | (c & 0x0F) << 4
    c = (c & 0xCC) >> 2 | (c & 0x33) << 2
    c = (c & 0xAA) >> 1 | (c & 0x55) << 1
    return c


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


def verify_crc16(input, skip=0, last=2, cut=0):
    lenn = len(input)
    data = input[skip : lenn - last - cut]
    goal = input[lenn - last - cut : lenn - cut]
    if last == 0:
        return hex(calc_crc16(data))
    elif last == 2:
        return calc_crc16(data) == goal[0] * 256 + goal[1]
    return False


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


def parse_root_items(root) -> list:
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


def decrypt_evn_data(data: str):
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

    apdu = evn_decrypt(frame, system_title, frame_counter)
    print("apdu: ", apdu)
    if apdu[0:4] != "0f80":
        raise ValueError("wrong apdu start")

    root = ET.fromstring(GXDLMSTranslator().pduToXml(apdu))
    return parse_root_items(root)


def evn_decrypt(frame, system_title, frame_counter):
    frame = unhexlify(frame)
    encryption_key = unhexlify(config.evn_key)
    init_vector = unhexlify(system_title + frame_counter)
    cipher = AES.new(encryption_key, AES.MODE_GCM, nonce=init_vector)
    return cipher.decrypt(frame).hex()


def decrypt_aes_gcm_landis_and_gyr(data_hex, encryption_key=None, authentication_key=None):
    if len(data_hex) != 282:
        raise ValueError(
            f"Wrong input encrypted data should have 282 characters. Please check your device, data_hex {data_hex}"
        )

    cipher_text_str = data_hex[38:276]
    apdu = decrypt_gcm(authentication_key, cipher_text_str, encryption_key)
    root = ET.fromstring(GXDLMSTranslator().pduToXml(apdu))
    return parse_root_items(root)


def decrypt_sagemcom(data_hex, encryption_key=None, authentication_key=None):
    apdu = decrypt_gcm(authentication_key, data_hex, encryption_key)
    obis_dict = parse_dsmr_frame(apdu)

    data_list = [
        {"key": "WirkenergieP", "value": int(obis_dict["1-0:1.8.0"])},
        {"key": "WirkenergieN", "value": int(obis_dict["1-0:2.8.0"])},
    ]

    return data_list


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


def convert_to_kwh(value) -> float:
    return value / 1000


def transform_to_metrics(data_list, public_key) -> MetricCreate:
    now = datetime.now()
    metric_data = {
        "public_key": public_key,
        "time_stamp": now.utcnow(),
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

    return MetricCreate(**metric_data)
