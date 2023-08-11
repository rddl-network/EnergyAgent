import logging
import os
from contextlib import contextmanager


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
        self.rabbitmq_host = os.environ.get("RABBITMQ_HOST") or "rabbitmq"
        self.queue_name = os.environ.get("QUEUE_NAME") or "metrics"
        self.exchange_name = os.environ.get("EXCHANGE_NAME") or ""
        self.rabbitmq_port = os.environ.get("RABBITMQ_PORT") or "5672"
        self.rabbitmq_password = os.environ.get("RABBITMQ_PASSWORD") or ""
        self.rabbitmq_username = os.environ.get("RABBITMQ_USERNAME") or ""
        self.amqp_url = (
            f"amqp://{self.rabbitmq_username}:{self.rabbitmq_password}@{self.rabbitmq_host}:{self.rabbitmq_port}/"
        )
        self.log_level = os.environ.get("LOG_LEVEL") or "INFO"

        self.evn_key = os.environ.get("EVN_KEY") or None
        self.lg_encryption_key = os.environ.get("LG_ENCRYPTION_KEY") or None
        self.lg_authentication_key = os.environ.get("LG_AUTH_KEY") or None

        # build the database url
        self.grpc_endpoint = f"{self.grpc_host}:{self.grpc_port}"


config = Config()

logging.basicConfig(level=config.log_level, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
