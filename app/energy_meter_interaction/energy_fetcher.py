import asyncio
import grpc
import json
import pika
from decimal import Decimal
from pika.credentials import PlainCredentials

from app.dependencies import config
from app.energy_meter_interaction.energy_decrypter import extract_data, decode_packet
from app.energy_meter_interaction.energy_meter_data import MeterData
from app.proto.MeterConnectorProto import meter_connector_pb2_grpc, meter_connector_pb2

import logging


class DataFetcher:
    def __init__(self):
        self.stopped = False
        self.thing_id = None
        self.logger = logging.getLogger(__name__)

    async def fetch_data(self):
        self.logger.info("start fetching")
        try:
            while not self.stopped:
                print("grpc_endpoint: %s", config.grpc_endpoint)
                channel = grpc.insecure_channel(config.grpc_endpoint)
                stub = meter_connector_pb2_grpc.MeterConnectorStub(channel)
                request = meter_connector_pb2.SMDataRequest()
                response = stub.readMeter(request)
                data_hex = response.message
                print("data_hex: %s", data_hex)
                decoded_packet = decode_packet(bytearray.fromhex(data_hex))
                print("data_hex: %s", decoded_packet)
                data = extract_data(decode_packet(bytearray.fromhex(data_hex)))
                self.logger.info("data: %s", data)
                if data is None:
                    self.logger.error("data is None")
                    raise Exception("data is None")
                await self.post_to_rabbitmq(data)
                await asyncio.sleep(config.interval)
        except Exception as e:
            self.logger.exception("DataFetcher thread failed with exception: %s", str(e))

    @staticmethod
    async def post_to_rabbitmq(data: MeterData):
        parameters = pika.ConnectionParameters(
            host=config.rabbitmq_host,
            port=config.rabbitmq_port,
            login=config.rabbitmq_user,
            password=config.rabbitmq_password,
        )

        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()

        channel.queue_declare(queue=config.queue_name)

        if data.energy_delivered != 0:
            metric_value = Decimal(data.energy_delivered)
        else:
            metric_value = Decimal(data.energy_consumed * -1)

        message = {
            "pubkey": config.pubkey,
            "timestamp": data.timestamp,
            "value": str(metric_value),
            "type": "absolute_energy",
        }

        channel.basic_publish(exchange="", routing_key=config.queue_name, body=json.dumps(message))

        connection.close()
