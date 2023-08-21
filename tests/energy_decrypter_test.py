from app.dependencies import config
from app.energy_meter_interaction.energy_decrypter import (
    decrypt_evn_data,
    decrypt_aes_gcm_landis_and_gyr,
    decrypt_sagemcom,
)


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


# db085341473500046c9b8201f2300000807d2c13af3525b76a039334fe227934a2fb6b7bdb1795efa3dd6e54f93c4fbc41955dd2960911ad33656426f841b10df3201cf9024e0c4a87b3b716004e7697a2f3fd9076db4d62752595436892ff3724c95c93c12bf0ba3f2942470e371d9b539e676c191ef64265062a0f640f3396cbbec9660c36331029be39a82c06f1ea2e147cd8725c07813cf644f94bc1dc613c030dab0b2e426f7fdd920b080608cf350e3fd969714a5b97fd13d6227721072166b09b21536440b7b5545579addd9fdbbad6f8769d98819567014433e1524c870034f24fd0d3f68fd22c582d5f54d28cb5298f0be58c1daf2943c79ffe7c9c0a0372a3e4a48db2068aa9f6d21f01089563a9c7a260beb2efa44a56dc6bf21e3690f45a6da27c6604b3eebd0fc3aadb2fc819fc6ee1bde55300e233dc5f08c8ef331216894d633fedab73372254f67fd387691308922ef82d65344aec024951f91b0ab0257af775cc681e99d317e7c251f58edb220eac6e759276d195f4ba64b0ec0615656185a101d3fb006c0941d85910c91c244373995612ee63bd9cf0aca1b55406ee5db6bbbac1a3536c12c50130228b7264db08b5501cb78edc623c12d3b5d7bb7f0dcccba541e136b977fa9e7e5e1e40186aa1a3dcd19631b665a9f1cf2f08690037fec8f88094c261a78a68274cf96f933aaa62b0851066f5494e


# db084c475a67737c7e
# 7ea08bceff0313eee1e6e700e0400001000077db084c475a67737c7e8e820103300009855416f213a1bea812428a7159e61fa2cf09677c5460537847496035c01beb3e1ed4dc85709ddf31c240f77d1cc04632ddd5d2e2f05a162e543955c0f8696ad8b82d573370c7e7fc67a7ec75505a11ea2e632959135632df0d05969466071fbcf36409476a78f83ca87e
def test_decode_packet_lg():
    print("test_decode_packet_v2")
    data_hex_str = "7ea08bceff0313eee1e6e700e0400001000077db084c475a67737c7ee082010330000879a66ad533b89c24bfe1680b0745ab2138b4098c33c9ba956639d0cbfce9a657a4076ad04ae0b190441d489b62452aef0c240229e8c0ff3c03e18ddabdc6cdffa94330ca9c16be8059aa17a9084b6bec007d2f675d720a65fd0a70f1eaf16122cddf80971057b4d8eb7e"
    encryption_key = bytes.fromhex("7340BC1501143C498CD677811D771921")
    authentication_key = bytes.fromhex("DDFC444A5C78B74D46C158DBE711D37A")
    dec = decrypt_aes_gcm_landis_and_gyr(data_hex_str, encryption_key, authentication_key)
    # show_data(dec) if (dec) else "CRC error"
    print(dec)
    assert dec == [{"key": "WirkenergieP", "value": 8684853}, {"key": "MomentanleistungP", "value": 1565}]


def test_decode_packet_sc_1():
    encryption_key = bytes.fromhex("A8C74F67ECA8EF9C55C4743FF6F4F031")
    authentication_key = bytes.fromhex("F6089912E1CC910884DFC86E9F028201")

    cipher_text = "db085341473500033fe28201f230000000fc1aab23652c74cf94ea17a2719952fe21f41aad4f712be354c9d274d6340ab9980692831894dcf65c73e4b96d76660f2f0fe1b39a4ef07f8aea45cbabf11f3a6dc0dc721be1b6a4fbd204bfa145025d83a0b3458fbb199bc4ae2144094ca7ee42ad9ac59bd477d8e9011e4d306d078044b34acfaeb366c1668e2ae34e1b9179f63e091c960f1b77ec115d5aefac45f2b7bea96e0ba993f89a667d1b8f76593bc752dc180d65db87fc344c93b727e175f3a7b027668b6fe1f06ce858bda9b66719d4e8a787195cf24fc63f07c7f6935993b29b69745f5a3e803f84ce310f1654ccf32bf02fd1a495c551692cf0e2527bf01891740f1a14fb67a3109755eb35eb4541f006c2517edd9b32c2c732899440c96c4c601a32a20fc27fe3a0af1c826a17769e24a913998314c6cdee5ca7ae04de72ef185288cec40b220ab8176bb3015d5a7a7200292bd9c8462dac9a116ff13a183208bf0b122fa8cb6aa6e9fce23937ccfff50998bb62a185efb13d7f956e4e8a902d8486e0e227c79f26e9f87283cffd9f25c602b204797a6d64f6fdf9844ddbd30b9ff5b51c41269a0ccecb46cf2b444da4d3e7aabadf9b568f3221b77db8e5ae23def82be121a56b3adf1586794863b2de001f54b70ccccb6698faf26c9f0237f2ddb549e9a46c2cb6d88d4acc1976b752a511f4522ae1bfca4d1d"

    dec = decrypt_sagemcom(cipher_text, encryption_key, authentication_key)
    assert dec == [{"key": "WirkenergieP", "value": 7112944}, {"key": "WirkenergieN", "value": 33153972}]


def test_decode_packet_lg_exception():
    print("test_decode_packet_v2")
    data_hex_str = (
        "7ea030ceff031386f8e0c0000300001f8b379c3b5a58d7c6c8517275468aae0f5b5f5916445e6fc45ca0fed1618ad77f2a7e"
    )
    encryption_key = bytes.fromhex("7340BC1501143C498CD677811D771921")
    authentication_key = bytes.fromhex("DDFC444A5C78B74D46C158DBE711D37A")
    try:
        decrypt_aes_gcm_landis_and_gyr(data_hex_str, encryption_key, authentication_key)
    except Exception as e:
        assert e.args[0] == "Wrong input encrypted data should have 282 characters. Please check your device"
