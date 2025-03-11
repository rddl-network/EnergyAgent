import serial
import meterbus
import time


#from app.helpers.logs import logger, log
from mbus_frame import DLMSFrame


class MbusReader:
    def __init__(self, serial_port="/dev/ttyUSB0", baud_rate=2400, address=1):
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
                port=self.serial_port, baudrate=self.baud_rate, bytesize=8, parity="E", stopbits=1, timeout=1
            )
            print(f"Serial port opened: {self.ser.name}")
        except serial.SerialException as e:
            print(f"Error opening serial port: {e}")
            raise

    
    def close_connection(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("Serial port closed")

    
    @staticmethod
    def extract_frames(byte_array: bytearray):
        frame_list = []
        tmp_array = byte_array
        while tmp_array:
            frame, tmp_array = MbusReader.extract_frame(tmp_array)
            if frame:
                frame_list.append(frame)
        return frame_list

    @staticmethod
    def extract_frame(byte_array: bytearray):
        pointer = 0
        if byte_array[pointer] != 0x7E:
            return None, None
        pointer = pointer + 1
        if byte_array[pointer] != 0xA0:
            return None, None
        pointer = pointer + 1

        length = byte_array[pointer]
        if len(byte_array) >= length + 2:
            return byte_array[: length + 2], byte_array[length + 2 :]
        return None, None

    def read_frame(self, max_attempts=10):
        attempt = 0
        while attempt < max_attempts:
            try:
                attempt += 1
                print(f"\nAttempt {attempt} of {max_attempts}")
                if not self.ser:
                    self.open_connection()

                meterbus.send_request_frame(self.ser, self.address)
                time.sleep(1)
                start_time = time.time()
                bytes_array = bytearray()
                while time.time() - start_time < 15:
                    chunk = self.ser.read(2000)
                    if chunk:
                        bytes_array.extend(chunk)
                    else:
                        if len(bytes_array) > 0:
                            # process the previously composed frame chunks
                            # before waiting for another frame set
                            frames = MbusReader.extract_frames(bytes_array)
                            if len(frames) > 0:
                                payload = bytearray()
                                for frame in frames:
                                    print(f"found frame: {frame}")
                                    dlms_frame = DLMSFrame(frame)
                                    payload.extend(dlms_frame.get_payload())
                                payload = payload.hex()
                                print(f"Valid frame and payload found: {payload}")
                                return payload
                        # reset the bytes array in any case
                        bytes_array = bytearray()
                print(f"No valid frame found in attempt {attempt}")
            except Exception as e:
                print(f"Error in read_frame attempt {attempt}: {e}")

        # If all attempts fail, raise an exception or return None
        print("Failed to read valid frame after maximum attempts.")
        return None
