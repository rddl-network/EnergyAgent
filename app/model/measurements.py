import datetime
from datetime import timezone


from asyncio import Lock as AsyncLock
from app.helpers.logs import log


class Measurements:
    def __init__(self) -> None:
        self.async_mutex = AsyncLock()
        self.production = 0.0
        self.to_grid = 0.0
        self.from_grid = 0.0

    @log
    @staticmethod
    def convert_to_kwh(value: float) -> float:
        return value / 1000

    @log
    def transform_to_metrics(self, planetmint_address, cid) -> dict:
        now = datetime.now(timezone.utc)
        metric_data = {
            "public_key": planetmint_address,
            "time_stamp": now.isoformat(),
            "type": "absolute_energy",
            "unit": "kWh",
            "absolute_energy_in": self.from_grid,
            "absolute_energy_out": self.to_grid,
            "absolute_energy_produced": self.production,
            "cid": cid,
        }

        return metric_data  # Return the metric data

    def get_state(self, planetmint_address, cid: None) -> dict:
        state = {}
        with self.async_mutex:
            state = self.transform_to_metrics(planetmint_address, cid)

        return state

    def set_abs_production_value(self, production: float):
        self.production = production

    def set_abs_to_grid(self, to_grid):
        self.to_grid = to_grid

    def set_abs_from_grid(self, from_grid):
        self.from_grid = from_grid

    def set_sm_data(self, data_list):
        for data in data_list:
            if data.get("key") == "WirkenergieP":
                self.from_grid = Measurements.convert_to_kwh(float(data.get("value")))
            elif data.get("key") == "WirkenergieN":
                self.to_grid = Measurements.convert_to_kwh(float(data.get("value")))
