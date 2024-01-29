"""
To decode smart meter data retrieved from the infrared customer interface provided by Wiener Netze.
Tested with Iskra AM550 (But should work for all smart meters provided by Wiener Netze)
"""

import binascii
from decimal import Decimal
from datetime import datetime
from typing import Union

from Crypto.Cipher import AES

from app.dependencies import config, logger
from app.energy_meter_interaction.energy_meter_data import MeterData
from binascii import unhexlify
from gurux_dlms.GXDLMSTranslator import GXDLMSTranslator
import xml.etree.ElementTree as ET

from submoudles.submodules.app_mypower_modul.schemas import MetricCreate

if config.selection == "Matthias":
    key_smart_meter = "62DC84B413AF3E16AA271CE9ED04AC74"  # Matthias
    # Matthias home unsliced
    payload = "7ea067cf022313fbf1e6e700db0849534b6974a8d8994f2000909dd750e337f09d460befa73f43e61e5cbdd88f7f1e4a91ff2fcb38b8fd4e38bd0d431f6f42892c24545b49389a5b4a3e976c924ae466d4e25abfd26a1573b95c0a4a4bce9a273f1233765c38da4c76779c3821aa9243d34209e33e1bf67a9eee813f0773308227d34232eb863933b3cf9c8aa58966ffeb0a2ade0add0b1b35147be913ddd3e22f1045a33d8bd72345ec83f784e3086b0810b7b344cba4a6a0f9aa37d5f5c1e092b1ef198ae08dae"  # noqa
    # public key in byte (remove first byte 04 as it just a notation)
    public_key_byte_string = "041D1F36BB2C5362B8BE3AD472084AC3623F4B8F4890BAFECAD0EC7CFF53AA45412C1A67F29121028AA841E344E7A77D124993EDEF3A84C9A252F7C5E7A6A10B94"  # noqa
    # slice the data from the smart meter (missing byte.
    # that's the reason why not payload[:(-128-64)]) only 104bytes are sent instead of the original 105bytes.
    data = payload[:210]
elif config.selection == 0:  # rpi-zero0 - SIEMENS
    key_smart_meter = "4F9278B252D90B3F742F5711232AD27A"  # SMS1030788000020
    # rpi-zero0
    payload = "7ea07bcf000200231362b1e6e700db08534d5367753ec614612000124ef6b993602ba8f1abb3c5d7208604f922f1240720e5d60b3846a3c9bcce2fbed4c9f87da01a2fd084fb0d1846b4b299326db5524b4d0fc60adbaf8af60fbbcca86fe755b6223c787d23d0466f93d4c5ee906692cc2fb77e61f60f5a2ad44f777eb88ad7d2ed2cc4a09072c98423ab030fbbf70d9b7881da9fba8ca3e30875d016675837c40aa962359593401300deae193655e3bb6fa46ab2d54adabaabb939e783f95489289c8b00b38dad308a41327320650ec9cb5de0296861ca05ae84bc2f"  # noqa
    public_key_byte_string = "04cf711f82714be5ec70f17f35c77a57a735f30d48914d7a479b77427922a9eacb17215d6a895bbbbe09ee109d83b079a39ae0b285e8a23b5487c5b944bc19cc7f"  # noqa
    data = payload[: (-128 - 64)]
elif config.selection == 2:  # rpi-zero2 - ISKRA
    key_smart_meter = "927CE4ECA62FE23E19406C5EE452285E"  # ISK1050771045183
    # rpi-zero2
    payload = "7ea067cf022313fbf1e6e700db0849534b69743c103f4f200010d9e208f5c0c61a10c2359a014dfa00024e52839d213a16b086e297ad13f7db4574d0d4d3aff9bada8f10f3bb33a39ac2fc5fb447342ff4d6a9e9361ecbd84c9b6f76f5ece94425b2917a660b0af27e41fd07ddf650be01e89564063f58a8800c401c894d1bcfcfa5bac541fc79c302ab606511dee0eca4fc15d72b24314c9265bc4c9295f2e619419f9c082e025d52cac968fec6aff04774018dda4e614d71284fe3ffe439c2eaf550e38cb621e0c1"  # noqa
    public_key_byte_string = "044d7bd8e2c066adeaf3bc41446e5908e876d2ac8b694c8d482e15a2760d5ef194a198e5d062fffaea8a5a407da40ad81423ab4c97cb1fb0b2f55c41f68e91f2ce"  # noqa
    data = payload[: (-128 - 64)]
elif config.selection == 3:  # rpi-zero3 - LANDIS+GYR
    key_smart_meter = "1F51C774301C3E940065D9200DDDA5B4"  # LGZ1030740710430
    payload = "7ea067ceff031338bde6e700db084c475a67726d311e4f200021ed98f64d452292bf5966b5af37da66b67a4a49f9186244b1aa594e80248e44b9ce93cf04c54d209880fffa632a60c474591763cc1d31803012531dc84f1b43e0e4d076b57fb8f4cdef1f86f36d497e4d97b172f3ce2c63306f1ca35c9e60ed4f00ef841e98b2012446a165a0aa8a1eb324786889cd85a62bb09615da71f3f13d8b81b22232aea015b3d0adea0465aa2e32492b8197ddbc84f7d79b0ce78c65650825218cd15f70b60942e3e7837b68"  # noqa
    public_key_byte_string = "04f559f84b07d58575761e0fc3bdbcf8fc46d17c2f237e0cffd998062ff64b57fbe597ef9945478dfab072d398cfea2ff92ce0c85b957c89e3888b71e86612d187"  # noqa
    data = payload[: (-128 - 64)]
elif config.selection == "mock":  # simcard - LANDIS+GYR
    """Does not contain a signature"""
    config.verify_signature = False
    key_smart_meter = "62DC84B413AF3E16AA271CE9ED04AC74"  # LGZ1030740710430
    payload = "7EA067CF022313FBF1E6E700DB0849534B6974A8D8994F2000909DD750E337F09D460BEFA73F43E61E5CBDD88F7F1E4A91FF2FC83EBBFC4439A40D431F6F42892E83255B49389A5B4A3E976C924AE466D4E25ABFD26A1573B95C0A4A4BCE9A273F1233765C38E45B7E"  # noqa
    public_key_byte_string = "04FFAABBCCDDEE918FB2352F4E83FFA3C3DFF00A0B75697C57ED39C85B95070046E20EADF6C1B0C1E7B6AFD98B736A598FFB565B1E2AD49060D2D65C89C8B4C154"  # noqa
    data = payload


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


# CRC-STUFF DONE


# DECODE-STUFF BEGIN
def decode_packet(
    input,
) -> bytes:  # expects input to be bytearray.fromhex(hexstring), full packet  "7ea067..7e" # noqa
    if verify_crc16(input, 1, 2, 1):
        nonce = bytes(input[14:22] + input[24:28])  # systemTitle+invocation counter
        cipher = AES.new(binascii.unhexlify(key_smart_meter), AES.MODE_CTR, nonce=nonce, initial_value=2)
        return cipher.decrypt(input[28:-3])
    else:
        return b""


# DECODE-STUFF DONE


def bytes_to_int(bytes):
    result = 0
    for b in bytes:
        result = result * 256 + b
    return result


def show_data(s):
    print("SSS")
    print(s)
    if config.device == "WN":
        a = bytes_to_int(s[35:39]) / 1000.000  # +A Wh
        b = bytes_to_int(s[40:44]) / 1000.000  # -A Wh
        c = bytes_to_int(s[45:49]) / 1000.000  # +R varh
        d = bytes_to_int(s[50:54]) / 1000.000  # -R varh
        e = bytes_to_int(s[55:59])  # +P W
        f = bytes_to_int(s[60:64])  # -P W
        g = bytes_to_int(s[65:69])  # +Q var
        h = bytes_to_int(s[70:74])  # -Q var
        yyyy = bytes_to_int(s[22:24])
        mm = bytes_to_int(s[24:25])
        dd = bytes_to_int(s[25:26])
        hh = bytes_to_int(s[27:28])
        mi = bytes_to_int(s[28:29])
        ss = bytes_to_int(s[29:30])
        print(datetime(year=yyyy, month=mm, day=dd, hour=hh, minute=mi, second=ss))
        print(
            "Output: %10.3fkWh, %10.3fkWh, %10.3fkvarh, %10.3fkvarh, %5dW, %5dW, %5dvar, %5dvar at %02d.%02d.%04d-%02d:%02d:%02d"
            % (a, b, c, d, e, f, g, h, dd, mm, yyyy, hh, mi, ss)
        )
    elif config.device == "KN":
        a = bytes_to_int(s[57:61]) / 1000.000  # +A Wh
        b = bytes_to_int(s[62:66]) / 1000.000  # -A Wh
        c = bytes_to_int(s[67:71]) / 1000.000  # +R varh
        d = bytes_to_int(s[72:76]) / 1000.000  # -R varh
        e = bytes_to_int(s[77:81])  # +P W
        f = bytes_to_int(s[82:86])  # -P W
        yyyy = bytes_to_int(s[51:53])
        mm = bytes_to_int(s[53:54])
        dd = bytes_to_int(s[54:55])
        hh = bytes_to_int(s[45:46])
        mi = bytes_to_int(s[46:47])
        ss = bytes_to_int(s[47:48])
        print(
            "Output: %10.3fkWh, %10.3fkWh, %10.3fkvarh, %10.3fkvarh, %5dW, %5dW at %02d.%02d.%04d-%02d:%02d:%02d"
            % (a, b, c, d, e, f, dd, mm, yyyy, hh, mi, ss)
        )
    else:
        print("Device type not recognized")


def extract_data(s: bytes) -> Union[MeterData, None]:
    print("encrypted data: ", s)
    if config.device == "WN":
        energy_consumed = bytes_to_int(s[35:39]) / 1000.000  # +A Wh
        energy_delivered = bytes_to_int(s[40:44]) / 1000.000  # -A Wh
        positive_reactive_energy = bytes_to_int(s[45:49]) / 1000.000  # +R varh
        negative_reactive_energy = bytes_to_int(s[50:54]) / 1000.000  # -R varh
        active_power_consumption = bytes_to_int(s[55:59])  # +P W
        active_power_delivery = bytes_to_int(s[60:64])  # -P W
        positive_reactive_power = bytes_to_int(s[65:69])  # +Q var
        negative_reactive_power = bytes_to_int(s[70:74])  # -Q var
        yyyy = bytes_to_int(s[22:24])
        mm = bytes_to_int(s[24:25])
        dd = bytes_to_int(s[25:26])
        hh = bytes_to_int(s[27:28])
        mi = bytes_to_int(s[28:29])
        ss = bytes_to_int(s[29:30])
        timestamp = datetime(year=yyyy, month=mm, day=dd, hour=hh, minute=mi, second=ss)

        return MeterData(
            device_type=config.device,
            energy_consumed=energy_consumed,
            energy_delivered=energy_delivered,
            positive_reactive_energy=positive_reactive_energy,
            negative_reactive_energy=negative_reactive_energy,
            active_power_consumption=active_power_consumption,
            active_power_delivery=active_power_delivery,
            positive_reactive_power=positive_reactive_power,
            negative_reactive_power=negative_reactive_power,
            timestamp=timestamp,
        )
    elif config.device == "KN":
        energy_consumed = bytes_to_int(s[57:61]) / 1000.000  # +A Wh
        energy_delivered = bytes_to_int(s[62:66]) / 1000.000  # -A Wh
        positive_reactive_energy = bytes_to_int(s[67:71]) / 1000.000  # +R varh
        negative_reactive_energy = bytes_to_int(s[72:76]) / 1000.000  # -R varh
        active_power_consumption = bytes_to_int(s[77:81])  # +P W
        active_power_delivery = bytes_to_int(s[82:86])  # -P W
        yyyy = bytes_to_int(s[51:53])
        mm = bytes_to_int(s[53:54])
        dd = bytes_to_int(s[54:55])
        hh = bytes_to_int(s[45:46])
        mi = bytes_to_int(s[46:47])
        ss = bytes_to_int(s[47:48])
        timestamp = datetime(year=yyyy, month=mm, day=dd, hour=hh, minute=mi, second=ss)

        return MeterData(
            device_type=config.device,
            energy_consumed=energy_consumed,
            energy_delivered=energy_delivered,
            positive_reactive_energy=positive_reactive_energy,
            negative_reactive_energy=negative_reactive_energy,
            active_power_consumption=active_power_consumption,
            active_power_delivery=active_power_delivery,
            positive_reactive_power=None,
            negative_reactive_power=None,
            timestamp=timestamp,
        )

    print("Device type not recognized")
    return None


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


def evn_decrypt(frame, system_title, frame_counter):
    frame = unhexlify(frame)
    encryption_key = unhexlify(config.evn_key)
    init_vector = unhexlify(system_title + frame_counter)
    cipher = AES.new(encryption_key, AES.MODE_GCM, nonce=init_vector)
    return cipher.decrypt(frame).hex()


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
    logger.info(f"hex_frame: {hex_frame}")
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
