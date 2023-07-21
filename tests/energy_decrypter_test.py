from app.energy_meter_interaction.energy_decrypter import decrypt_evn_data, transform_to_metrics, parse_root_items
from gurux_dlms.GXDLMSTranslator import GXDLMSTranslator
import xml.etree.ElementTree as ET

from Crypto.Cipher import AES


def test_decode_packet_EVN():
    print("test_decode_packet_v2")
    data_hex_str = "68fafa6853ff000167db085341475905e990f381f8200001ca1d78efc0c0df5eb7fdf7ccef510234c8281c7dadfecd22d027a91352206a2f33ecb771c238240da352a398feda9ec144bcde15108e045470d549a35cad7fe716e1fdcfbbd75bae402019d69e4cdc58af40876b1a3d9428a2388ab63471c35c245784ebff041af5d55791f954ada371815940927e49a8208bfa1098a0203c2fe35808db07b9c01d366b4c7cc302d7e8eea2ecf5a97a6a3c5e67ed44c59e2eb6e04d82e5e35ae9c2237cf03119d40b48b132df77cac7b614fe30655838e76b9a28dbb6294eb8e100eafd98ca7e4a9ca77ee0dbc5d8511709a028d57f1010b28ae92461ab618022166814146853ff110167e5a52b128178e1fd01a2d75b60beab0716"
    dec = decrypt_evn_data(data_hex_str)
    metric = transform_to_metrics(dec, "test")
    # show_data(dec) if (dec) else "CRC error"
    print(dec)
    assert dec != None


def test_decode_packet_LG():
    print("test_decode_packet_v2")
    data_hex_str = "7ea08bceff0313eee1e6e700e0400001000077db084c475a67737c7ee0820103300001669a7654da96c65e4930a6f3719e304f4bebf8d6600508958b6cd46b16e8310b6868527c30ec8197ff9f80e7107ad7db303072428e0c0f59fcbe2dfb07c6edc5e1c4eb0a40dbf3e73ed8a52e65f3799f63a2341b345a940224ecda0ceb215a6c7bac19020d4468ce2a7e"
    encryption_key = bytes.fromhex('7340BC1501143C498CD677811D771921')
    authentication_key = bytes.fromhex('DDFC444A5C78B74D46C158DBE711D37A')
    apdu = decrypt_aes_gcm(data_hex_str, encryption_key, authentication_key)
    root = ET.fromstring(GXDLMSTranslator().pduToXml(apdu))
    dec = parse_root_items(root)
    metric = transform_to_metrics(dec, "test")
    # show_data(dec) if (dec) else "CRC error"
    print(dec)
    assert dec != None



