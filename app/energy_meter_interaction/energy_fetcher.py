import asyncio
import threading
import time
from typing import Optional

import grpc
from decimal import Decimal

from app.dependencies import config, get_db
from app.energy_meter_interaction.energy_decrypter import extract_data, decode_packet
from app.energy_meter_interaction.energy_meter_data import MeterData
from app.proto.MeterConnectorProto import meter_connector_pb2_grpc, meter_connector_pb2
from app.schemas import Thing

from submodules.app_mypower_model.dblayer import save_thing, fetch_thing_by_thing_id, save_time_series_data


class DataFetcher:
    def __init__(self, interval: int):
        self.interval = interval
        self.data_hex = None
        self.data: Optional[MeterData] = None
        self.stopped = False
        self.thing_id = None

    async def fetch_data(self):
        if self.thing_id is None:
            thing: Thing
            db = get_db()
            fetched_thing = await fetch_thing_by_thing_id(db, config.thing_id)
            if fetched_thing:
                saved_thing = await save_thing(db, config.thing_id, "engergy-meter", None)
                self.thing_id = saved_thing.id
            else:
                self.thing_id = fetched_thing.id

        while not self.stopped:
            channel = grpc.insecure_channel(config.grpc_endpoint)
            stub = meter_connector_pb2_grpc.MeterConnectorStub(channel)
            request = meter_connector_pb2.SMDataRequest()
            response = stub.readMeter(request)
            self.data_hex = response.message
            self.data = extract_data(decode_packet(bytearray.fromhex(self.data_hex)))
            print("data_hex: ", self.data_hex)
            print("data: ", self.data)
            await self.save_time_series_data()
            await asyncio.sleep(self.interval)

    async def save_time_series_data(self):
        db = get_db()
        return await save_time_series_data(
            db, self.thing_id, Decimal(self.data.energy_delivered), "kwh", self.data.timestamp, None
        )

    def start(self):
        loop = asyncio.get_running_loop()
        asyncio.run_coroutine_threadsafe(self.fetch_data(), loop=loop)

    def stop(self):
        self.stopped = True
