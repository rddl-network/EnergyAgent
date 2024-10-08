import asyncio
import json
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from gmqtt import Client as MQTTClient
from gmqtt.mqtt.constants import MQTTv311

from app.energy_agent.smart_meter_reader.smart_meter_reader import SmartMeterReader
from app.helpers.config_helper import load_config, save_config
from app.helpers.logs import log, logger
from app.RddlInteraction.TrustWallet.osc_message_sender import is_not_connected
from app.dependencies import config, trust_wallet_instance, data_buffer
from app.helpers.models import MQTTConfig

METADATA_CONFIG_PATH = f"{config.config_base_path}/smart_meter_metadata.json"


class SmartMeterError(Exception):
    """Base class for Smart Meter related errors."""


class MQTTConnectionError(SmartMeterError):
    """Raised when there's an error connecting to the MQTT broker."""


class SmartMeterReadError(SmartMeterError):
    """Raised when there's an error reading data from the Smart Meter."""


class SmartMeterManager:
    def __init__(self, smart_meter_config: Dict[str, Any]) -> None:
        self.smart_meter = SmartMeterReader(smart_meter_config=smart_meter_config, data_buffer=data_buffer)
        self.mqtt_client: Optional[MQTTClient] = None
        self.topic_prefix: str = ""
        self.planetmint_address: str = ""
        self.task: Optional[asyncio.Task] = None
        self.running: bool = False
        self.read_interval: int = smart_meter_config.get("smart_meter_reading_interval", 900)
        self.status: str = load_config(METADATA_CONFIG_PATH).get("status", "stopped")
        self.reconnect_interval: int = 60
        self.max_reconnect_attempts: int = 5
        self.mqtt_config: Optional[MQTTConfig] = None

    @property
    def is_running(self) -> bool:
        return self.running and self.task is not None and not self.task.done()

    @log
    async def start(self) -> None:
        if not self.is_running:
            try:
                self.running = True
                await self._connect_mqtt()
                self.task = asyncio.create_task(self._read_and_send_loop())
                self._update_status("running")
                logger.info("Smart meter manager started")
            except MQTTConnectionError as e:
                self._handle_startup_error(str(e))

    @log
    async def stop(self) -> None:
        if self.is_running:
            self.running = False
            await self._disconnect_mqtt()
            await self._cancel_task()
            self._update_status("stopped")
            logger.info("Smart meter manager stopped")

    @log
    async def restart(self) -> None:
        await self.stop()
        await self.start()

    @log
    async def check_and_restart(self) -> None:
        if self.status == "running" and not self.is_running:
            logger.warning("Smart Meter Manager should be running but isn't. Attempting to restart...")
            await self.start()

    @log
    async def _connect_mqtt(self) -> None:
        if not self.mqtt_config:
            self.mqtt_config = MQTTConfig.model_validate(load_config(config.path_to_smart_meter_mqtt_config))

        keys = trust_wallet_instance.get_planetmint_keys()
        self.planetmint_address = keys.planetmint_address
        self.topic_prefix = self.mqtt_config.topic_prefix

        for attempt in range(self.max_reconnect_attempts):
            try:
                self.mqtt_client = MQTTClient(
                    client_id=self.planetmint_address,
                    username=self.mqtt_config.username,
                    password=self.mqtt_config.password,
                )
                await self.mqtt_client.connect(
                    host=self.mqtt_config.host,
                    port=self.mqtt_config.port,
                    version=MQTTv311,
                )
                logger.info("Successfully connected to MQTT broker")
                return
            except Exception as e:
                logger.error(f"MQTT connection attempt {attempt + 1} failed: {str(e)}")
                if attempt < self.max_reconnect_attempts - 1:
                    await asyncio.sleep(self.reconnect_interval)

        raise MQTTConnectionError(f"Failed to connect to MQTT broker after {self.max_reconnect_attempts} attempts")

    @log
    async def _disconnect_mqtt(self) -> None:
        if self.mqtt_client:
            await self.mqtt_client.disconnect()
            self.mqtt_client = None

    @log
    async def _cancel_task(self) -> None:
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
            self.task = None

    @log
    async def _read_and_send_loop(self) -> None:
        while self.running:
            try:
                await self._read_and_send_data()
            except SmartMeterReadError as e:
                logger.error(f"Error reading smart meter data: {str(e)}")
            except MQTTConnectionError:
                await self._handle_mqtt_connection_error()
            except Exception as e:
                logger.error(f"Unexpected error in read and send loop: {str(e)}")
            finally:
                await asyncio.sleep(self.read_interval)

    @log
    async def _read_and_send_data(self) -> None:
        data = self.smart_meter.read_meter_data()
        if data:
            await self._send_mqtt(data)

    @log
    async def _send_mqtt(self, data: Dict[str, Any]) -> None:
        if not self.mqtt_client:
            raise MQTTConnectionError("MQTT client is not connected")
        try:
            topic = f"{self.topic_prefix}/{self.planetmint_address}"
            payload = json.dumps(data)
            self.mqtt_client.publish(topic, payload, qos=1)
            logger.info(f"Sent data to MQTT topic: {topic}")
        except Exception as e:
            raise MQTTConnectionError(f"Failed to send data via MQTT: {str(e)}")

    @log
    async def _handle_mqtt_connection_error(self) -> None:
        logger.error("Lost connection to MQTT broker. Attempting to reconnect...")
        try:
            await self._connect_mqtt()
        except MQTTConnectionError as e:
            logger.error(f"Failed to reconnect to MQTT broker: {str(e)}")
            await asyncio.sleep(self.reconnect_interval)

    def _update_status(self, new_status: str) -> None:
        self.status = new_status
        save_config(METADATA_CONFIG_PATH, {"status": self.status})

    def _handle_startup_error(self, error_message: str) -> None:
        self.running = False
        self._update_status("error")
        logger.error(f"Failed to start Smart Meter Manager: {error_message}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to connect to MQTT broker",
        )


_manager_instance: Optional[SmartMeterManager] = None


@log
def get_smart_meter_manager(smart_meter_config: Dict[str, Any]):
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = SmartMeterManager(smart_meter_config)
    return _manager_instance


router = APIRouter(
    prefix="/smart_meter",
    tags=["smart_meter"],
    responses={404: {"detail": "Not found"}},
)


@router.get("/start")
async def start_smart_meter(
    manager: SmartMeterManager = Depends(get_smart_meter_manager),
):
    if is_not_connected(config.trust_wallet_port):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Wallet not connected")
    await manager.start()
    return {"status": manager.status}


@router.get("/stop")
async def stop_smart_meter(
    manager: SmartMeterManager = Depends(get_smart_meter_manager),
):
    await manager.stop()
    return {"status": manager.status}


@router.get("/status")
async def smart_meter_status(
    manager: SmartMeterManager = Depends(get_smart_meter_manager),
):
    return {"status": manager.status}


@router.get("/restart")
async def restart_smart_meter(
    manager: SmartMeterManager = Depends(get_smart_meter_manager),
):
    if is_not_connected(config.trust_wallet_port):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Wallet not connected")
    await manager.restart()
    return {"status": manager.status}
