import serial
import time
import binascii
from energy_decrypter import decrypt_aes_gcm_landis_and_gyr, decrypt_sagemcom

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
                if len(mbusbytes) == 0:
                    buffer = bytearray()
                else:
                    buffer.extend(mbusbytes)
                    print(f"mbusbytes: {mbusbytes.hex()}")
                    if mbusbytes[-1] == 126:
                        return buffer
                #for byte in mbusbytes:
                #    #print(f"{hex(byte)}")
                #    if byte == 126:
                #        buffer.extend([byte])
                #        if not frame:
                #            #print(f"HIT")
                #            frame = True
                #        else:
                #            #print(f"Frame: {buffer.hex()}")
                #            return buffer
                #    elif frame:
                #        buffer.extend([byte])
                #        #print(f"Frame byte: {hex(byte)}")
                #    #else:
                #        #print(f"NO FRAME: {hex(byte)}")
        print("Max attempts reached without receiving a valid frame")
        return None

    def parse_frame(self, frame):
        if not frame:
            return "No valid frame received."

        frame_hex = frame.hex()
        print(f"Raw frame (hex): {frame_hex}")
        #print(f"Raw frame (ASCII): {frame.decode('ascii', errors='replace')}")

        # Basic frame structure parsing
        start_end = frame_hex[:2] + frame_hex[-2:]
        length = frame_hex[2:4]
        control = frame_hex[4:6]
        address = frame_hex[6:8]
        ci_field = frame_hex[8:10]
        
        # Identification
        identification = "" #bytes.fromhex(frame_hex[10:36]).decode('ascii', errors='replace')
        
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
    try:
        with LandisGyrE450Reader() as reader:
            frame = reader.read_frame()
            if frame:
                print("Successfully received a valid frame.")
                print(f"frame: {frame.hex()}")
                #parsed_frame = reader.parse_frame(frame)
                #print(parsed_frame)
                print("\nDecrpyt\n")
                
#                dec = decrypt_aes_gcm_landis_and_gyr(
                dec = decrypt_sagemcom(
                    frame,
                    bytes.fromhex("4475D2230289243A4AE7732E2396C572"),
                    bytes.fromhex("8FEADE1D7057D94D816A41E09D17CB58"))
                print(dec)
                
            else:
                print("Failed to receive a valid frame.")
    except serial.SerialException as e:
        print(f"Serial port error: {e}")
    #except Exception as e:
    #    print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
