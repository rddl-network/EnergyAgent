import logging
import os


class Config:
    def __init__(self):
        self.grpc_host = os.environ.get("GRPC_HOST") or "192.168.68.68"
        self.grpc_port = os.environ.get("GRPC_PORT") or "50051"
        self.device = os.environ.get("DEVICE") or "WN"
        self.selection = os.environ.get("SELECTION") or "mock"
        self.verify_signature = bool(os.environ.get("VERIFY_SIGNATURE")) or False
        self.interval = int(os.environ.get("INTERVAL") or "15")
        self.thing_id = os.environ.get("THING_ID") or "st-energy-meter"
        self.pubkey = os.environ.get("PUBKEY") or "st-energy-meter"
        self.mqtt_host = os.environ.get("MQTT_HOST") or "app-rabbitmq-dev.r3c.network"
        self.mqtt_port: int = os.environ.get("MQTT_PORT") or 1893
        self.mqtt_password = os.environ.get("MQTT_PASSWORD") or "cYBgEh8Gk6G9qqcKzEPr"
        self.mqtt_username = os.environ.get("MQTT_USERNAME") or "stanz"
        self.mqtt_topic = os.environ.get("MQTT_TOPIC") or "metrics"
        self.log_level = os.environ.get("LOG_LEVEL") or "INFO"

        self.evn_key = os.environ.get("EVN_KEY") or None
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
