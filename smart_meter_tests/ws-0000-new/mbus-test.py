import json
from mbus_reader import MbusReader
from energy_decrypter import decrypt_gcm
from lg_e450 import parse_e450_meter_data

def main():
    with MbusReader() as reader:
        frame_payload = reader.read_frame()
        if frame_payload:
            print("Successfully received a valid frame.")
            # print(f"frame payload: {frame_payload}")
            auth_key_bytes = bytes.fromhex("00000000000000000000000000000000")
            dec_key_bytes = bytes.fromhex("00000000000000000000000000000000")
            obis_dlms = decrypt_gcm(auth_key_bytes, frame_payload, dec_key_bytes)
            # print(obis_dlms)
            obis_dlms_parsed = parse_e450_meter_data(obis_dlms)
            print(f'{obis_dlms_parsed["obis_values"]["1.0.1.8.0.255"]["interpretation"]}: {obis_dlms_parsed["potential_energy_values"][7]["value"]}')

        else:
            print("Failed to receive a valid frame.")


if __name__ == "__main__":
    main()
