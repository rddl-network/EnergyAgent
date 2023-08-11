import grpc
import json
import pika
import time
from app.dependencies import config, logger
from app.energy_meter_interaction.energy_decrypter import (
    extract_data,
    decode_packet,
    decrypt_evn_data,
    transform_to_metrics,
    decrypt_aes_gcm_landis_and_gyr,
)
from app.proto.MeterConnectorProto import meter_connector_pb2_grpc, meter_connector_pb2
from submoudles.submodules.app_mypower_modul.schemas import MetricCreate


SM_READ_ERROR = "ERROR! SM METER READ"

class DataFetcher:
    def __init__(self):
        self.stopped = False

    def fetch_data(self):
        logger.info("start fetching")
        while not self.stopped:
            time.sleep(config.interval)
            try:
                print(f"grpc_endpoint: {config.grpc_endpoint}")
                channel = grpc.insecure_channel(config.grpc_endpoint)
                stub = meter_connector_pb2_grpc.MeterConnectorStub(channel)
                request = meter_connector_pb2.SMDataRequest()
                response = stub.readMeter(request)
                if response.message == SM_READ_ERROR:
                    logger.error("No data from Smart Meter")
                    continue
                data_hex = response.message
                print(f"data_hex: {data_hex}")
                metric = self.decrypt_device(data_hex)
                self.post_to_rabbitmq(metric)
            except ValueError as e:
                logger.exception(f"DataFetcher thread failed with exception: {e.args[0]}")
                continue

    @staticmethod
    def decrypt_device(data_hex):
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
                logger.error("data is None")
                raise ValueError("data is None")
            return metric

    @staticmethod
    def post_to_rabbitmq(data: MetricCreate):
        logger.info("Posting to RabbitMQ")

        metric_dict = data.dict()
        metric_dict["time_stamp"] = metric_dict["time_stamp"].isoformat()
        metric_dict["absolute_energy_in"] = float(metric_dict["absolute_energy_in"])
        metric_dict["absolute_energy_out"] = float(metric_dict["absolute_energy_out"])
        logger.debug(f"Metric data: {metric_dict}")

        message = json.dumps(metric_dict)

        try:
            with pika.BlockingConnection(pika.URLParameters(config.amqp_url)) as connection:
                channel = connection.channel()
                channel.basic_publish(
                    exchange='',
                    routing_key=config.queue_name,
                    body=message.encode(),
                    properties=pika.BasicProperties(content_type="application/json")
                )
                logger.info(f" [x] Sent {message}")
        except Exception as e:
            logger.error(f"Exception occurred: {e}")
