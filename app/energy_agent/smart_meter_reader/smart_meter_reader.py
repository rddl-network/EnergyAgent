from app.dependencies import config
from app.energy_agent.data_buffer import DataBuffer
from app.energy_agent.smart_meter_reader.mbus_reader import MbusReader
from app.energy_agent.smart_meter_reader.modbus_reader import ModbusReader
from app.energy_agent.energy_decrypter import decrypt_device
from app.helpers.logs import logger, log
from typing import Dict, Any
import json

from app.helpers.models import LANDIS_GYR, SAGEMCOM


class SmartMeterReader:
    @log
    def __init__(self, data_buffer: DataBuffer, smart_meter_config: Dict[str, Any]):
        self.smart_meter_config = smart_meter_config
        self.reader = self._get_reader()
        self.previous_data = None
        self.data_buffer = data_buffer

    @log
    def _get_reader(self):
        smart_meter_type = self.smart_meter_config.get("smart_meter_type")
        if not smart_meter_type:
            return None
        smart_meter_type = smart_meter_type.upper()
        if smart_meter_type == LANDIS_GYR:
            logger.info("Using MbusReader for Landis&Gyr meter")
            return MbusReader(
                serial_port=self.smart_meter_config.get("smart_meter_serial_port", "/dev/ttyUSB0"),
                baud_rate=self.smart_meter_config.get("smart_meter_baud_rate", 2400),
                address=self.smart_meter_config.get("smart_meter_address", 1),
                valid_frame_pattern=r"db08.*?7e7ea08bceff0313ee",
            )
        elif smart_meter_type == SAGEMCOM:
            return ModbusReader(start_index=self.smart_meter_config.get("start_index", "5e4e"))
        else:
            raise ValueError(f"Unsupported meter type: {smart_meter_type}")

    @log
    def read_meter_data(self) -> dict | None:
        smart_meter_type = self.smart_meter_config.get("smart_meter_type").upper()
        data = None
        if smart_meter_type == LANDIS_GYR:
            data = self._read_landis_gyr()
        elif smart_meter_type == SAGEMCOM:
            data = self._read_sagemcom()
        _check_if_valid_incremental_data = self._check_if_valid_incremental_data(data)

        if not _check_if_valid_incremental_data:
            return None
        self.previous_data = data
        self.data_buffer.add_data({smart_meter_type: data})
        return data

    @log
    def _read_landis_gyr(self) -> Dict:
        with self.reader as reader:
            frame = reader.read_frame()
            if frame:
                data = decrypt_device(frame, self.smart_meter_config)
                logger.debug(f"Successfully decrypted data: {data}")
                return data
            else:
                logger.error("Failed to read frame from Landis&Gyr meter")
                return {}

    @log
    def _read_sagemcom(self) -> Dict:
        self.reader.client = self.reader.get_client(
            serial_port=self.smart_meter_config.get("smart_meter_serial_port", "/dev/ttyUSB0"),
            baudrate=self.smart_meter_config.get("smart_meter_baudrate", 2400),
            bytesize=self.smart_meter_config.get("byte_size", 8),
            parity=self.smart_meter_config.get("parity", "N"),
            stopbits=self.smart_meter_config.get("stopbits", 1),
            timeout=self.smart_meter_config.get("timeout", 90),
        )
        hex_data = self.reader.read_frame()
        if hex_data:
            return decrypt_device(hex_data, self.smart_meter_config)
        else:
            logger.error("Failed to read data from Sagemcom meter")
            return {}

    @log
    def _check_if_valid_incremental_data(self, data: Dict[str, Any]) -> bool:
        is_prev_data_none = self.previous_data is None
        is_data_none = data is None
        logger.debug(f"is_prev_data_none: {is_prev_data_none}, data: {data}")

        if is_prev_data_none and not is_data_none:
            logger.debug("Previous data is None and data is not None")
            return True

        if is_prev_data_none or is_data_none:
            logger.debug("No previous data or data is None")
            return False

        previous_energy_in = self.previous_data.get("absolute_energy_in", -1)
        current_energy_in = data.get("absolute_energy_in", -1)
        previous_energy_out = self.previous_data.get("absolute_energy_out", -1)
        current_energy_out = data.get("absolute_energy_out", -1)

        has_valid_increment_in = previous_energy_in <= current_energy_in
        has_valid_increment_out = previous_energy_out <= current_energy_out

        if has_valid_increment_in or has_valid_increment_out:
            return True

        return False
