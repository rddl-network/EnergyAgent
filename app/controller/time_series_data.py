from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from submodules.app_mypower_model.dblayer import tables
from submodules.app_mypower_model.dblayer import thing as thing_db
from submodules.app_mypower_model.dblayer import time_series_data as time_series_data_db


async def save_time_series_data(
    session: Session,
    thing_id: int,
    absolute_energy: Decimal,
    unit: str,
    create_at: datetime,
    cid: Optional[str] = None,
) -> tables.TimeSeriesData:
    """
    Saves time-series data for a thing with the given thing_id.

    :param session: A database session object.
    :param thing_id: The id of thing for which the time-series data is being saved.
    :param absolute_energy: The absolute energy value of the time-series data.
    :param unit: The unit of measurement.
    :param create_at: The timestamp of the time-series data.
    :param cid: The cid of the time-series data.
    :return: The saved DaoTimeSeriesData object.
    :raises HTTPException: If no thing with the given ID is found in the database.
    """
    thing = await thing_db.fetch_thing_by_id(session, thing_id)
    if not thing:
        raise HTTPException(status_code=404, detail="Thing not found.")
    return await time_series_data_db.save_time_series_data(session, thing_id, absolute_energy, unit, create_at, cid)


async def fetch_thing_aggregated_time_series_data(
    session: Session, thing_id: int, start_date: datetime, end_date: datetime, resolution: str
) -> List[dict]:
    """
    Retrieves aggregated time-series data for a thing for defined period.

    :param session: A database session object.
    :param thing_id: The id of thing for which the time-series data is being saved.
    :param start_date: The start date of the time period for which the data is being retrieved.
    :param end_date: The end date of the time period for which the data is being retrieved.
    :param resolution: The resolution.
    :return: A list of dictionaries representing the retrieved time-series data.
    :raises HTTPException: If no thing with the given ID is found in the database.
    """
    thing = await thing_db.fetch_thing_by_id(session, thing_id)
    if not thing:
        raise HTTPException(status_code=404, detail="Thing not found.")
    return await time_series_data_db.fetch_thing_aggregated_time_series_data(
        session, thing_id, start_date, end_date, resolution
    )


async def fetch_all_aggregated_time_series_data(
    session: Session, start_date: datetime, end_date: datetime, resolution: str
) -> List[dict]:
    """
    Retrieves aggregated time-series data for all things for defined period.

    :param session: A database session object.
    :param start_date: The start date of the time period for which the data is being retrieved.
    :param end_date: The end date of the time period for which the data is being retrieved.
    :param resolution: The resolution.
    :return: A list of dictionaries representing the retrieved time-series data.
    """
    return await time_series_data_db.fetch_all_aggregated_time_series_data(session, start_date, end_date, resolution)
