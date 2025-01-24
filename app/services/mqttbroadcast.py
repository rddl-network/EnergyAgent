import asyncio
import json
from typing import Optional, Dict, Any
from gmqtt import Client as MQTTClient
from gmqtt.mqtt.constants import MQTTv311

from app.energy_agent.smart_meter_reader.smart_meter_reader import SmartMeterReader
from app.helpers.config_helper import load_config
from app.helpers.logs import log, logger
from app.dependencies import config, trust_wallet_instance, data_buffer
from app.helpers.models import MQTTConfig
from app.model.measurements import Measurements


class MQTTConnectionError(Exception):
    """Raised when there's an error connecting to the MQTT broker."""

    pass


class MQTTBroadcaster:
    def __init__(self) -> None:
        """Initialize the MQTT to broadcast data to with configuration."""
        self.mqtt_client: Optional[MQTTClient] = None
        self.topic_prefix: str = ""
        self.planetmint_address: str = ""
        self.task: Optional[asyncio.Task] = None

        self.mqtt_config: Optional[MQTTConfig] = None
        self._reconnect_task: Optional[asyncio.Task] = None

    async def _connect_mqtt(self) -> None:
        """Establish connection to MQTT broker."""
        if not self.mqtt_config:
            self.mqtt_config = MQTTConfig.model_validate(load_config(config.path_to_smart_meter_mqtt_config))

        keys = trust_wallet_instance.get_planetmint_keys()
        self.planetmint_address = keys.planetmint_address
        self.topic_prefix = self.mqtt_config.topic_prefix

        for attempt in range(self.max_reconnect_attempts):
            if self._stopping:
                raise MQTTConnectionError("Stopping requested during connection attempt")

            try:
                self.mqtt_client = MQTTClient(client_id=self.planetmint_address)
                self.mqtt_client.set_auth_credentials(self.mqtt_config.username, self.mqtt_config.password)
                await self.mqtt_client.connect(
                    host=self.mqtt_config.host,
                    port=self.mqtt_config.port,
                    version=MQTTv311,
                    keepalive=60,
                )
                logger.info("Successfully connected to MQTT broker")
                return
            except Exception as e:
                logger.error(f"MQTT connection attempt {attempt + 1} failed: {str(e)}")
                if attempt < self.max_reconnect_attempts - 1 and not self._stopping:
                    await asyncio.sleep(self.reconnect_interval)
                else:
                    raise MQTTConnectionError(
                        f"Failed to connect to MQTT broker after {self.max_reconnect_attempts} attempts"
                    )

    @log
    async def send_state(self, state) -> None:
        """Send measurements via MQTT."""
        try:
            # data = self.smart_meter.read_meter_data()
            # data = Measurements.getState()
            if state:
                await self._connect_mqtt(self)
                await self._send_mqtt(state)
                await self.mqtt_client.disconnect()
        except Exception as e:
            raise MQTTConnectionError(f"Failed to send the state: {str(e)}")

    @log
    async def _send_mqtt(self, data: Dict[str, Any]) -> None:
        """Send data to MQTT broker."""
        if not self.mqtt_client:
            raise MQTTConnectionError("MQTT client is not connected")

        try:
            topic = f"{self.topic_prefix}"
            payload = json.dumps(data)
            self.mqtt_client.publish(topic, payload, qos=1)
            logger.info(f"[X] Sent data to MQTT topic: {topic}, payload: {payload}")
        except Exception as e:
            raise MQTTConnectionError(f"Failed to send data via MQTT: {str(e)}")
