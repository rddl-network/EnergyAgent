import binascii

from Crypto.Cipher import AES
from gurux_dlms.GXDLMSTranslator import GXDLMSTranslator
import xml.etree.ElementTree as ET

from app.energy_meter_interaction.energy_decrypter import decode_packet, show_data, extract_data


def test_decode_packet():
    data_hex_str = "7ea067cf022313fbf1e6e700db0849534b6974a8d8994f2000909dd750e337f09d460befa73f43e61e5cbdd88f7f1e4a91ff2fc936b8fd423c930d431f6f4288104a9c5b49389a5b4a3e976c924ae466d4e25abfd26a1573b95c0a4a4bce9a273f1233765c38c9367e"
    dec = decode_packet(bytearray.fromhex(data_hex_str))
    show_data(dec) if (dec) else "CRC error"
    test = extract_data(dec)
    print("test: ", test)
    assert dec != None


def test_decode_packet_v2():
    print("test_decode_packet_v2")
    data_hex_str = "68fafa6853ff000167db085341475905e990f381f820000e87e1eb04bbd2809986cc5c584ca34a4deb34a6d96d29ea846915402f814d11a6b1b2debd07e97699bde5c249c4e3aa32f0c335272d717d04d37a670c032151739bf312d2a8ec071691c8de2fb2aee07c5e212eb9127053c67e498c5bb65769fcf6c9d07ee84e3652d1773d9140bfafeef5097f2b220c170f8687f8e820872f0fb2b7f831bfeb08d85024e8ce3fabbcde470f45fe66534942619d7d7cd06dc865acdb3c31f065424b6a21996c232dff5d9c06e0c0bf834de7bd8efd46dee89acaa1e113c5f52dcab0623f3ee98f846efadbf499c035025073da7b5d8adf186023b301194728b4c5166814146853ff110167c106694937be602126a2ef4d5cb703d416"
    data_bytearray = bytearray.fromhex(data_hex_str)
    # dec = decode_packet(data_bytearray)
    dec = decrypt_data(data_hex_str)
    show_data(dec) if (dec) else "CRC error"
    test = extract_data(dec)
    print("test: ", test)
    assert dec != None


def evn_decrypt(frame, key, systemTitel, frameCounter):
    frame = binascii.unhexlify(frame)
    encryption_key = binascii.unhexlify(key)
    init_vector = binascii.unhexlify(systemTitel + frameCounter)
    cipher = AES.new(encryption_key, AES.MODE_GCM, nonce=init_vector)
    return cipher.decrypt(frame).hex()


def decrypt_data(data: str):
    mbusstart = data[0:8]
    frameLen = int("0x" + mbusstart[2:4], 16)
    systemTitel = data[22:38]
    frameCounter = data[44:52]
    frame = data[52 : 12 + frameLen * 2]
    if mbusstart[0:2] == "68" and mbusstart[2:4] == mbusstart[4:6] and mbusstart[6:8] == "68":
        print("Daten ok")
    else:
        print("wrong M-Bus Start, restarting")

    octet_string_values = {}
    octet_string_values["0100010800FF"] = "WirkenergieP"
    octet_string_values["0100020800FF"] = "WirkenergieN"
    octet_string_values["0100010700FF"] = "MomentanleistungP"
    octet_string_values["0100020700FF"] = "MomentanleistungN"
    octet_string_values["0100200700FF"] = "SpannungL1"
    octet_string_values["0100340700FF"] = "SpannungL2"
    octet_string_values["0100480700FF"] = "SpannungL3"
    octet_string_values["01001F0700FF"] = "StromL1"
    octet_string_values["0100330700FF"] = "StromL2"
    octet_string_values["0100470700FF"] = "StromL3"
    octet_string_values["01000D0700FF"] = "Leistungsfaktor"

    apdu = evn_decrypt(frame, "36C66639E48A8CA4D6BC8B282A793BBB", systemTitel, frameCounter)
    print("apdu: ", apdu)
    if apdu[0:4] != "0f80":
        raise Exception("wrong apdu start")
    tr = GXDLMSTranslator()
    xml = tr.pduToXml(
        apdu,
    )
    # print("xml: ",xml)
    root = ET.fromstring(xml)
    found_lines = []
    momentan = []

    items = list(root.iter())
    for i, child in enumerate(items):
        if child.tag == "OctetString" and "Value" in child.attrib:
            value = child.attrib["Value"]
            if value in octet_string_values.keys():
                if "Value" in items[i + 1].attrib:
                    if value in ["0100010700FF", "0100020700FF"]:
                        # special handling for momentanleistung
                        momentan.append(int(items[i + 1].attrib["Value"], 16))
                    found_lines.append(
                        {"key": octet_string_values[value], "value": int(items[i + 1].attrib["Value"], 16)}
                    )

    #        print(found_lines)
    return apdu
