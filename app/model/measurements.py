import datetime
from datetime import timezone


from threading import Lock

from app.helpers.logs import log, logger


class Measurements:
    def __init__(self) -> None:
        # self.async_mutex = AsyncLock()
        self.mutex = Lock()
        self.production_dict = {}
        self.to_grid = 0.0
        self.from_grid = 0.0

    @staticmethod
    def convert_to_kwh(value: float) -> float:
        return value / 1000

    def get_state(self, planetmint_address, cid: None) -> dict:
        state = {}
        with self.mutex:
            now = datetime.datetime.now(timezone.utc)
            state = {
                "public_key": planetmint_address,
                "time_stamp": now.isoformat(),
                "type": "absolute_energy",
                "unit": "kWh",
                "absolute_energy_in": self.from_grid,
                "absolute_energy_out": self.to_grid,
                "absolute_energy_produced": self.get_overall_production(),
                "cid": cid,
            }

        return state

    def get_overall_production(self) -> float:
        production = 0.0
        for key in self.production_dict:
            production = production + self.production_dict[key]
        return production

    def set_abs_production_value(self, production: float, key: str = ""):
        with self.mutex:
            logger.debug(f"Measurements: write production {production}")
            self.production_dict.update({key: production})

    def set_abs_to_grid(self, to_grid):
        with self.mutex:
            logger.debug(f"Measurements: write to grid {to_grid}")
            self.to_grid = to_grid

    def set_abs_from_grid(self, from_grid):
        with self.mutex:
            logger.debug(f"Measurements: write from grid {from_grid}")
            self.from_grid = from_grid

    def set_sm_data(self, data_list):
        for data in data_list:
            if data.get("key") == "WirkenergieP":
                self.set_abs_from_grid(Measurements.convert_to_kwh(float(data.get("value"))))
            elif data.get("key") == "WirkenergieN":
                self.set_abs_to_grid(Measurements.convert_to_kwh(float(data.get("value"))))
