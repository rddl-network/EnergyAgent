import logging
import os





class Config:
    def __init__(self):
        # general config
        self.log_level = os.environ.get("LOG_LEVEL") or "INFO"
        self.pubkey = os.environ.get("PUBKEY") or "st-energy-meter"
        self.path_to_topic_config = os.environ.get("PATH_TO_TOPIC_CONFIG") or "topic_config.json"

        # Forwarder MQTT Config
        self.forwarder_mqtt_host = os.environ.get("MQTT_HOST") or "app-rabbitmq-dev.r3c.network"
        self.forwarder_mqtt_port: int = int(os.environ.get("MQTT_PORT") or 1893)
        self.forwarder_mqtt_password = os.environ.get("MQTT_PASSWORD") or "cYBgEh8Gk6G9qqcKzEPr"
        self.forwarder_mqtt_username = os.environ.get("MQTT_USERNAME") or "stanz"
        self.forwarder_mqtt_topic = os.environ.get("MQTT_TOPIC") or "metrics"

        # Data MQTT Config
        self.data_mqtt_host = os.environ.get("MQTT_HOST") or "mqtt"
        self.data_mqtt_port: int = int(os.environ.get("MQTT_PORT") or 1893)
        self.data_mqtt_password = os.environ.get("MQTT_PASSWORD") or ""
        self.data_mqtt_username = os.environ.get("MQTT_USERNAME") or ""
        self.data_mqtt_topic = os.environ.get("MQTT_TOPIC") or ""

        # Smart Meter Config
        self.device = os.environ.get("DEVICE") or "WN"
        self.encryption_key = os.environ.get("ENCRYPTION_KEY") or None
        self.authentication_key = os.environ.get("AUTH_KEY") or None
        self.path_smart_meter_config = os.environ.get("PATH_SMART_METER_CONFIG") or "smart_meter_config.json"


config = Config()


numeric_level = getattr(logging, config.log_level.upper(), None)
if not isinstance(numeric_level, int):
    raise ValueError(f"Invalid log level: {config.log_level}")
logging.basicConfig(level=numeric_level)

logger = logging.getLogger(__name__)
