import serial
import meterbus
import time
import re

from app.helpers.logs import logger, log
from app.energy_agent.smart_meter_reader.mbus_frame import DLMSFrame


class MbusReader:
    def __init__(
        self, serial_port="/dev/ttyUSB0", baud_rate=2400, address=1, valid_frame_pattern=r"db08.*?7e7ea08bceff0313ee"
    ):
        self.serial_port = serial_port
        self.baud_rate = baud_rate
        self.address = address
        self.valid_frame_pattern = valid_frame_pattern
        self.ser = None

    def __enter__(self):
        self.open_connection()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_connection()

    @log
    def open_connection(self):
        try:
            self.ser = serial.Serial(
                port=self.serial_port, baudrate=self.baud_rate, bytesize=8, parity="E", stopbits=1, timeout=1
            )
            logger.debug(f"Serial port opened: {self.ser.name}")
        except serial.SerialException as e:
            logger.error(f"Error opening serial port: {e}")
            raise

    @log
    def close_connection(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
            logger.debug("Serial port closed")

    @log
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
                logger.debug(f"\nAttempt {attempt} of {max_attempts}")
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
                        frames = MbusReader.extract_frames(bytes_array)
                        if len(frames) > 0:
                            payload = bytearray()
                            for frame in frames:
                                logger.debug(f"found frame: {frame}")
                                dlms_frame = DLMSFrame(frame)
                                payload.extend(dlms_frame.get_payload())
                            payload = dlms_frame.get_payload_hex()
                            logger.debug(f"Valid frame and payload found: {payload}")
                            return payload
                    else:
                        bytes_array = bytearray()
                logger.debug(f"No valid frame found in attempt {attempt}")
            except Exception as e:
                logger.error(f"Error in read_frame attempt {attempt}: {e}")

        # If all attempts fail, raise an exception or return None
        logger.error("Failed to read valid frame after maximum attempts.")
        return None
