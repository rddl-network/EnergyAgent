import binascii

from app.energy_meter_interaction.energy_decrypter import decode_packet, show_data, extract_data


def test_decode_packet():
    data_hex_str = "7ea067cf022313fbf1e6e700db0849534b6974a8d8994f2000909dd750e337f09d460befa73f43e61e5cbdd88f7f1e4a91ff2fc936b8fd423c930d431f6f4288104a9c5b49389a5b4a3e976c924ae466d4e25abfd26a1573b95c0a4a4bce9a273f1233765c38c9367e"
    dec = decode_packet(bytearray.fromhex(data_hex_str))
    show_data(dec) if (dec) else "CRC error"
    test = extract_data(dec)
    print("test: ", test)
    assert dec != None
