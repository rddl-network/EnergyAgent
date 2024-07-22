import json
import asyncio
import threading

from gmqtt import Client as MQTTClient
from gmqtt.mqtt.constants import MQTTv311

from app.RddlInteraction.cid_tool import store_cid
from app.RddlInteraction.planetmint_interaction import create_tx_notarize_data
from app.db.tx_store import insert_tx
from app.dependencies import config, trust_wallet_instance
from app.energy_agent.energy_decrypter import decrypt_device
from app.helpers.config_helper import load_config, extract_client_id
from app.helpers.models import MQTTConfig
from app.helpers.smd_entry_helper import process_data_buffer
from app.helpers.logs import log, logger


class EnergyAgent:
    def __init__(self):
        logger.info("MQTT Energy Agent setup")
        self.client = None
        self.smart_meter_topic = ""
        self.mqtt_config = MQTTConfig()
        self.stopped = False
        self.data_buffer = []
        self.max_buffer_size = 10000
        self.retry_attempts = 6
        self.lock = threading.Lock()

    @log
    def setup(self):
        try:
            self.update_mqtt_connection_params()
            self.initialize_mqtt_client()
        except Exception as e:
            logger.error(f"Setup error: {e}")
            raise

    @log
    def initialize_mqtt_client(self):
        keys = trust_wallet_instance.get_planetmint_keys()
        self.client = MQTTClient(client_id=keys.planetmint_address)
        self.client.on_message = self.on_message
        self.client.set_auth_credentials(self.mqtt_config.username, self.mqtt_config.password)

    @log
    async def connect_to_mqtt(self):
        try:
            await self.client.connect(self.mqtt_config.host, self.mqtt_config.port, keepalive=60, version=MQTTv311)
        except Exception as e:
            logger.error(f"MQTT connection error: {e}")
            raise

    @log
    async def disconnect_from_mqtt(self):
        try:
            await self.client.disconnect()
        except Exception as e:
            logger.error(f"MQTT disconnection error: {e}")

    @log
    def on_message(self, client, topic, payload, qos, properties):
        try:
            decoded_payload = payload.decode()
            asyncio.create_task(self.process_message(topic, decoded_payload))
            logger.info(f"Received message: {topic}, {decoded_payload}")
        except UnicodeDecodeError:
            logger.error("Error decoding the message payload")
        except Exception as e:
            logger.error(f"Unexpected error processing message: {e}")

    @log
    async def process_message(self, topic: str, data: str):
        client_id: str = extract_client_id(topic)
        data_dict = {client_id: data}
        logger.debug(f"Data to be notarized: {data_dict}")
        with self.lock:
            self.data_buffer.append(data_dict)
        if len(self.data_buffer) >= self.max_buffer_size:
            logger.info("Buffer size limit reached. Initiating immediate notarization.")
            await self.notarize_data()

    @log
    async def notarize_data(self):
        attempts = 0
        while attempts < self.retry_attempts:
            try:
                with self.lock:
                    data = json.dumps(self.data_buffer)
                    notarize_cid = store_cid(data)
                    await process_data_buffer(self.data_buffer, notarize_cid)
                    logger.debug(f"Notarize CID transaction: {notarize_cid}, {data}")
                    tx_hash = create_tx_notarize_data(notarize_cid, config.rddl.planetmint_api, config.rddl.chain_id)
                    insert_tx(tx_hash, notarize_cid)
                    logger.info(f"Planetmint transaction response: {tx_hash}")
                    self.data_buffer.clear()
                break
            except Exception as e:
                attempts += 1
                await asyncio.sleep(300)
                logger.error(f"Error occurred while notarizing data, attempt {attempts}/{self.retry_attempts}: {e}")
                if attempts >= self.retry_attempts:
                    logger.error("Max retry attempts reached. Data notarization failed.")
                    raise Exception("Data notarization failed")

    @log
    async def notarize_data_with_interval(self):
        while not self.stopped:
            logger.debug(f"Data buffer: {self.data_buffer}")
            if self.data_buffer:
                await self.notarize_data()
            else:
                logger.debug("No data to notarize")
            await asyncio.sleep(config.notarize_interval * 60)

    @log
    def update_mqtt_connection_params(self):
        try:
            mqtt_config_dict = load_config(config.path_to_mqtt_config)
            self.mqtt_config = MQTTConfig.model_validate(mqtt_config_dict)
        except Exception as e:
            logger.error(f"Error loading MQTT configuration: {e}")
            raise

    @log
    def process_meter_data(self, data):
        try:
            metric = decrypt_device(data)
            metric_dict = self.enrich_metric(metric)
            return json.dumps(metric_dict)
        except Exception as e:
            logger.error(f"Error processing meter data: {e}")
            raise

    @staticmethod
    @log
    def enrich_metric(data):
        metric_dict = data
        try:
            metric_dict["time_stamp"] = metric_dict["time_stamp"].isoformat()
            metric_dict["absolute_energy_in"] = float(metric_dict["absolute_energy_in"])
            metric_dict["absolute_energy_out"] = float(metric_dict["absolute_energy_out"])
            logger.debug(f"Metric data: {metric_dict}")
        except KeyError as e:
            logger.error(f"Key missing in metric data: {e}")
        except ValueError as e:
            logger.error(f"Data conversion error in metric: {e}")
        return metric_dict

    @log
    async def run(self):
        notarization_task = None
        try:
            await self.connect_to_mqtt()
            self.client.subscribe(config.smd_topic)
            notarization_task = asyncio.create_task(self.notarize_data_with_interval())

            while not self.stopped:
                await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Error in DataAgent run loop: {e}")
            raise
        finally:
            await self.disconnect_from_mqtt()
            if notarization_task:
                notarization_task.cancel()
