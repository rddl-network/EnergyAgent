from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.time_series_data import \
    fetch_time_series_data_by_machine_id_in_range
from app.dependencies import get_db
from app.helper.enums import Resolution
from app.logic import time_series_data as time_series_data_logic
from app.models.time_series_data import (AggregatedTimeSeriesData,
                                         TimeSeriesData, TimeSeriesDataCreate)

router = APIRouter(
    prefix="/time-series-data",
    tags=["time-series-data"],
    responses={404: {"detail": "Not found"}},
)


@router.post("/", response_model=TimeSeriesData, summary="Add a new time-series-data")
def add_time_series_data(
        db: Session = Depends(get_db),
        data: TimeSeriesDataCreate = None,
):
    """
    Description
    -----------
    - Add a new time-series-data.
    """
    return time_series_data_logic.save_time_series_data(db, data.machine_id, data.absolute_energy, data.unit,
                                                        data.created_at, data.cid if data.cid else None)


@router.get("/range", response_model=List[TimeSeriesData], summary="Return all time-series-data in a range")
def get_time_series_data_by_machine_id_in_range(
        db: Session = Depends(get_db),
        machine_id: int = 0,
        start: datetime = datetime.now(),
        end: datetime = datetime.now(),
):
    """
    Description
    -----------
    - Return all time-series-data in a range for a specific machine.
    """
    return fetch_time_series_data_by_machine_id_in_range(db, machine_id, start, end)


@router.get("/machine_aggregated_data", response_model=List[AggregatedTimeSeriesData])
def get_machine_aggregated_time_series_data(
        machine_id: int,
        start_date: datetime,
        end_date: datetime,
        resolution: Resolution = Resolution.fifteen_minutes.value,
        db: Session = Depends(get_db),
):
    data = time_series_data_logic.fetch_machine_aggregated_time_series_data(db, machine_id, start_date, end_date,
                                                                            resolution.value)
    return sorted(data, key=lambda d: d.time_slot)


@router.get("/all_aggregated_data", response_model=List[AggregatedTimeSeriesData])
def get_machine_aggregated_time_series_data(
        start_date: datetime,
        end_date: datetime,
        resolution: Resolution = Resolution.fifteen_minutes.value,
        db: Session = Depends(get_db),
):
    data = time_series_data_logic.fetch_all_aggregated_time_series_data(db, start_date, end_date, resolution.value)
    return sorted(data, key=lambda d: (d.machine_id, d.time_slot))
