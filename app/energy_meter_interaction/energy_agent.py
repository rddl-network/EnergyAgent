import json
import paho.mqtt.client as mqtt
from ipfs_cid import cid_sha256_hash

from app.RddlInteraction.cid_tool import store_cid
from app.db.cid_store import insert_key_value
from app.dependencies import config, logger
from app.energy_meter_interaction.energy_decrypter import (
    transform_to_metrics,
    decrypt_aes_gcm_landis_and_gyr,
    decrypt_sagemcom,
    decrypt_evn_data,
)
from app.helpers.config_helper import load_config
from app.helpers.models import TopicConfig

SM_READ_ERROR = "ERROR! SM METER READ"
DEFAULT_SLEEP_TIME = 5


class DataAgent:
    def __init__(self):
        self.data_mqtt_client = None
        self.data_mqtt_topics = None
        self.sm_meter_topic = None
        self.stopped = False

    def on_message(self, client, userdata, message):
        try:
            topic = message.topic
            data = message.payload.decode()

            topic_config_dict = load_config(config.path_to_topic_config)
            topic_config = TopicConfig.parse_obj(topic_config_dict)

            if topic_config.contains(topic):
                cid = store_cid(data)
                print(f"notarize CID planetmint transaction {cid}")
            elif topic == self.sm_meter_topic:
                metric = self.decrypt_device(data)
                metric_dict = self.enricht_metric(metric)
                cid = store_cid(json.dumps(metric_dict))
                print(f"notarize SM data cid on planetmint {cid}")
        except Exception as e:
            logger.error(f"Error occurred while processing message: {e}")

    def connect_to_mqtt(self):
        # Subscriber MQTT client
        # TODO: check if newer version of paho-mqtt works? callback_api_version=mqtt.CallbackAPIVersion.VERSION2 is new in old version 1.6.1 it was not needed
        # TODO: Also check if code compiles on raspberrypi!
        self.data_mqtt_client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id=config.pubkey, protocol=mqtt.MQTTv5
        )
        self.data_mqtt_client.on_message = self.on_message
        self.data_mqtt_client.username_pw_set(config.data_mqtt_username, config.data_mqtt_password)

        try:
            self.data_mqtt_client.connect(config.data_mqtt_host, config.data_mqtt_port, 60)
            self.data_mqtt_client.subscribe(self.data_mqtt_topics)
            self.data_mqtt_client.loop_start()  # Start the network loop
        except Exception as e:
            logger.error(f"Exception occurred while connecting to MQTT: {e}")
            self.data_mqtt_client.reconnect()

    @staticmethod
    def decrypt_device(data_hex):
        if config.device_type == "LG":
            dec = decrypt_aes_gcm_landis_and_gyr(
                data_hex, bytes.fromhex(config.encryption_key), bytes.fromhex(config.authentication_key)
            )
            return transform_to_metrics(dec, config.pubkey)
        elif config.device_type == "SC":
            dec = decrypt_sagemcom(
                data_hex, bytes.fromhex(config.encryption_key), bytes.fromhex(config.authentication_key)
            )
            return transform_to_metrics(dec, config.pubkey)
        elif config.device == "EVN":
            dec = decrypt_evn_data(data_hex)
            return transform_to_metrics(dec, config.pubkey)
        else:
            logger.error(f"Unknown device: {config.device_type}")

    def enricht_metric(self, data: dict) -> dict:
        metric_dict = data
        metric_dict["time_stamp"] = metric_dict["time_stamp"].isoformat()
        metric_dict["absolute_energy_in"] = float(metric_dict["absolute_energy_in"])
        metric_dict["absolute_energy_out"] = float(metric_dict["absolute_energy_out"])
        logger.debug(f"Metric data: {metric_dict}")
        return metric_dict

    def on_connect(self, client, userdata, flags, rc):
        logger.info(f"Connected to MQTT Broker with result code {rc}")

    def on_disconnect(self, client, userdata, rc):
        logger.info("Disconnected from MQTT Broker")
