import threading
import time
from typing import Optional

import grpc
from pydantic.types import Decimal

from app.dependencies import config, get_db
from app.energy_meter_interaction.energy_decrypter import extract_data, decode_packet
from app.energy_meter_interaction.energy_meter_data import MeterData
from app.proto.MeterConnectorProto import meter_connector_pb2_grpc, meter_connector_pb2

from submodules.app_mypower_model.controller import time_series_data as time_series_data_controller


class DataFetcher:
    def __init__(self, interval: int):
        self.interval = interval
        self.data_hex = None
        self.data: Optional[MeterData] = None
        self.stopped = False
        self.thing_id = None

    def fetch_data(self):
        if self.thing_id is None:
            raise Exception("Thing ID not set")

        while not self.stopped:
            channel = grpc.insecure_channel(config.grpc_endpoint)
            stub = meter_connector_pb2_grpc.MeterConnectorStub(channel)
            request = meter_connector_pb2.SMDataRequest()
            response = stub.readMeter(request)
            self.data_hex = response.message
            self.data = extract_data(decode_packet(bytearray.fromhex(self.data_hex)))
            print("data_hex: ", self.data_hex)
            print("data: ", self.data)
            self.save_time_series_data()
            time.sleep(self.interval)

    def save_time_series_data(self):
        db = get_db()
        return await time_series_data_controller.save_time_series_data(
            db, self.thing_id, self.data.energy_delivered, "kwh", self.data.timestamp, None
        )

    def start(self):
        t = threading.Thread(target=self.fetch_data)
        t.start()

    def stop(self):
        self.stopped = True