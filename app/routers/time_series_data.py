from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.controller import time_series_data as time_series_data_controller
from app.dependencies import get_db
from app.helper.enums import Resolution
from app.schemas import (AggregatedTimeSeriesData, TimeSeriesData,
                         TimeSeriesDataCreate)

router = APIRouter(
    prefix="/time-series-data",
    tags=["time-series-data"],
    responses={404: {"detail": "Not found"}},
)


@router.post("/", response_model=TimeSeriesData, summary="Add a new time-series-data for a machine")
def add_time_series_data(data: TimeSeriesDataCreate, db: Session = Depends(get_db)):
    """
    Description
    -----------
    - Add a new time-series-data for a machine.
    """
    return time_series_data_controller.save_time_series_data(db, data.machine_id, data.absolute_energy, data.unit,
                                                             data.created_at, data.cid if data.cid else None)


@router.get("/machine_aggregated_data", response_model=List[AggregatedTimeSeriesData],
            summary='Retrieves aggregated time-series data for a machine')
def get_machine_aggregated_time_series_data(
        machine_id: int,
        start_date: datetime,
        end_date: datetime,
        resolution: Resolution = Resolution.fifteen_minutes.value,
        db: Session = Depends(get_db),
):
    """
    Description
    -----------
    -  Retrieves aggregated time-series data for a machine.
    """
    data = time_series_data_controller.fetch_machine_aggregated_time_series_data(db, machine_id, start_date, end_date,
                                                                                 resolution.value)
    return sorted(data, key=lambda d: d.time_slot)


@router.get("/all_aggregated_data", response_model=List[AggregatedTimeSeriesData],
            summary='Retrieves aggregated time-series data all machines')
def get_machine_aggregated_time_series_data(
        start_date: datetime,
        end_date: datetime,
        resolution: Resolution = Resolution.fifteen_minutes.value,
        db: Session = Depends(get_db),
):
    """
    Description
    -----------
    -  Retrieves aggregated time-series data all machines.
    """
    data = time_series_data_controller.fetch_all_aggregated_time_series_data(db, start_date, end_date, resolution.value)
    return sorted(data, key=lambda d: (d.machine_id, d.time_slot))
