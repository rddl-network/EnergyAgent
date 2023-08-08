from decimal import Decimal
from datetime import datetime

from app.dependencies import config
from app.energy_meter_interaction.energy_decrypter import (
    decrypt_evn_data,
    transform_to_metrics,
    decrypt_aes_gcm_landis_and_gyr,
)
from submoudles.submodules.app_mypower_modul.schemas import MetricCreate


def test_decode_packet_evn():
    print("test_decode_packet_v2")
    config.evn_key = "A89AE6C225E45130298B3CC3F4D23463"
    data_hex_str = "68fafa6853ff000167db085341475905e990f381f8200001ca1d78efc0c0df5eb7fdf7ccef510234c8281c7dadfecd22d027a91352206a2f33ecb771c238240da352a398feda9ec144bcde15108e045470d549a35cad7fe716e1fdcfbbd75bae402019d69e4cdc58af40876b1a3d9428a2388ab63471c35c245784ebff041af5d55791f954ada371815940927e49a8208bfa1098a0203c2fe35808db07b9c01d366b4c7cc302d7e8eea2ecf5a97a6a3c5e67ed44c59e2eb6e04d82e5e35ae9c2237cf03119d40b48b132df77cac7b614fe30655838e76b9a28dbb6294eb8e100eafd98ca7e4a9ca77ee0dbc5d8511709a028d57f1010b28ae92461ab618022166814146853ff110167e5a52b128178e1fd01a2d75b60beab0716"
    dec = decrypt_evn_data(data_hex_str)
    # show_data(dec) if (dec) else "CRC error"
    print(dec)
    assert dec == [
        {"key": "WirkenergieP", "value": 6842204},
        {"key": "WirkenergieN", "value": 6430217},
        {"key": "MomentanleistungP", "value": 0},
        {"key": "MomentanleistungN", "value": 2088},
        {"key": "SpannungL1", "value": 2373},
        {"key": "SpannungL2", "value": 2378},
        {"key": "SpannungL3", "value": 2392},
        {"key": "StromL1", "value": 320},
        {"key": "StromL2", "value": 273},
        {"key": "StromL3", "value": 292},
        {"key": "Leistungsfaktor", "value": 991},
    ]


def test_decode_packet_LG():
    print("test_decode_packet_v2")
    data_hex_str = "7ea08bceff0313eee1e6e700e0400001000077db084c475a67737c7ee082010330000879a66ad533b89c24bfe1680b0745ab2138b4098c33c9ba956639d0cbfce9a657a4076ad04ae0b190441d489b62452aef0c240229e8c0ff3c03e18ddabdc6cdffa94330ca9c16be8059aa17a9084b6bec007d2f675d720a65fd0a70f1eaf16122cddf80971057b4d8eb7e"
    encryption_key = bytes.fromhex("7340BC1501143C498CD677811D771921")
    authentication_key = bytes.fromhex("DDFC444A5C78B74D46C158DBE711D37A")
    dec = decrypt_aes_gcm_landis_and_gyr(data_hex_str, encryption_key, authentication_key)
    # show_data(dec) if (dec) else "CRC error"
    print(dec)
    assert dec == [{"key": "WirkenergieP", "value": 8684853}, {"key": "MomentanleistungP", "value": 1565}]


def test_decode_packet_LG_exception():
    print("test_decode_packet_v2")
    data_hex_str = (
        "7ea030ceff031386f8e0c0000300001f8b379c3b5a58d7c6c8517275468aae0f5b5f5916445e6fc45ca0fed1618ad77f2a7e"
    )
    encryption_key = bytes.fromhex("7340BC1501143C498CD677811D771921")
    authentication_key = bytes.fromhex("DDFC444A5C78B74D46C158DBE711D37A")
    try:
        decrypt_aes_gcm_landis_and_gyr(data_hex_str, encryption_key, authentication_key)
    except Exception as e:
        assert e.args[0] == "The input string must have exactly 282 characters."
