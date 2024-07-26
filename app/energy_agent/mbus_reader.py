import serial
import meterbus
import time
import re

from app.helpers.logs import logger, log


class LandisGyrE450Reader:
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

    @staticmethod
    @log
    def extract_valid_frame(hex_data):
        pattern = r"7e[0-9a-f]{52}7e[0-9a-f]{224}7e"
        match = re.search(pattern, hex_data)
        return match.group(0) if match else None

    @log
    def send_ping(self):
        logger.debug(f"Sending ping to address {self.address}")
        meterbus.send_ping_frame(self.ser, self.address)
        time.sleep(0.5)
        response = self.ser.read(1)
        if response:
            logger.debug(f"Received response: {response.hex()}")
            return True
        else:
            logger.debug("No response received")
            return False

    def read_frame(self, max_attempts=10):
        attempt = 0
        buffer = "7e"

        while attempt < max_attempts:
            attempt += 1
            logger.debug(f"\nAttempt {attempt} of {max_attempts}")

            if self.send_ping():
                logger.debug("Ping successful, sending request frame")
                meterbus.send_request_frame(self.ser, self.address)
                time.sleep(1)

                start_time = time.time()
                while time.time() - start_time < 10:  # 10 seconds timeout
                    chunk = self.ser.read(1000)
                    if chunk:
                        buffer += chunk.hex()
                        return self.extract_valid_frame(buffer)
