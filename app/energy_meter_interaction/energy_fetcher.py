import asyncio
import grpc
import json
from aio_pika import connect, Message
from pika.credentials import PlainCredentials

from app.dependencies import config
from app.energy_meter_interaction.energy_decrypter import (
    extract_data,
    decode_packet,
    decrypt_evn_data,
    transform_to_metrics,
)
from app.energy_meter_interaction.energy_meter_data import MeterData
from app.proto.MeterConnectorProto import meter_connector_pb2_grpc, meter_connector_pb2

import logging

from submoudles.submodules.app_mypower_modul.schemas import MetricCreate


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
                metric = await self.decrypt_device(data_hex)
                await self.post_to_rabbitmq(metric)
                await asyncio.sleep(config.interval)
        except Exception as e:
            self.logger.exception("DataFetcher thread failed with exception: %s", str(e))

    async def decrypt_device(self, data_hex):
        if config.device == "EVN":
            dec = decrypt_evn_data(data_hex)
            return transform_to_metrics(dec, config.pubkey)
        else:
            decoded_packet = decode_packet(bytearray.fromhex(data_hex))
            print("data_hex: %s", decoded_packet)
            metric = extract_data(decode_packet(bytearray.fromhex(data_hex)))
            self.logger.info("data: %s", metric)
            if metric is None:
                self.logger.error("data is None")
                raise Exception("data is None")
            return metric

    @staticmethod
    async def post_to_rabbitmq(data: MetricCreate):
        print("post_to_rabbitmq")
        metric_dict = data.dict()
        metric_dict["time_stamp"] = metric_dict["time_stamp"].isoformat()
        metric_dict["absolute_energy_in"] = float(metric_dict["absolute_energy_in"])
        metric_dict["absolute_energy_out"] = float(metric_dict["absolute_energy_out"])
        print(metric_dict)

        message = json.dumps(metric_dict)

        connection = await connect(
            config.amqp_url,
        )

        async with connection:
            channel = await connection.channel()

            queue = await channel.declare_queue(config.queue_name, auto_delete=True)

            await channel.default_exchange.publish(Message(body=message.encode()), routing_key=queue.name)

        print(" [x] Sent %r" % message)
