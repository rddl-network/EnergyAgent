import json
import paho.mqtt.client as mqtt
from app.RddlInteraction.cid_tool import store_cid
from app.RddlInteraction.planetmint_interaction import create_tx_notarize_data
from app.dependencies import config, logger
from app.energy_agent.energy_decrypter import decrypt_device
from app.helpers.config_helper import load_config
from app.helpers.models import TopicConfig, SmartMeterConfig, MQTTConfig
from app.routers.trust_wallet_interaction import trust_wallet

SM_READ_ERROR = "ERROR! SM METER READ"
DEFAULT_SLEEP_TIME = 5
MQTT_KEEP_ALIVE = 60


class DataAgent:
    def __init__(self):
        self.data_mqtt_client = None
        self.smart_meter_topic: str = ""
        self.mqtt_config: MQTTConfig = MQTTConfig()
        self.stopped: bool = False

    def setup(self):
        self.update_mqtt_connection_params()
        self.update_smart_meter_topic()

    def on_message(self, client, userdata, message):
        try:
            self.process_message(message)
        except Exception as e:
            logger.error(f"Error occurred while processing message: {e}")

    def process_message(self, message):
        topic = message.topic
        data = message.payload.decode()

        notarize_data = data
        if self.smart_meter_topic == topic:
            notarize_data = self.process_meter_data(data)
        notarize_cid = store_cid(data)
        logger.debug(f"notarize CID planetmint transaction {notarize_cid}, {notarize_data}")
        planetmint_keys = trust_wallet.get_planetmint_keys()
        planetmint_tx = create_tx_notarize_data(notarize_cid, planetmint_keys.planetmint_address)
        logger.info(f"Planetmint transaction: {planetmint_tx}")

    def update_mqtt_connection_params(self):
        topic_config_dict = load_config(config.path_to_mqtt_config)
        topic_config = MQTTConfig.parse_obj(topic_config_dict)
        self.mqtt_config = topic_config

    def update_smart_meter_topic(self):
        smart_meter_topic_dict = load_config(config.path_to_topic_config)
        sm_topic = SmartMeterConfig.parse_obj(smart_meter_topic_dict)
        self.smart_meter_topic = sm_topic.smart_meter_topic

    def process_meter_data(self, data) -> str:
        metric = decrypt_device(data)
        metric_dict = self.enrich_metric(metric)
        data = json.dumps(metric_dict)
        return data

    def connect_to_mqtt(self):

        self.initialize_mqtt_client()
        try:
            self.connect_client()
        except Exception as e:
            logger.error(f"Exception occurred while connecting to MQTT: {e}")
            self.data_mqtt_client.reconnect()

    def initialize_mqtt_client(self):
        self.data_mqtt_client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id=config.pubkey, protocol=mqtt.MQTTv5
        )
        self.data_mqtt_client.on_message = self.on_message
        self.data_mqtt_client.username_pw_set(self.mqtt_config.mqtt_username, self.mqtt_config.mqtt_password)

    def connect_client(self):
        self.data_mqtt_client.connect(self.mqtt_config.mqtt_host, self.mqtt_config.mqtt_port, MQTT_KEEP_ALIVE)
        self.data_mqtt_client.subscribe(config.rddl_topic)
        self.data_mqtt_client.loop_start()  # Start the network loop

    def enrich_metric(self, data: dict) -> dict:
        metric_dict = data
        metric_dict["time_stamp"] = metric_dict["time_stamp"].isoformat()
        metric_dict["absolute_energy_in"] = float(metric_dict["absolute_energy_in"])
        metric_dict["absolute_energy_out"] = float(metric_dict["absolute_energy_out"])
        logger.debug(f"Metric data: {metric_dict}")
        return metric_dict

    def on_connect(self, userdata, flags, rc):
        logger.debug(f"Connected to MQTT Broker with result code {rc}")

    def on_disconnect(self, client, userdata, rc):
        logger.debug("Disconnected from MQTT Broker")
