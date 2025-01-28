import asyncio
from typing import Optional, Dict, Any

from app.energy_agent.smart_meter_reader.smart_meter_reader import SmartMeterReader
from app.helpers.config_helper import load_config
from app.helpers.logs import log, logger

from app.dependencies import config, data_buffer

DEFAULT_READ_INTERVAL = 900  # 15 minutes in seconds
DEFAULT_RECONNECT_INTERVAL = 60  # 1 minute in seconds
DEFAULT_MAX_RECONNECT_ATTEMPTS = 5
STOP_TIMEOUT = 10  # seconds to wait for graceful shutdown


class SmartMeterError(Exception):
    """Base class for Smart Meter related errors."""

    pass


class SmartMeterReadError(SmartMeterError):
    """Raised when there's an error reading data from the Smart Meter."""

    pass


class SmartMeterManager:
    def __init__(self, smart_meter_config: Dict[str, Any]) -> None:
        """Initialize the SmartMeterManager with configuration."""
        self.smart_meter = SmartMeterReader(smart_meter_config=smart_meter_config, data_buffer=data_buffer)

    @log
    def read_smart_meter(self) -> dict:
        """Read data from smart meter and send via MQTT."""
        try:
            data = self.smart_meter.read_meter_data()
            return data
        except Exception as e:
            raise SmartMeterReadError(f"Failed to read or send meter data: {str(e)}")
