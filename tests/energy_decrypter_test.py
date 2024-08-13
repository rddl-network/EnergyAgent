from app.energy_agent.energy_decrypter import (
    decrypt_aes_gcm_landis_and_gyr,
    decrypt_sagemcom,
)


def test_decode_packet_lg():
    print("test_decode_packet_v2")
    data_hex_str = "db084c475a67737c7ee0820103300038db9c8b5c5c82dd4faa65b34e90334af64459ec9fcc75b6859385865d30d329c40568742909c2ed6418cc30b29dd91c21c573aecf63d0b57083dfb4dfffa8b4aa05b0c7e4982c21cca07b6636f128563aa6032595190a8149f14025fdb1242e9be6197bd56823a983b17e7ea08bceff0313ee"
    encryption_key = bytes.fromhex("7340BC1501143C498CD677811D771921")
    authentication_key = bytes.fromhex("DDFC444A5C78B74D46C158DBE711D37A")
    dec = decrypt_aes_gcm_landis_and_gyr(data_hex_str, encryption_key, authentication_key)
    print(dec)
    assert dec == [
        {"key": "WirkenergieP", "value": 15685460},
        {"key": "MomentanleistungP", "value": 0},
        {"key": "WirkenergieN", "value": 5891165},
    ]


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
