import serial
from energy_decrypter import decrypt_aes_gcm_landis_and_gyr
from mbus_reader import MbusReader


def main():
    try:
        with MbusReader() as reader:
            frame = reader.read_frame()
            if frame:
                print("Successfully received a valid frame.")
                print(f"frame: {frame}")
                # parsed_frame = reader.parse_frame(frame)
                # print(parsed_frame)
                print("\nDecrpyt\n")

                dec = decrypt_aes_gcm_landis_and_gyr(
                    frame,  # frame.hex().lower(),
                    bytes.fromhex("4B1ED9523B7DA755C3822B2F63E33B37"),
                    bytes.fromhex("FB7A2527410579A8219E20D2CDEAC212"),
                )
                print(dec)

            else:
                print("Failed to receive a valid frame.")
    except serial.SerialException as e:
        print(f"Serial port error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
