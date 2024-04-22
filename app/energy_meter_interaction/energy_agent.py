import json
import paho.mqtt.client as mqtt

from app.dependencies import config, logger
from app.energy_meter_interaction.energy_decrypter import (
    transform_to_metrics,
    decrypt_aes_gcm_landis_and_gyr,
    decrypt_sagemcom,
    decrypt_evn_data,
)

SM_READ_ERROR = "ERROR! SM METER READ"
DEFAULT_SLEEP_TIME = 5


class DataAgent:
    def __init__(self):
        self.forwarder_mqtt_client = None
        self.data_mqtt_client = None
        self.stopped = False

    def on_message(self, client, userdata, message):
        topic = message.topic
        data = message.payload.decode()

        # TODO use actual sm topic
        if topic == "sm_meter_data":
            # Handle the message for the specific topic
            metric = self.decrypt_device(data)
            metric_dict = self.enricht_metric(metric)
            self.post_to_mqtt(metric_dict)
        else:
            self.post_to_mqtt(data)

    def connect_to_mqtt(self):
        # Forwarder MQTT client
        self.forwarder_mqtt_client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=config.pubkey,
            protocol=mqtt.MQTTv311,
        )
        self.forwarder_mqtt_client.on_connect = self.on_connect
        self.forwarder_mqtt_client.on_disconnect = self.on_disconnect
        self.forwarder_mqtt_client.on_publish = self.on_publish
        self.forwarder_mqtt_client.username_pw_set(config.forwarder_mqtt_username, config.forwarder_mqtt_password)

        # Subscriber MQTT client
        # TODO: check if newer version of paho-mqtt works? callback_api_version=mqtt.CallbackAPIVersion.VERSION2 is new in old version 1.6.1 it was not needed
        # TODO: Also check if code compiles on raspberrypi!
        self.data_mqtt_client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id=config.pubkey, protocol=mqtt.MQTTv5
        )
        self.data_mqtt_client.on_message = self.on_message
        self.data_mqtt_client.username_pw_set(config.data_mqtt_username, config.data_mqtt_password)

        try:
            # Connect to forwarder MQTT server
            self.forwarder_mqtt_client.connect(config.forwarder_mqtt_host, config.forwarder_mqtt_port, 60)
            self.forwarder_mqtt_client.loop_start()  # Start the network loop

            # Connect to subscriber MQTT server and subscribe to the topic
            self.data_mqtt_client.connect(config.data_mqtt_host, config.data_mqtt_port, 60)
            self.data_mqtt_client.subscribe(config.data_mqtt_topic)
            self.data_mqtt_client.loop_start()  # Start the network loop
        except Exception as e:
            logger.error(f"Exception occurred while connecting to MQTT: {e}")
            self.forwarder_mqtt_client.reconnect()
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

    def post_to_mqtt(self, data: dict):
        logger.info("Posting to MQTT")
        message = json.dumps(data)
        try:
            result = self.forwarder_mqtt_client.publish(config.forwarder_mqtt_topic, payload=message, qos=1)
            result.wait_for_publish()
            logger.info(f" [x] Sent {message}")
        except Exception as e:
            logger.error(f"Exception occurred while publishing to MQTT: {e}")
            self.handle_publish_failure(data)

    def handle_publish_failure(self, data):
        logger.warning("Attempting to republish to MQTT")
        self.forwarder_mqtt_client.reconnect()  # Attempt to reconnect
        self.post_to_mqtt(data)  # Try to republish the data

    def on_connect(self, client, userdata, flags, rc):
        logger.info(f"Connected to MQTT Broker with result code {rc}")

    def on_disconnect(self, client, userdata, rc):
        logger.info("Disconnected from MQTT Broker")

    def on_publish(self, client, userdata, mid):
        logger.info(f"Message with mid {mid} has been published.")
