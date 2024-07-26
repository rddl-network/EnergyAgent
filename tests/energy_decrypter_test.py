from app.energy_agent.energy_decrypter import decrypt_aes_gcm_landis_and_gyr, decrypt_sagemcom


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


def test_decode_packet_lg_2():
    print("test_decode_packet_v2")
    data_hex_str = "7ea08bceff0313eee1e6e700e0400001000077db084c475a67737c7ecb820103300036d79ff09867f39169810ae8be6d2b0ccb0b516e91fc1fde82d68fb8e0b11501bef0d3d33eac508a1c7d8f5fc1cab563c1cbcab40b2005f307f762b6d47fb6398c5df5d4d5eec117c6fbaa764a707fb9f71cbff4c0488dc40420541d49cc9108e1b4b49e66302285d01d7e"
    encryption_key = bytes.fromhex("DD7E6510916F2F73F026C70C6A3F7EF1")
    authentication_key = bytes.fromhex("9DF1169A749F49500174AA840243E7E ")
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
        assert (
            e.args[0]
            == "Wrong input encrypted data should have 282 characters. Please check your device, data_hex 7ea030ceff031386f8e0c0000300001f8b379c3b5a58d7c6c8517275468aae0f5b5f5916445e6fc45ca0fed1618ad77f2a7e"
        )
