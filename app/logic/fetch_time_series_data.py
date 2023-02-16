import time
from datetime import datetime, time
from typing import List

from sqlalchemy.orm import Session

from app.database import DaoTimeSeriesData
from app.models.time_series_data import TimeSeriesData


def fetch_and_store_time_series_data_every_n_minutes_from_hardware(machine_id: int, n: int = 15):
    #TODO: Replace dummy data with real data from hardware
    while True:
        data = [
            TimeSeriesData(timestamp=datetime.now(), unin='kwh', absolute_energy=1.0),
            TimeSeriesData(timestamp=datetime.now(), unin='kwh', absolute_energy=2.0),
        ]
        store_time_series_data(machine_id, data)
        time.sleep(n * 60)


def store_time_series_data(session: Session, machine_id: int, data: List[TimeSeriesData]):
    for time_series_data in data:
        session.add(DaoTimeSeriesData(machine_id=machine_id, **time_series_data.dict()))
