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

DEFAULT_READ_INTERVAL = 900  # 15 minutes in seconds
DEFAULT_RECONNECT_INTERVAL = 60  # 1 minute in seconds
DEFAULT_MAX_RECONNECT_ATTEMPTS = 5
STOP_TIMEOUT = 10  # seconds to wait for graceful shutdown


class SmartMeterError(Exception):
    """Base class for Smart Meter related errors."""

    pass


class MQTTConnectionError(SmartMeterError):
    """Raised when there's an error connecting to the MQTT broker."""

    pass


class SmartMeterReadError(SmartMeterError):
    """Raised when there's an error reading data from the Smart Meter."""

    pass


class SmartMeterManager:
    def __init__(self, smart_meter_config: Dict[str, Any]) -> None:
        """Initialize the SmartMeterManager with configuration."""
        self.smart_meter = SmartMeterReader(smart_meter_config=smart_meter_config, data_buffer=data_buffer)
        self.mqtt_client: Optional[MQTTClient] = None
        self.topic_prefix: str = ""
        self.planetmint_address: str = ""
        self.task: Optional[asyncio.Task] = None
        self._stopping: bool = False
        self.running: bool = False
        self.read_interval: int = smart_meter_config.get("smart_meter_reading_interval", DEFAULT_READ_INTERVAL)
        self.status: str = load_config(config.metadata_config_path).get("status", "stopped")
        self.reconnect_interval: int = smart_meter_config.get("reconnect_interval", DEFAULT_RECONNECT_INTERVAL)
        self.max_reconnect_attempts: int = smart_meter_config.get(
            "max_reconnect_attempts", DEFAULT_MAX_RECONNECT_ATTEMPTS
        )
        self.mqtt_config: Optional[MQTTConfig] = None
        self._lock = asyncio.Lock()
        self._reconnect_task: Optional[asyncio.Task] = None

    @property
    def is_running(self) -> bool:
        """Check if the manager is currently running."""
        return self.running and self.task is not None and not self.task.done() and not self._stopping

    @log
    async def start(self) -> None:
        """Start the Smart Meter Manager."""
        async with self._lock:
            if self.is_running or self._stopping:
                logger.warning("Smart Meter Manager is already running or stopping")
                return

            try:
                self._stopping = False
                self.running = True
                await self._connect_mqtt()
                self.task = asyncio.create_task(self._read_and_send_loop())
                self.task.add_done_callback(self._handle_task_done)
                self._update_status("running")
                logger.info("Smart meter manager started successfully")
            except Exception as e:
                await self._cleanup()
                self._handle_startup_error(str(e))

    @log
    async def stop(self) -> None:
        """Stop the Smart Meter Manager."""
        async with self._lock:
            if not self.is_running and not self._stopping:
                logger.warning("Smart Meter Manager is not running")
                return

            try:
                self._stopping = True
                self.running = False

                # Cancel reconnection task if it exists
                if self._reconnect_task and not self._reconnect_task.done():
                    self._reconnect_task.cancel()

                # Wait for main task to complete with timeout
                if self.task:
                    try:
                        await asyncio.wait_for(self.task, timeout=STOP_TIMEOUT)
                    except asyncio.TimeoutError:
                        logger.warning("Timeout waiting for task to stop, forcing shutdown")
                        self.task.cancel()
                        try:
                            await self.task
                        except asyncio.CancelledError:
                            pass

                await self._cleanup()
                self._update_status("stopped")
                logger.info("Smart meter manager stopped successfully")
            except Exception as e:
                logger.error(f"Error during shutdown: {str(e)}")
                raise
            finally:
                self._stopping = False

    async def _cleanup(self) -> None:
        """Clean up resources."""
        await self._disconnect_mqtt()
        self.task = None
        self._reconnect_task = None
        self.running = False

    def _handle_task_done(self, future: asyncio.Future) -> None:
        """Handle completion of the main task."""
        try:
            future.result()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Task ended with error: {str(e)}")
            self._update_status("error")

    @log
    async def restart(self) -> None:
        """Restart the Smart Meter Manager."""
        async with self._lock:
            await self.stop()
            await asyncio.sleep(1)  # Brief pause before restart
            await self.start()

    @log
    async def check_and_restart(self) -> None:
        """Check manager status and restart if necessary."""
        if self.status == "running" and not self.is_running:
            logger.warning("Smart Meter Manager should be running but isn't. Attempting to restart...")
            await self.start()

    @log
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
    async def _disconnect_mqtt(self) -> None:
        """Disconnect from MQTT broker."""
        if self.mqtt_client:
            try:
                await self.mqtt_client.disconnect()
            except Exception as e:
                logger.error(f"Error disconnecting from MQTT broker: {str(e)}")
            finally:
                self.mqtt_client = None

    @log
    async def _read_and_send_loop(self) -> None:
        """Main loop for reading and sending data."""
        while self.running and not self._stopping:
            try:
                await self._read_and_send_data()
                await asyncio.sleep(self.read_interval)
            except asyncio.CancelledError:
                logger.info("Read and send loop cancelled")
                break
            except SmartMeterReadError as e:
                logger.error(f"Error reading smart meter data: {str(e)}")
                if not self._stopping:
                    await asyncio.sleep(self.reconnect_interval)
            except MQTTConnectionError:
                if not self._stopping:
                    await self._handle_mqtt_connection_error()
            except Exception as e:
                logger.error(f"Unexpected error in read and send loop: {str(e)}")
                if not self._stopping:
                    await asyncio.sleep(self.reconnect_interval)

    @log
    async def _read_and_send_data(self) -> None:
        """Read data from smart meter and send via MQTT."""
        try:
            data = self.smart_meter.read_meter_data()
            if data:
                await self._send_mqtt(data)
        except Exception as e:
            raise SmartMeterReadError(f"Failed to read or send meter data: {str(e)}")

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

    @log
    async def _handle_mqtt_connection_error(self) -> None:
        """Handle MQTT connection errors with reconnection logic."""
        if self._stopping:
            return

        logger.error("Lost connection to MQTT broker. Attempting to reconnect...")
        try:
            await self._disconnect_mqtt()
            self._reconnect_task = asyncio.create_task(self._connect_mqtt())
            await self._reconnect_task
        except MQTTConnectionError as e:
            logger.error(f"Failed to reconnect to MQTT broker: {str(e)}")
            if not self._stopping:
                await asyncio.sleep(self.reconnect_interval)

    def _update_status(self, new_status: str) -> None:
        """Update and persist the manager's status."""
        self.status = new_status
        try:
            save_config(config.metadata_config_path, {"status": self.status})
        except Exception as e:
            logger.error(f"Failed to save status to config file: {str(e)}")

    def _handle_startup_error(self, error_message: str) -> None:
        """Handle errors during startup."""
        self.running = False
        self._update_status("error")
        logger.error(f"Failed to start Smart Meter Manager: {error_message}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to start Smart Meter Manager: {error_message}",
        )


_manager_instance: Optional[SmartMeterManager] = None


def get_smart_meter_manager() -> SmartMeterManager:
    """Get or create singleton instance of SmartMeterManager."""
    smart_meter_config = load_config(config.path_to_smart_meter_config)
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = SmartMeterManager(smart_meter_config)
    return _manager_instance


router = APIRouter(
    prefix="/smart_meter",
    tags=["smart_meter"],
    responses={
        404: {"description": "Not found"},
        503: {"description": "Service unavailable"},
        400: {"description": "Bad request"},
    },
)


@router.get("/start", response_model=Dict[str, str])
async def start_smart_meter(
    manager: SmartMeterManager = Depends(get_smart_meter_manager),
):
    """Start the smart meter manager."""
    if is_not_connected(config.trust_wallet_port):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Wallet not connected")
    await manager.start()
    return {"status": manager.status}


@router.get("/stop", response_model=Dict[str, str])
async def stop_smart_meter(
    manager: SmartMeterManager = Depends(get_smart_meter_manager),
):
    """Stop the smart meter manager."""
    await manager.stop()
    return {"status": manager.status}


@router.get("/status", response_model=Dict[str, str])
async def smart_meter_status(
    manager: SmartMeterManager = Depends(get_smart_meter_manager),
):
    """Get the current status of the smart meter manager."""
    return {"status": manager.status}


@router.get("/restart", response_model=Dict[str, str])
async def restart_smart_meter(
    manager: SmartMeterManager = Depends(get_smart_meter_manager),
):
    """Restart the smart meter manager."""
    if is_not_connected(config.trust_wallet_port):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Wallet not connected")
    await manager.restart()
    return {"status": manager.status}
