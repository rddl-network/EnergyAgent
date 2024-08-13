from pymodbus.client import ModbusSerialClient
import time
import binascii
import re
from app.helpers.logs import logger, log

READ_SIZE = 511


class ModbusReader:
    def __init__(self, start_index: str = "5e4e"):
        self.client = None
        self.start_index = start_index

    @log
    def get_client(
        self,
        serial_port="/dev/ttyUSB0",
        baudrate=115200,
        bytesize=8,
        parity="N",
        stopbits=1,
        timeout=90,
    ):
        return ModbusSerialClient(
            port=serial_port,
            baudrate=baudrate,
            bytesize=bytesize,
            parity=parity,
            stopbits=stopbits,
            timeout=timeout,
        )

    @log
    def serial_read_smartmeter(self):
        try:
            if not self.client.connect():
                logger.error("Failed to connect to the smart meter")
                return None

            ser = self.client.socket
            raw_data = ser.read(READ_SIZE)
            if raw_data:
                hex_data = binascii.hexlify(raw_data).decode("utf-8")
                logger.debug(f"Raw data: {hex_data}")
                return self.extract_dataframes(hex_data)
            else:
                logger.error("No data received")
                return None

        except Exception as e:
            logger.error(f"Error reading from smart meter: {e}")
            return None
        finally:
            self.client.close()

    @log
    def extract_dataframes(self, hex_data):
        logger.debug("Extracting dataframes")

        # Pattern to match: starts with 5e4e, followed by any number of hex characters, ends with 5e4e
        pattern = f"{self.start_index}[0-9a-f]+{self.start_index}"
        match = re.search(pattern, hex_data)

        if match:
            frame = match.group(0)
            logger.info(f"Valid frame found: {frame}")
            return frame
        else:
            logger.warning("No valid frame found")
            return None

    @log
    def read_frame(self, max_attempts=3):
        for attempt in range(max_attempts):
            logger.debug(f"Attempt {attempt + 1} of {max_attempts}")
            frame = self.serial_read_smartmeter()
            if frame:
                return frame
            time.sleep(1)  # Wait before next attempt

        logger.error(f"Failed to read a valid frame after {max_attempts} attempts")
        return None
