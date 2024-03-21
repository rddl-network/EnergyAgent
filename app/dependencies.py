import logging
import os


class Config:
    def __init__(self):
        self.device = os.environ.get("DEVICE") or "WN"
        self.verify_signature = bool(os.environ.get("VERIFY_SIGNATURE")) or False
        self.interval = int(os.environ.get("INTERVAL") or "15")
        self.thing_id = os.environ.get("THING_ID") or "st-energy-meter"
        self.pubkey = os.environ.get("PUBKEY") or "st-energy-meter"
        self.forwarder_mqtt_host = os.environ.get("MQTT_HOST") or "app-rabbitmq-dev.r3c.network"
        self.forwarder_mqtt_port: int = int(os.environ.get("MQTT_PORT") or 1893)
        self.forwarder_mqtt_password = os.environ.get("MQTT_PASSWORD") or "cYBgEh8Gk6G9qqcKzEPr"
        self.forwarder_mqtt_username = os.environ.get("MQTT_USERNAME") or "stanz"
        self.forwarder_mqtt_topic = os.environ.get("MQTT_TOPIC") or "metrics"
        self.data_mqtt_host = os.environ.get("MQTT_HOST") or "app-rabbitmq-dev.r3c.network"
        self.data_mqtt_port: int = int(os.environ.get("MQTT_PORT") or 1893)
        self.data_mqtt_password = os.environ.get("MQTT_PASSWORD") or "cYBgEh8Gk6G9qqcKzEPr"
        self.data_mqtt_username = os.environ.get("MQTT_USERNAME") or "stanz"
        self.data_mqtt_topic = os.environ.get("MQTT_TOPIC") or "metrics"
        self.log_level = os.environ.get("LOG_LEVEL") or "INFO"

        self.encryption_key = os.environ.get("ENCRYPTION_KEY") or None
        self.authentication_key = os.environ.get("AUTH_KEY") or None

        # build the database url
        self.grpc_endpoint = f"{self.grpc_host}:{self.grpc_port}"


config = Config()


numeric_level = getattr(logging, config.log_level.upper(), None)
if not isinstance(numeric_level, int):
    raise ValueError(f"Invalid log level: {config.log_level}")
logging.basicConfig(level=numeric_level)

logger = logging.getLogger(__name__)
