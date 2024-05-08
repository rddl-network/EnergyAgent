import json
import asyncio
from gmqtt import Client as MQTTClient
from gmqtt.mqtt.constants import MQTTv311

from app.RddlInteraction.cid_tool import store_cid
from app.RddlInteraction.planetmint_interaction import create_tx_notarize_data
from app.dependencies import config, logger
from app.energy_agent.energy_decrypter import decrypt_device
from app.helpers.config_helper import load_config
from app.helpers.models import SmartMeterConfig, MQTTConfig
from app.routers.trust_wallet_interaction import trust_wallet


class DataAgent:
    def __init__(self):
        self.client = None
        self.smart_meter_topic = ""
        self.mqtt_config = MQTTConfig()
        self.stopped = False
        self.data_buffer = []

    def setup(self):
        self.update_mqtt_connection_params()
        self.update_smart_meter_topic()
        self.initialize_mqtt_client()

    def initialize_mqtt_client(self):
        self.client = MQTTClient(client_id=config.client_id)
        self.client.on_message = self.on_message
        self.client.set_auth_credentials(self.mqtt_config.mqtt_username, self.mqtt_config.mqtt_password)

    async def connect_to_mqtt(self):
        await self.client.connect(
            self.mqtt_config.mqtt_host, self.mqtt_config.mqtt_port, keepalive=60, version=MQTTv311
        )

    async def disconnect_from_mqtt(self):
        await self.client.disconnect()

    async def on_message(self, client, topic, payload, qos, properties):
        try:
            self.process_message(topic, payload.decode())
            logger.info(f"Received message: {topic}, {payload.decode()}")
        except Exception as e:
            logger.error(f"Error occurred while processing message: {e}")

    def process_message(self, topic, data):
        notarize_data = data
        if self.smart_meter_topic == topic:
            notarize_data = self.process_meter_data(data)
        self.data_buffer.append(notarize_data)

    async def notarize_data(self):
        try:
            data = json.dumps(self.data_buffer)
            notarize_cid = store_cid(data)
            logger.debug(f"notarize CID planetmint transaction {notarize_cid}, {data}")
            planetmint_keys = trust_wallet.get_planetmint_keys()
            planetmint_tx = create_tx_notarize_data(notarize_cid, planetmint_keys.planetmint_address)
            logger.info(f"Planetmint transaction: {planetmint_tx}")
            self.data_buffer.clear()
        except Exception as e:
            logger.error(f"Error occurred while notarizing data: {e}")

    async def notarize_data_with_interval(self):
        while not self.stopped:
            logger.debug(f"Data buffer: {self.data_buffer}")  # Log the contents of the data buffer
            if self.data_buffer:
                logger.debug("Data to notarize")
                await self.notarize_data()
            else:
                logger.debug("No data to notarize")
                await asyncio.sleep(config.notarize_interval * 60)

    def update_mqtt_connection_params(self):
        mqtt_config_dict = load_config(config.path_to_mqtt_config)
        mqtt_config_obj = MQTTConfig.parse_obj(mqtt_config_dict)
        self.mqtt_config = mqtt_config_obj

    def update_smart_meter_topic(self):
        smart_meter_topic_dict = load_config(config.path_to_topic_config)
        sm_topic = SmartMeterConfig.parse_obj(smart_meter_topic_dict)
        self.smart_meter_topic = sm_topic.smart_meter_topic

    def process_meter_data(self, data):
        metric = decrypt_device(data)
        metric_dict = self.enrich_metric(metric)
        return json.dumps(metric_dict)

    @staticmethod
    def enrich_metric(data):
        metric_dict = data
        metric_dict["time_stamp"] = metric_dict["time_stamp"].isoformat()
        metric_dict["absolute_energy_in"] = float(metric_dict["absolute_energy_in"])
        metric_dict["absolute_energy_out"] = float(metric_dict["absolute_energy_out"])
        logger.debug(f"Metric data: {metric_dict}")
        return metric_dict

    async def run(self):
        await self.connect_to_mqtt()
        self.client.subscribe(config.rddl_topic)
        await self.notarize_data_with_interval()
