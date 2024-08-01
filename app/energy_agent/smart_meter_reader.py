from app.dependencies import config
from app.energy_agent.mbus_reader import LandisGyrE450Reader
from app.energy_agent.modbus_reader import ModbusReader
from app.energy_agent.energy_decrypter import decrypt_device, LANDIS_GYR, SAGEMCOM
from app.helpers.logs import logger, log
from typing import Dict, Any
import json


class SmartMeterReader:
    @log
    def __init__(self, meter_type: str):
        self.meter_type = meter_type.lower()
        self.config = config
        self.reader = self._get_reader()

    @log
    def _get_reader(self):
        if self.meter_type == LANDIS_GYR:
            return LandisGyrE450Reader(
                serial_port=config.smart_meter_serial_port,
                baud_rate=config.smart_meter_baud_rate,
                address=config.smart_meter_address,
            )
        elif self.meter_type == SAGEMCOM:
            return ModbusReader(start_index=self.config.get("start_index", "5e4e"))
        else:
            raise ValueError(f"Unsupported meter type: {self.meter_type}")

    @log
    def read_meter_data(self) -> Dict[str, Any]:
        if self.meter_type == LANDIS_GYR:
            return self._read_landis_gyr()
        elif self.meter_type == SAGEMCOM:
            return self._read_sagemcom()

    @log
    def _read_landis_gyr(self) -> Dict[str, Any]:
        with self.reader as reader:
            frame = reader.read_frame()
            if frame:
                decrypted_data = decrypt_device(frame)
                return self._parse_landis_gyr_data(decrypted_data)
            else:
                logger.error("Failed to read frame from Landis&Gyr meter")
                return {}

    @log
    def _read_sagemcom(self) -> Dict[str, Any]:
        self.reader.client = self.reader.get_client(
            serial_port=config.smart_meter_serial_port, baudrate=config.smart_meter_baud_rate
        )
        hex_data = self.reader.serial_read_smartmeter()
        if hex_data:
            decrypted_data = decrypt_device(hex_data)
            return self._parse_sagemcom_data(decrypted_data)
        else:
            logger.error("Failed to read data from Sagemcom meter")
            return {}

    @log
    def _parse_landis_gyr_data(self, decrypted_data: str) -> Dict[str, Any]:
        try:
            data = json.loads(decrypted_data)
            return {
                "meter_type": LANDIS_GYR,
                "timestamp": data.get("time_stamp"),
                "absolute_energy_in": float(data.get("absolute_energy_in", 0)),
                "absolute_energy_out": float(data.get("absolute_energy_out", 0)),
                "raw_data": data,
            }
        except json.JSONDecodeError:
            logger.error("Failed to parse Landis&Gyr data")
            return {}

    @log
    def _parse_sagemcom_data(self, decrypted_data: str) -> Dict[str, Any]:
        try:
            data = json.loads(decrypted_data)
            return {
                "meter_type": SAGEMCOM,
                "timestamp": data.get("timestamp"),
                "absolute_energy_in": float(data.get("energy_in", 0)),
                "absolute_energy_out": float(data.get("energy_out", 0)),
                "raw_data": data,
            }
        except json.JSONDecodeError:
            logger.error("Failed to parse Sagemcom data")
            return {}
