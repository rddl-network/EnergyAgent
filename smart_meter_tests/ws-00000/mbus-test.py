import json
from mbus_reader import MbusReader
from energy_decrypter import decrypt_gcm
from lg_e450 import parse_e450_meter_data


def main():
    with MbusReader() as reader:
        frame_payload = reader.read_frame()
        # frame_payload = "db084c475a677362f13a8201c53000b1cdb52ec1eb626fde9e6d337047190e0cb1ca7f6d681d0dbede752c685dadf86382cf4ea66bb1890e11fdb1eb87090db5fc451603362da0ce529e57cb0be9e3af314e61ef3c3ea7ec236dcc3846bacd3256c98a220165fcc30696c7a8a3b44114b87c816b760d420a474c319e92d674b21117089bb4c52b7cc551eaf3052a2892fcdd95c48bedf90d5d521cfe4b3cc4f3b974c865d9116d5208e19831d869db3a1d6609e4a54c43c9b9504495a43e21f5b344c462d5e79e9f1416484f359a0cc56ac0a1bae8445144bee3a7aa7e8320b36a2703374a6441cb307430c13d0ae891b8030768e7626e0f7045185945483038efd0520c05ff5179f8e0090ae86317718fa4f09666f7609b365a72bb82e655242c3fdb7c9aa86c9de78346fc62a92a8bc421c9aaef15bf786b09035a8d95de21c38a56a5e01dd2308ef2b949aa89c8a53c3d1d8e609ac6e026a8f9eb79d597983a2b519b24cbce415c74947893a5a0c6fc1db0926f2ec72fc115bb4f8ff217c356a2752c1c0ef4195e1c5312ab0d23e2535cffc6bd4a0c9f002c753b05ac313888a81021e52c248cebf3c566639b6e82755d6abd1da2b4ca707812cdb9c44e4688c957c9d9c488705d0e098b41d6096d259ebde315dd"
        if frame_payload:
            print("Successfully received a valid frame.")
            print(f"frame payload: {frame_payload}")
            auth_key_bytes = bytes.fromhex("00000000000000000000000000000000")
            dec_key_bytes = bytes.fromhex("00000000000000000000000000000000")
            obis_dlms = decrypt_gcm(auth_key_bytes, frame_payload, dec_key_bytes)
            obis_dlms_parsed = parse_e450_meter_data(obis_dlms)
            print(obis_dlms_parsed)
            jstr = json.dumps(obis_dlms_parsed, indent=2)
            print(jstr)

        else:
            print("Failed to receive a valid frame.")


if __name__ == "__main__":
    main()
