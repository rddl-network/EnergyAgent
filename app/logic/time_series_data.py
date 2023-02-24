import time
from datetime import datetime, time
from decimal import Decimal
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.database import machine as machine_db
from app.database import time_series_data as time_series_data_db
from app.models.time_series_data import TimeSeriesData


def fetch_and_store_time_series_data_every_n_minutes_from_hardware(machine_id: int, n: int = 15):
    # TODO: Replace dummy data with real data from hardware
    while True:
        data = [
            TimeSeriesData(created_at=datetime.now(), unit='kwh', absolute_energy=1.0),
            TimeSeriesData(created_at=datetime.now(), unit='kwh', absolute_energy=2.0),
        ]
        store_time_series_data(machine_id, data)
        time.sleep(n * 60)


def store_time_series_data(session: Session, machine_id: int, data: List[TimeSeriesData]):
    for time_series_data in data:
        session.add(time_series_data_db.DaoTimeSeriesData(machine_id=machine_id, **time_series_data.dict()))


def save_time_series_data(session: Session, machine_id: int, absolute_energy: Decimal, unit: str, create_at: datetime,
                          cid: Optional[str] = None) -> time_series_data_db.DaoTimeSeriesData:
    dao_machine = machine_db.fetch_machine_by_id(session, machine_id)
    if not dao_machine:
        raise HTTPException(status_code=404, detail='Machine not found.')
    return time_series_data_db.save_time_series_data(session, machine_id, absolute_energy, unit, create_at, cid)


def fetch_machine_aggregated_time_series_data(session: Session, machine_id: int, start_date: datetime,
                                              end_date: datetime, resolution: str):
    dao_machine = machine_db.fetch_machine_by_id(session, machine_id)
    if not dao_machine:
        raise HTTPException(status_code=404, detail='Machine not found.')
    return time_series_data_db.fetch_machine_aggregated_time_series_data(session, machine_id, start_date, end_date,
                                                                         resolution)


def fetch_all_aggregated_time_series_data(session: Session, start_date: datetime, end_date: datetime, resolution: str):
    return time_series_data_db.fetch_all_aggregated_time_series_data(session, start_date, end_date, resolution)
