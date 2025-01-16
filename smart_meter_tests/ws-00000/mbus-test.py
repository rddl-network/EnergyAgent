import serial
import time
import binascii
from energy_decrypter import decrypt_aes_gcm_landis_and_gyr
import re

class LandisGyrE450Reader:
    def __init__(self, serial_port='/dev/ttyUSB0', baud_rate=2400, address=1):
        self.serial_port = serial_port
        self.baud_rate = baud_rate
        self.address = address
        self.ser = None

    def __enter__(self):
        self.open_connection()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_connection()

    def open_connection(self):
        try:
            self.ser = serial.Serial(
                port=self.serial_port,
                baudrate=self.baud_rate,
                bytesize=8,
                parity='E',
                stopbits=1,
                timeout=1
            )
            print(f"Serial port opened: {self.ser.name}")
        except serial.SerialException as e:
            print(f"Error opening serial port: {e}")
            raise

    def close_connection(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("Serial port closed")

    def send_ping(self):
        print(f"Sending ping to address {self.address}")
        ping_frame = bytes([0x10, 0x40, self.address, self.address + 64])
        self.ser.write(ping_frame)
        print(f"Ping frame sent: {ping_frame.hex()}")
        time.sleep(0.5)
        response = self.ser.read(1)
        if response:
            print(f"Received response: {response.hex()}")
            return True
        else:
            print("No response received")
            return False

    def send_request_frame(self):
        request_frame = bytes([0x68, 0x03, 0x03, 0x68, 0x53, self.address, 0x50, 0x16])
        self.ser.write(request_frame)
        print(f"Request frame sent: {request_frame.hex()}")

    def extract_valid_frame(self, hex_data):
        valid_frame_pattern=r"db08.*?7e7ea08bceff0313ee"
        if valid_frame_pattern == "":
            return hex_data
        match = re.search(valid_frame_pattern, hex_data)
        return match.group(0) if match else None

    def read_frame2(self, max_attempts=10):
        attempt = 0
        while attempt < max_attempts:
            try:
                attempt += 1
                print(f"\nAttempt {attempt} of {max_attempts}")
                if not self.ser:
                    self.open_connection()

                #meterbus.send_request_frame(self.ser, self.address)
                #time.sleep(1)
                start_time = time.time()
                bytesarray = bytearray()
                while time.time() - start_time < 15:
                    chunk = self.ser.read(2000)
                    print(f"chunk: {chunk.hex()}")
                    if chunk:
                        bytesarray.extend(chunk)
                        frame = self.extract_valid_frame(bytesarray.hex().lower())
                        if frame:
                            #logger.debug(f"Valid frame found: {frame}")
                            return frame
                    else:
                        bytesarray = bytearray()

                print(f"No valid frame found in attempt {attempt}")
            except Exception as e:
                print(f"Error in read_frame attempt {attempt}: {e}")

        # If all attempts fail, raise an exception or return None
        print("Failed to read valid frame after maximum attempts.")
        return None

    def read_frame(self, max_attempts=10):
        attempt = 0
        while attempt < max_attempts:
            attempt += 1
            print(f"\nAttempt {attempt} of {max_attempts}")
            start_time = time.time()
            buffer = bytearray()
            frame = False
            while time.time() - start_time < 10:  # 10 seconds timeout
                mbusbytes = self.ser.read(1000)
                print(f"mbusbytes: {mbusbytes.hex()}")
                for byte in mbusbytes:
                    #print(f"{hex(byte)}")
                    if byte == 126:
                        buffer.extend([byte])
                        if not frame:
                            #print(f"HIT")
                            frame = True
                        else:
                            #print(f"Frame: {buffer.hex()}")
                            return buffer
                    elif frame:
                        buffer.extend([byte])
                        #print(f"Frame byte: {hex(byte)}")
                    #else:
                        #print(f"NO FRAME: {hex(byte)}")
        print("Max attempts reached without receiving a valid frame")
        return None

    def parse_frame(self, frame):
        if not frame:
            return "No valid frame received."

        frame_hex = frame.hex()
        print(f"Raw frame (hex): {frame_hex}")
        print(f"Raw frame (ASCII): {frame.decode('ascii', errors='replace')}")

        # Basic frame structure parsing
        start_end = frame_hex[:2] + frame_hex[-2:]
        length = frame_hex[2:4]
        control = frame_hex[4:6]
        address = frame_hex[6:8]
        ci_field = frame_hex[8:10]
        
        # Identification
        identification = bytes.fromhex(frame_hex[10:36]).decode('ascii', errors='replace')
        
        # Access number and status
        access_number = frame_hex[36:38]
        status = frame_hex[38:40]
        
        # Configuration word
        config_word = frame_hex[40:44]
        
        # Parse data records
        data_start = 44
        data_records = []
        while data_start < len(frame_hex) - 4:  # -4 to account for checksum and stop byte
            dif = frame_hex[data_start:data_start+2]
            data_start += 2
            vif = frame_hex[data_start:data_start+2]
            data_start += 2
            
            # Determine data length based on DIF
            data_length = 0
            if dif in ['01', '02', '03', '04']:
                data_length = int(dif, 16) * 2
            elif dif == '05':
                data_length = 8
            elif dif in ['06', '0D']:
                data_length = 12
            
            data = frame_hex[data_start:data_start+data_length]
            data_start += data_length
            
            data_records.append(f"DIF: {dif}, VIF: {vif}, Data: {data}")

        # Checksum
        checksum = frame_hex[-4:-2]

        return f"""
Frame Structure:
----------------
Start/End: {start_end}
Length: {length}
Control: {control}
Address: {address}
CI Field: {ci_field}
Identification: {identification}
Access Number: {access_number}
Status: {status}
Configuration Word: {config_word}

Data Records:
-------------
{chr(10).join(data_records)}

Checksum: {checksum}
"""



def main():
    #try:
        #with LandisGyrE450Reader() as reader:
            #frame = reader.read_frame2()
    frame = "db084c475a677362f13a8201c53000b1cdb52ec1eb626fde9e6d337047190e0cb1ca7f6d681d0dbede752c685dadf86382cf4ea66bb1890e11fdb1eb87090db5fc451603362da0ce529e57cb0be9e3af314e61ef3c3ea7ec236dcc3846bacd3256c98a220165fcc30696c7a8a3b44114b87c816b760d420a474c319e92d674b21117089bb4c52b7cc551eaf3052a2892fcdd95c48bedf90d5d521cfe4b3cc4f3b974c865d9116d5208e19831d869db3a1d6609e4a54c43c9b9504495a43e21f5b344c462d5e79e9f1416484f359a0cc56ac0a1bae8445144bee3a7aa7e8320b36a2703374a6441cb307430c13d0ae891b8030768e7626e0f7045185945483038efd0520c05ff5179f8e0090ae86317718fa4f09666f7609b365a72bb82e655242c3fdb7c9aa86c9de78346fc62a92a8bc421c9aaef15bf786b09035a8d95de21c38a56a5e01dd2308ef2b949aa89c8a53c3d1d8e609ac6e026a8f9eb79d597983a2b519b24cbce415c74947893a5a0c6fc1db0926f2ec72fc115bb4f8ff217c356a2752c1c0ef4195e1c5312ab0d23e2535cffc6bd4a0c9f002c753b05ac313888a81021e52c248cebf3c566639b6e82755d6abd1da2b4ca707812cdb9c44e4688c957c9d9c488705d0e098b41d6096d259ebde315dd"
    if frame:
        print("Successfully received a valid frame.")
        print(f"frame: {frame}")
        #parsed_frame = reader.parse_frame(frame)
        #print(parsed_frame)
        print("\nDecrpyt\n")
        
        dec = decrypt_aes_gcm_landis_and_gyr(
            frame, #frame.hex().lower(),
            bytes.fromhex("00000000000000000000000000000000"),
            bytes.fromhex("00000000000000000000000000000000"))
        print(dec)
        
    else:
        print("Failed to receive a valid frame.")
    #except serial.SerialException as e:
    #    print(f"Serial port error: {e}")
    #except Exception as e:
    #    print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
