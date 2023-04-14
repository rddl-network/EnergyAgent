import asyncio
import threading
import time
from typing import Optional

import grpc
from decimal import Decimal

from app.dependencies import config, get_db, db_context
from app.energy_meter_interaction.energy_decrypter import extract_data, decode_packet
from app.energy_meter_interaction.energy_meter_data import MeterData
from app.proto.MeterConnectorProto import meter_connector_pb2_grpc, meter_connector_pb2
from app.schemas import Thing

from submodules.app_mypower_model.controller import time_series_data as time_series_data_controller
from submodules.app_mypower_model.dblayer import save_thing, fetch_thing_by_thing_id, save_time_series_data

import sys
import logging


class DataFetcher:
    def __init__(self):
        self.stopped = False
        self.thing_id = None
        self.logger = logging.getLogger(__name__)

    async def fetch_data(self):
        with db_context() as db:
            if config.thing_id:
                self.logger.info("fetching thing %s", config.thing_id)
                fetched_thing = await fetch_thing_by_thing_id(db, config.thing_id)
                if not fetched_thing:
                    self.logger.info("thing does not exists")
                    saved_thing = await save_thing(db, config.thing_id, "engergy-meter", None)
                    self.thing_id = saved_thing.id
                else:
                    self.logger.info("thing exists")
                    self.thing_id = fetched_thing.id

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

    async def save_time_series_data(self, data: MeterData):
        with db_context() as db:
            absolute_energy = data.energy_delivered - data.energy_consumed
            return await save_time_series_data(
                db, self.thing_id, Decimal(absolute_energy), "kwh", data.timestamp, None
            )
