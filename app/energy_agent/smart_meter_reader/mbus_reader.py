import serial
import meterbus
import time
import re

from app.helpers.logs import logger, log


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
    def extract_valid_frame(self, hex_data):
        if self.valid_frame_pattern == "":
            return hex_data
        match = re.search(self.valid_frame_pattern, hex_data)
        return match.group(0) if match else None

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
                while time.time() - start_time < 15:
                    chunk = self.ser.read(2000)
                    if chunk:
                        frame = self.extract_valid_frame(chunk.hex().lower())
                        if frame:
                            return frame
                logger.debug(f"No valid frame found in attempt {attempt}")
            except Exception as e:
                logger.error(f"Error in read_frame attempt {attempt}: {e}")

        # If all attempts fail, raise an exception or return None
        logger.error("Failed to read valid frame after maximum attempts.")
        return None
