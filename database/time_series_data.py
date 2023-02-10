import datetime
from typing import List

from sqlalchemy.orm import Session

from database.schema import DaoTimeSeriesData
from models.time_series_data import TimeSeriesDataCreate


def save_time_series_data(session: Session, data: TimeSeriesDataCreate) -> DaoTimeSeriesData:
    data = DaoTimeSeriesData(timestamp=data.timestamp, kwh=data.kwh, machine_id=data.machine_id)
    session.add(data)
    session.commit()
    return data


def fetch_time_series_data_by_id(session: Session, id: int) -> DaoTimeSeriesData:
    return session.query(DaoTimeSeriesData).filter_by(id=id).first().data


def fetch_time_series_data_by_machine_id(session: Session, machine_id: int) -> List[DaoTimeSeriesData]:
    return session.query(DaoTimeSeriesData).filter_by(machine_id=machine_id).all()


def fetch_time_series_data_by_machine_id_in_range(session: Session, machine_id: int, start: datetime, end: datetime) -> List[DaoTimeSeriesData]:
    return session.query(DaoTimeSeriesData).filter_by(machine_id=machine_id).filter(DaoTimeSeriesData.timestamp.between(start, end)).all()
