import json
from datetime import datetime
import time
import asyncio
from gmqtt import Client as MQTTClient
from gmqtt import Message
from gmqtt.mqtt.constants import MQTTv311

from app.RddlInteraction.cid_tool import store_cid
from app.RddlInteraction.planetmint_interaction import create_tx_notarize_data
from app.dependencies import config, logger
from app.energy_agent.energy_decrypter import decrypt_device
from app.helpers.config_helper import load_config
from app.helpers.models import MQTTConfig
from app.dependencies import trust_wallet_instance


class RDDLAgent:
    def __init__(self):
        self.client = None
        self.mqtt_config = MQTTConfig()
        self.stopped = False
        self.data_buffer = []
        self.max_buffer_size = 3000
        self.retry_attempts = 3
        self.mqtt_config.mqtt_username = config.rddl_mqtt_user
        self.mqtt_config.mqtt_password = config.rddl_mqtt_password
        self.mqtt_config.mqtt_host = config.rddl_mqtt_server
        self.mqtt_config.mqtt_port = config.rddl_mqtt_port

    def setup(self):
        try:
            self.initialize_mqtt_client()
        except Exception as e:
            logger.error(f"MQTT RDDL Setup error: {e}")
            raise

    def initialize_mqtt_client(self):
        keys = trust_wallet_instance.get_planetmint_keys()
        self.client = MQTTClient(client_id=keys.planetmint_address)
        self.client.on_message = self.on_message
        self.client.set_auth_credentials(self.mqtt_config.mqtt_username, self.mqtt_config.mqtt_password)

    async def connect_to_mqtt(self):
        try:
            await self.client.connect(
                self.mqtt_config.mqtt_host, self.mqtt_config.mqtt_port, keepalive=60, version=MQTTv311, ssl=True
            )
        except Exception as e:
            logger.error(f"MQTT RDDL connection error: {e}")
            raise

    async def disconnect_from_mqtt(self):
        try:
            await self.client.disconnect()
        except Exception as e:
            logger.error(f"MQTT RDDL disconnection error: {e}")

    async def on_message(self, client, topic, payload, qos, properties):
        try:
            decoded_payload = payload.decode()
            self.process_message(topic, decoded_payload)
            logger.info(f"MQTT RDDL Received message: {topic}, {decoded_payload}")
        except UnicodeDecodeError:
            logger.error("MQTT RDDL Error decoding the message payload")
        except Exception as e:
            logger.error(f"MQTT RDDL Unexpected error processing message: {e}")

    def process_message(self, topic, data):
        notarize_data = data
        self.data_buffer.append(notarize_data)
        if len(self.data_buffer) >= self.max_buffer_size:
            logger.info("MQTT RDDL Buffer size limit reached. Initiating immediate notarization.")
            asyncio.create_task(self.notarize_data())

    async def notarize_data(self):
        attempts = 0
        while attempts < self.retry_attempts:
            try:
                data = json.dumps(self.data_buffer)
                notarize_cid = store_cid(data)
                logger.debug(f"MQTT RDDL Notarize CID transaction: {notarize_cid}, {data}")
                planetmint_keys = trust_wallet_instance.get_planetmint_keys()
                planetmint_tx = create_tx_notarize_data(notarize_cid, planetmint_keys.planetmint_address)
                logger.info(f"MQTT RDDL lanetmint transaction: {planetmint_tx}")
                self.data_buffer.clear()
                break
            except Exception as e:
                attempts += 1
                logger.error(
                    f"MQTT RDDL Error occurred while notarizing data, attempt {attempts}/{self.retry_attempts}: {e}"
                )
                if attempts >= self.retry_attempts:
                    logger.error("MQTT RDDL Max retry attempts reached. Data notarization failed.")

    async def notarize_data_with_interval(self):
        while not self.stopped:
            logger.debug(f"MQTT RDDL Data buffer: {self.data_buffer}")
            if self.data_buffer:
                await self.notarize_data()
            else:
                logger.debug("MQTT RDDL No data to notarize")
            await asyncio.sleep(config.notarize_interval * 60)

    async def run(self):
        try:
            await self.connect_to_mqtt()
            planetmint_keys = trust_wallet_instance.get_planetmint_keys()

            self.client.subscribe("cmnd/" + planetmint_keys.planetmint_address + "/PoPChallenge")
            self.client.subscribe("cmnd/" + planetmint_keys.planetmint_address + "/PoPInit")

            self.client.subscribe(config.rddl_topic)

            while not self.stopped:
                await self.postStatus(planetmint_keys.planetmint_address)
                await asyncio.sleep(60)
                

        except Exception as e:
            logger.error(f"MQTT RDDL Error in RDDLAgent run loop: {e}")
        finally:
            await self.disconnect_from_mqtt()

    async def postStatus(self, address: str):
        topic = "tele/"+ address + "/STATE"
        payload = "{\"Time\": \"" +str(datetime.now())+ "\" }"
        msg = Message(topic, payload, qos=1, content_type="json",
                            message_expiry_interval=300, user_property=("time", str(datetime.now())))
        self.client.publish(msg)
