import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from ..dblayer.tables import TimeSeriesData


async def save_time_series_data(
    session: Session,
    thing_id: int,
    absolute_energy: Decimal,
    unit: str,
    create_at: datetime,
    cid: Optional[str] = None,
) -> TimeSeriesData:
    """
    Saves time-series data for a thing with the given thing_id.

    :param session: A database session object.
    :param thing_id: The id of thing for which the time-series data is being saved.
    :param absolute_energy: The absolute energy value of the time-series data.
    :param unit: The unit of measurement.
    :param create_at: The timestamp of the time-series data.
    :param cid: The cid of the time-series data.
    :return: The saved DaoTimeSeriesData object.
    """
    data = TimeSeriesData(
        created_at=create_at, absolute_energy=absolute_energy, unit=unit, thing_id=thing_id, cid=cid if cid else None
    )
    session.add(data)
    session.commit()
    return data


async def fetch_time_series_data_by_id(session: Session, id: int) -> TimeSeriesData:
    """
    Retrieves time-series data by its id.

    :param session: A database session object.
    :param id: The id of time-series data .
    :return: time-series data.
    """
    return session.query(TimeSeriesData).filter_by(id=id).first().data


async def fetch_time_series_data_by_thing_id(session: Session, thing_id: int) -> List[TimeSeriesData]:
    """
    Retrieves list of time-series data by thing_id.

    :param session: A database session object.
    :param thing_id: thing_id of time_series data.
    :return: list of time-series data.
    """
    return session.query(TimeSeriesData).filter_by(thing_id=thing_id).all()


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
    """
    stmt = text(
        """
        SELECT COALESCE(main_query.thing_id, :thing_id) AS thing_id,
            generate_serires_query.time_slot,
            COALESCE (main_query.energy_value, 0) AS energy_value
        FROM (
            SELECT generate_series(:start_date ::timestamp, :end_date ::timestamp - INTERVAL '1 second', :resolution) AS time_slot
        ) AS generate_serires_query
        LEFT JOIN (
            SELECT thing_id,
                time_slot,
                energy_value
            FROM (
                SELECT thing_id,
                    time_bucket(:resolution, created_at) AS time_slot,
                    MAX(absolute_energy) -
                        COALESCE(
                        LAG(MAX(absolute_energy) FILTER (WHERE absolute_energy IS NOT NULL), 1)
                        OVER (PARTITION BY thing_id ORDER BY time_bucket(:resolution, created_at)), 0
                    ) AS energy_value
                FROM timeseries_data
                WHERE thing_id = :thing_id
                AND created_at >= :start_date ::timestamp - INTERVAL :resolution
                AND created_at < :end_date ::timestamp
                GROUP BY thing_id, time_slot
        ) AS subquery
        WHERE time_slot >= :start_date) AS main_query
        ON generate_serires_query.time_slot = main_query.time_slot;
    """
    )
    stmt = stmt.bindparams(
        start_date=start_date.strftime("%Y-%m-%d %H:%M:%S"),
        end_date=end_date.strftime("%Y-%m-%d %H:%M:%S"),
        thing_id=thing_id,
        resolution=resolution,
    )
    return session.execute(stmt).all()


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
    stmt = text(
        """
        SELECT generate_serires_query.thing_id AS thing_id,
            generate_serires_query.time_slot,
            COALESCE (main_query.energy_value, 0) AS energy_value
        FROM (
            SELECT DISTINCT id AS thing_id,
                generate_series(:start_date ::timestamp, :end_date ::timestamp - INTERVAL '1 second', :resolution) AS time_slot
            FROM thing
        ) AS generate_serires_query
        LEFT JOIN (
        SELECT thing_id,
            time_slot,
            energy_value
        FROM (
            SELECT thing_id,
            time_bucket(:resolution, created_at) AS time_slot,
            MAX(absolute_energy) -
            COALESCE(
                LAG(MAX(absolute_energy) FILTER (WHERE absolute_energy IS NOT NULL), 1)
                OVER (PARTITION BY thing_id ORDER BY time_bucket(:resolution, created_at)), 0
            ) AS energy_value
            FROM timeseries_data
            WHERE created_at >= :start_date ::timestamp - INTERVAL :resolution
            AND created_at < :end_date ::timestamp
            GROUP BY thing_id, time_slot
        ) AS subquery
        WHERE time_slot >= :start_date) AS main_query
        ON generate_serires_query.time_slot = main_query.time_slot
        AND generate_serires_query.thing_id = main_query.thing_id;
    """
    )
    stmt = stmt.bindparams(
        start_date=start_date.strftime("%Y-%m-%d %H:%M:%S"),
        end_date=end_date.strftime("%Y-%m-%d %H:%M:%S"),
        resolution=resolution,
    )
    return session.execute(stmt).all()
