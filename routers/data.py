from typing import List

from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session

import schema
from dependencies import get_db

router = APIRouter(
    prefix="/time-series-data",
    tags=["time-series-data"],
    responses={404: {"detail": "Not found"}},
)


@router.get("/", response_model=List[schema.TimeSeriesData], summary="Return all time-series-data")
def get_time_series_data(
        db: Session = Depends(get_db),
        skip: int = 0,
        limit: int = 100,
):
    """
    Description
    -----------
    - Return all time-series-data.

    Pre-conditions
    -----------
    - The **master-key** must be created before.
    """
    pass


@router.get("/range", response_model=List[schema.TimeSeriesData], summary="Return all time-series-data in a range")
def get_time_series_data_range(
        db: Session = Depends(get_db),
        start: int = 0,
        end: int = 0,
):
    """
    Description
    -----------
    - Return all time-series-data in a range.

    Pre-conditions
    -----------
    - The **master-key** must be created before.
    """
    pass


@router.post("/", response_model=schema.TimeSeriesData, summary="Add a new time-series-data")
def add_time_series_data(
        db: Session = Depends(get_db),
        time_series_data: schema.TimeSeriesData = None,
):
    """
    Description
    -----------
    - Add a new time-series-data.

    Pre-conditions
    -----------
    - The **master-key** must be created before.
    """
    pass

