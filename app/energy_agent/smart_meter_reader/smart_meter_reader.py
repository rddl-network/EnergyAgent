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
        smart_meter_type = self.smart_meter_config.get("smart_meter_type").toLowerCase()
        if smart_meter_type == LANDIS_GYR:
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
        smart_meter_type = self.smart_meter_config.get("smart_meter_type").toLowerCase()
        data = None
        if smart_meter_type == LANDIS_GYR:
            data = self._read_landis_gyr()
        elif smart_meter_type == SAGEMCOM:
            data = self._read_sagemcom()
        _check_if_valid_incremental_data = self._check_if_valid_incremental_data(data)

        if not _check_if_valid_incremental_data:
            return None
        self.previous_data = data
        self.data_buffer.add_data({smart_meter_type: json.dumps(data)})
        return data

    @log
    def _read_landis_gyr(self) -> Dict:
        with self.reader as reader:
            frame = reader.read_frame()
            if frame:
                return decrypt_device(frame)
            else:
                logger.error("Failed to read frame from Landis&Gyr meter")
                return {}

    @log
    def _read_sagemcom(self) -> Dict:
        self.reader.client = self.reader.get_client(
            serial_port=config.smart_meter_serial_port,
            baudrate=config.smart_meter_baud_rate,
        )
        hex_data = self.reader.serial_read_smartmeter()
        if hex_data:
            return decrypt_device(hex_data)
        else:
            logger.error("Failed to read data from Sagemcom meter")
            return {}

    @log
    def _check_if_valid_incremental_data(self, data: Dict[str, Any]) -> bool:
        is_prev_data_none = self.previous_data is None
        has_valid_increment_in = self.previous_data.get("absolute_energy_in") < data.get("absolute_energy_in")
        has_valid_increment_out = self.previous_data.get("absolute_energy_out") <= data.get("absolute_energy_out")

        if is_prev_data_none or (has_valid_increment_in and has_valid_increment_out):
            return True
        return False
