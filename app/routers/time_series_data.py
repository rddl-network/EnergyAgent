from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.time_series_data import (
    fetch_time_series_data_by_machine_id_in_range, save_time_series_data)
from app.dependencies import get_db
from app.models.time_series_data import TimeSeriesData, TimeSeriesDataCreate

router = APIRouter(
    prefix="/time-series-data",
    tags=["time-series-data"],
    responses={404: {"detail": "Not found"}},
)


@router.post("/", response_model=TimeSeriesData, summary="Add a new time-series-data")
def add_time_series_data(
        db: Session = Depends(get_db),
        time_series_data: TimeSeriesDataCreate = None,
):
    """
    Description
    -----------
    - Add a new time-series-data.

    Pre-conditions
    -----------
    - The **master-key** must be created before.
    """
    dao_time_series = save_time_series_data(db, time_series_data)
    return TimeSeriesData.from_dao(dao_time_series)


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

    Pre-conditions
    -----------
    - The **master-key** must be created before.
    """
    dao_time_series = fetch_time_series_data_by_machine_id_in_range(db, machine_id, start, end)
    return [TimeSeriesData.from_dao(dao_time_series) for dao_time_series in dao_time_series]
