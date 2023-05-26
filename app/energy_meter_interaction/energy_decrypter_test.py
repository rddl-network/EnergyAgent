import binascii

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
    data_hex_str = "68fafa6853ff000167db085341475905e990f381f820000e7f1fbf17df7e9997ce84e6df6889180d2322b46259b6f6013ccf09f201f42122ac6a925080fcd711d03db8a67c9bc414b19531d6452346c159d16b0a9d04afeed300411ce66cf7f013a1d1c371003468c8f977948c4c55f69dbd7bbcfcec77059ca62d7377710b0fd20ceeb3b534521c9bcec5e0805226655a4d58dc590fcf5739297ae31b93a98b982d4454547132761a32bfb2e0ef6d864145a55b1ec671da5835188ffcf29a8908efe9e3fa4b46252b9278283dd01dca2d9aadeea3cfbae512219916a19ec3df2221f134be9ea4d9eff1a9aea44574fda7b9b5cb712b59f39d9b2c315e9f3f166814146853ff110167a3d8d8985d50946a5240cc21d36ad8f516"
    dec = decode_packet(bytearray.fromhex(data_hex_str))
    show_data(dec) if (dec) else "CRC error"
    test = extract_data(dec)
    print("test: ", test)
    assert dec != None
