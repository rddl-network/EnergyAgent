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

        # build the database url
        self.grpc_endpoint = f"{self.grpc_host}:{self.grpc_port}"


config = Config()
