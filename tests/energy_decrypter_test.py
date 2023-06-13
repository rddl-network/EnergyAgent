from app.energy_meter_interaction.energy_decrypter import decrypt_evn_data, transform_to_metrics
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend

from Crypto.Cipher import AES
from Crypto.Util import Counter
import json

from gurux_dlms.GXDLMSTranslator import GXDLMSTranslator
import xml.etree.ElementTree as ET

def test_decode_packet_v2():
    print("test_decode_packet_v2")
    data_hex_str = "68fafa6853ff000167db085341475905e990f381f8200001ca1d78efc0c0df5eb7fdf7ccef510234c8281c7dadfecd22d027a91352206a2f33ecb771c238240da352a398feda9ec144bcde15108e045470d549a35cad7fe716e1fdcfbbd75bae402019d69e4cdc58af40876b1a3d9428a2388ab63471c35c245784ebff041af5d55791f954ada371815940927e49a8208bfa1098a0203c2fe35808db07b9c01d366b4c7cc302d7e8eea2ecf5a97a6a3c5e67ed44c59e2eb6e04d82e5e35ae9c2237cf03119d40b48b132df77cac7b614fe30655838e76b9a28dbb6294eb8e100eafd98ca7e4a9ca77ee0dbc5d8511709a028d57f1010b28ae92461ab618022166814146853ff110167e5a52b128178e1fd01a2d75b60beab0716"
    dec = decrypt_evn_data(data_hex_str)
    metric = transform_to_metrics(dec, "test")
    # show_data(dec) if (dec) else "CRC error"
    print(dec)
    assert dec != None


def decrypt_aes_gcm(encrypted_data, key, iv, tag):
    # create cipher
    cipher = Cipher(
        algorithms.AES(key),
        modes.GCM(iv, tag),
        backend=default_backend()
    )

    # decryptor object
    decryptor = cipher.decryptor()

    # decrypt data
    decrypted_data = decryptor.update(encrypted_data) + decryptor.finalize()

    # return decrypted data
    return decrypted_data



def test_decode_packet_v2():
    print("test_decode_packet_v2")
    7
    # ea08bceff0313eee1e6e700e0400001000077db084c475a67737c7ee0820103300001669a7654da96c65e4930a6f3719e304f4bebf8d6600508958b6cd46b16e8310b6868527c30ec8197ff9f80e7107ad7db303072428e0c0f59fcbe2dfb07c6edc5e1c4eb0a40dbf3e73ed8a52e65f3799f63a2341b345a940224ecda0ceb215a6c7bac19020d4468ce2a7e
    encrypted_data = bytes.fromhex('7ea08bceff0313eee1e6e700e0400001000077db084c475a67737c7ee0820103300001669a7654da96c65e4930a6f3719e304f4bebf8d6600508958b6cd46b16e8310b6868527c30ec8197ff9f80e7107ad7db303072428e0c0f59fcbe2dfb07c6edc5e1c4eb0a40dbf3e73ed8a52e65f3799f63a2341b345a940224ecda0ceb215a6c7bac19020d4468ce2a7e')

    # test = ET.fromstring(GXDLMSTranslator().pduToXml("3000177BCA14DD298539C05BD0E9250BCB05D33295AAD43EDA9A14E25AC843C12FC63CA7E5C42A4D53E3F6A0C9C8793C0E1D011AB0DF9B7A48A3361428240D3775A473CD4AC2238AB2594D87C7B037BB5BC130E3070770E04B9E407DA3CD42314BD87F2E08067D34A7CA9BFF215F01815448199ABA45CBDBE44CCABAAC4EB1CB10D3F89D2FD3948408B5A45BE7C56C4AE060E994D14C112D3922F0C047DB71D047098EC576F0A98FE6A2FA51C1A99DA63ADDD6EDC6E85D37E439B45A327C42372187E2DBD02776EF92380E5E9234D7B0DBA1DA122B0C6C4DD98E103839B3784C1606FA339A13717B673DB2EFCFF3A84FC53252EB8649881117E26462D5489052C89E62"))
    key = bytes.fromhex('7340BC1501143C498CD677811D771921')
    auth_key = bytes.fromhex('DDFC444A5C78B74D46C158DBE711D37A')

    data = parse_received_data(encrypted_data, key, auth_key)
    # metric = transform_to_metrics(dec, "test")
    # show_data(dec) if (dec) else "CRC error"
    print(data)

from Crypto.Cipher import AES
import json

# --------------- MAIN FUNCTION ---------------
def parse_received_data(message, key, auth_key):
    # Decrypt message
    decrypted_message = decrypt_message3(message, key, auth_key)
    # decrypted_message = decrypt_message3(message, key, auth_key)

    print(decrypted_message)

    # Extract time and date from decrypted message
    year = bytes_to_int(decrypted_message, 22, 24)
    month = bytes_to_int(decrypted_message, 24, 25)
    day = bytes_to_int(decrypted_message, 25, 26)
    hour = bytes_to_int(decrypted_message, 27, 28)
    minute = bytes_to_int(decrypted_message, 28, 29)
    second = bytes_to_int(decrypted_message, 29, 30)
    timestamp = f"{day:02d}.{month:02d}.{year:04d} {hour:02d}:{minute:02d}:{second:02d}"

    # Create JSON
    doc = {}
    doc["timestamp"] = timestamp
    doc["+A"] = bytes_to_int(decrypted_message, 35, 39)/1000.0
    doc["-A"] = bytes_to_int(decrypted_message, 40, 44)/1000.0
    doc["+R"] = bytes_to_int(decrypted_message, 45, 49)/1000.0
    doc["-R"] = bytes_to_int(decrypted_message, 50, 54)/1000.0
    doc["+P"] = bytes_to_int(decrypted_message, 55, 59)
    doc["-P"] = bytes_to_int(decrypted_message, 60, 64)
    doc["+Q"] = bytes_to_int(decrypted_message, 65, 69)
    doc["-Q"] = bytes_to_int(decrypted_message, 70, 74)
    payload = json.dumps(doc)

    # Publish JSON
    print(payload)
    return payload


# --------------- DECRYPTOR ---------------

def decrypt_message2(received_data, key):
    # Extract message and nonce from received data
    encrypted_message = received_data[28:102]
    additive = bytes([0x00, 0x00, 0x00, 0x02])
    nonce = received_data[14:22] + received_data[24:28] + additive
    counter = Counter.new(128, initial_value=int.from_bytes(nonce, byteorder='big'))
    # Decrypt message
    aes = AES.new(key, AES.MODE_GCM, counter=counter)
    decrypted_message = aes.decrypt(encrypted_message)
    return decrypted_message


from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def decrypt_message3(received_data, key, authentication_key):
    # Extract message and nonce from received data
    additive = bytes([0x00, 0x00, 0x00, 0x02])
    encrypted_message = bytes.fromhex("DB084C475A67737C7EE0820103300001669A7654DA96C65E4930A6F3719E304F4BEBF8D6600508958B6CD46B16E8310B6868527C30EC8197FF9F80E7107AD7DB303072428E0C0F59FCBE2DFB07C6EDC5E1C4EB0A40DBF3E73ED8A52E65F3799F63A2341B345A940224ECDA0CEB215A6C7BAC19020D4468")
    nonce = received_data[14:22] + received_data[24:28] + additive

    # Decrypt the message with AES-GCM
    aesgcm = AESGCM(key)
    decrypted_message = aesgcm.decrypt(nonce, encrypted_message, authentication_key)

    return decrypted_message.hex()

# --------------- HELPER FUNCTION ---------------

def bytes_to_int(bytes_array, start, end):
    return int.from_bytes(bytes_array[start:end], byteorder='big')
