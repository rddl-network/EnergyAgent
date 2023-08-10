import asyncio
import grpc
import json
from aio_pika import connect, Message

from app.dependencies import config
from app.energy_meter_interaction.energy_decrypter import (
    extract_data,
    decode_packet,
    decrypt_evn_data,
    transform_to_metrics,
    decrypt_aes_gcm_landis_and_gyr,
)
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
        while not self.stopped:
            await asyncio.sleep(config.interval)
            try:
                print(f"grpc_endpoint: {config.grpc_endpoint}")
                channel = grpc.insecure_channel(config.grpc_endpoint)
                stub = meter_connector_pb2_grpc.MeterConnectorStub(channel)
                request = meter_connector_pb2.SMDataRequest()
                response = stub.readMeter(request)
                data_hex = response.message
                print(f"data_hex: {data_hex}")
                metric = await self.decrypt_device(data_hex)
                await self.post_to_rabbitmq(metric)
            except Exception as e:
                self.logger.exception(f"DataFetcher thread failed with exception: {e}")
                continue

    async def decrypt_device(self, data_hex):
        if config.device == "EVN":
            dec = decrypt_evn_data(data_hex)
            return transform_to_metrics(dec, config.pubkey)
        elif config.device == "LG":
            dec = decrypt_aes_gcm_landis_and_gyr(
                data_hex, bytes.fromhex(config.lg_encryption_key), bytes.fromhex(config.lg_authentication_key)
            )
            return transform_to_metrics(dec, config.pubkey)
        else:
            decoded_packet = decode_packet(bytearray.fromhex(data_hex))
            metric = extract_data(decoded_packet)
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
        print(f"Queue name: {config.queue_name}")

        message = json.dumps(metric_dict)

        try:
            connection = await connect(
                config.amqp_url,
            )

            async with connection:
                channel = await connection.channel()
                await channel.default_exchange.publish(
                    Message(body=message.encode(), content_type="application/json"), routing_key=config.queue_name
                )

            print(" [x] Sent %r" % message)
        except Exception as e:
            print(f"Exception occurred: {e}")
