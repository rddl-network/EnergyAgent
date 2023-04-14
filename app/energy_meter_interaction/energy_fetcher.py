import asyncio
import threading
import time
from typing import Optional

import grpc
from decimal import Decimal

from app.dependencies import config, db_context
from app.energy_meter_interaction.energy_decrypter import extract_data, decode_packet
from app.energy_meter_interaction.energy_meter_data import MeterData
from app.proto.MeterConnectorProto import meter_connector_pb2_grpc, meter_connector_pb2
from app.schemas import Thing

from submodules.app_mypower_model.dblayer import fetch_thing_by_public_key, save_metric

import sys
import logging


class DataFetcher:
    def __init__(self):
        self.stopped = False
        self.thing_id = None
        self.logger = logging.getLogger(__name__)

    async def fetch_data(self):
        self.logger.info("thing_id: %s", self.thing_id)
        self.logger.info("start fetching")
        try:
            while not self.stopped:
                channel = grpc.insecure_channel(config.grpc_endpoint)
                stub = meter_connector_pb2_grpc.MeterConnectorStub(channel)
                request = meter_connector_pb2.SMDataRequest()
                response = stub.readMeter(request)
                data_hex = response.message
                data = extract_data(decode_packet(bytearray.fromhex(data_hex)))
                self.logger.info("data_hex: %s", data_hex)
                self.logger.info("data: %s", data)
                await self.save_time_series_data(data)
                await asyncio.sleep(config.interval)
        except Exception as e:
            self.logger.exception("DataFetcher thread failed with exception: %s", str(e))

    @staticmethod
    async def save_time_series_data(data: MeterData):
        with db_context() as db:
            if data.energy_delivered != 0:
                return await save_metric(
                    db, config.pubkey, data.timestamp, Decimal(data.energy_delivered), "absolute_energy")

            return await save_metric(
                db, config.pubkey, data.timestamp, Decimal(data.energy_consumed), "absolute_energy_out")
