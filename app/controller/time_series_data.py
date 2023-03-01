from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..dblayer import machine as machine_db
from ..dblayer import tables
from ..dblayer import time_series_data as time_series_data_db


async def save_time_series_data(session: Session, machine_id: int, absolute_energy: Decimal, unit: str,
                                create_at: datetime, cid: Optional[str] = None) -> tables.DaoTimeSeriesData:
    """
     Saves time-series data for a machine with the given machine_id.

     :param session: A database session object.
     :param machine_id: The id of machine for which the time-series data is being saved.
     :param absolute_energy: The absolute energy value of the time-series data.
     :param unit: The unit of measurement.
     :param create_at: The timestamp of the time-series data.
     :param cid: The cid of the time-series data.
     :return: The saved DaoTimeSeriesData object.
     :raises HTTPException: If no machine with the given ID is found in the database.
     """
    dao_machine = await machine_db.fetch_machine_by_id(session, machine_id)
    if not dao_machine:
        raise HTTPException(status_code=404, detail='Machine not found.')
    return await time_series_data_db.save_time_series_data(session, machine_id, absolute_energy, unit, create_at, cid)


async def fetch_machine_aggregated_time_series_data(session: Session, machine_id: int, start_date: datetime,
                                                    end_date: datetime, resolution: str) -> List[dict]:
    """
    Retrieves aggregated time-series data for a machine for defined period.

    :param session: A database session object.
    :param machine_id: The id of machine for which the time-series data is being saved.
    :param start_date: The start date of the time period for which the data is being retrieved.
    :param end_date: The end date of the time period for which the data is being retrieved.
    :param resolution: The resolution.
    :return: A list of dictionaries representing the retrieved time-series data.
    :raises HTTPException: If no machine with the given ID is found in the database.
    """
    dao_machine = await machine_db.fetch_machine_by_id(session, machine_id)
    if not dao_machine:
        raise HTTPException(status_code=404, detail='Machine not found.')
    return await time_series_data_db.fetch_machine_aggregated_time_series_data(session, machine_id, start_date,
                                                                               end_date, resolution)


async def fetch_all_aggregated_time_series_data(session: Session, start_date: datetime, end_date: datetime,
                                                resolution: str) -> List[dict]:
    """
    Retrieves aggregated time-series data for all machines for defined period.

    :param session: A database session object.
    :param start_date: The start date of the time period for which the data is being retrieved.
    :param end_date: The end date of the time period for which the data is being retrieved.
    :param resolution: The resolution.
    :return: A list of dictionaries representing the retrieved time-series data.
    """
    return await time_series_data_db.fetch_all_aggregated_time_series_data(session, start_date, end_date, resolution)
