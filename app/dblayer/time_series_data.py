import datetime
from decimal import Decimal
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.dblayer.machine import fetch_machine_by_id
from app.dblayer.tables import DaoTimeSeriesData


def save_time_series_data(session: Session, machine_id: int, absolute_energy: Decimal, unit: str, create_at: datetime,
                          cid: Optional[str] = None) -> DaoTimeSeriesData:
    """
     Saves time-series data for a machine with the given machine_id.

     :param session: A database session object.
     :param machine_id: The id of machine for which the time-series data is being saved.
     :param absolute_energy: The absolute energy value of the time-series data.
     :param unit: The unit of measurement.
     :param create_at: The timestamp of the time-series data.
     :param cid: The cid of the time-series data.
     :return: The saved DaoTimeSeriesData object.
     """
    machine = fetch_machine_by_id(session, machine_id)
    if not machine:
        raise HTTPException(status_code=404, detail='Machine not found.')
    data = DaoTimeSeriesData(created_at=create_at, absolute_energy=absolute_energy, unit=unit,
                             machine_id=machine_id, cid=cid if cid else None)
    session.add(data)
    session.commit()
    return data


def fetch_time_series_data_by_id(session: Session, id: int) -> DaoTimeSeriesData:
    return session.query(DaoTimeSeriesData).filter_by(id=id).first().data


def fetch_time_series_data_by_machine_id(session: Session, machine_id: int) -> List[DaoTimeSeriesData]:
    return session.query(DaoTimeSeriesData).filter_by(machine_id=machine_id).all()


def fetch_machine_aggregated_time_series_data(session: Session, machine_id: int, start_date: datetime,
                                              end_date: datetime, resolution: str) -> List[dict]:
    """
    Retrieves aggregated time-series data for a machine for defined period.

    :param session: A database session object.
    :param machine_id: The id of machine for which the time-series data is being saved.
    :param start_date: The start date of the time period for which the data is being retrieved.
    :param end_date: The end date of the time period for which the data is being retrieved.
    :param resolution: The resolution.
    :return: A list of dictionaries representing the retrieved time-series data.
    """
    stmt = text("""
        SELECT COALESCE(main_query.machine_id, :machine_id) AS machine_id,
            generate_serires_query.time_slot,
            COALESCE (main_query.energy_value, 0) AS energy_value
        FROM (
            SELECT generate_series(:start_date ::timestamp, :end_date ::timestamp - INTERVAL '1 second', :resolution) AS time_slot
        ) AS generate_serires_query
        LEFT JOIN (
            SELECT machine_id,
                time_slot,
                energy_value
            FROM (
                SELECT machine_id,
                    time_bucket(:resolution, created_at) AS time_slot,
                    MAX(absolute_energy) -
                        COALESCE(
                        LAG(MAX(absolute_energy) FILTER (WHERE absolute_energy IS NOT NULL), 1)
                        OVER (PARTITION BY machine_id ORDER BY time_bucket(:resolution, created_at)), 0
                    ) AS energy_value
                FROM timeseries_data
                WHERE machine_id = :machine_id
                AND created_at >= :start_date ::timestamp - INTERVAL :resolution
                AND created_at < :end_date ::timestamp
                GROUP BY machine_id, time_slot
        ) AS subquery
        WHERE time_slot >= :start_date) AS main_query
        ON generate_serires_query.time_slot = main_query.time_slot;
    """)
    stmt = stmt.bindparams(
        start_date=start_date.strftime('%Y-%m-%d %H:%M:%S'),
        end_date=end_date.strftime('%Y-%m-%d %H:%M:%S'),
        machine_id=machine_id,
        resolution=resolution
    )
    return session.execute(stmt).all()


def fetch_all_aggregated_time_series_data(session: Session, start_date: datetime, end_date: datetime,
                                          resolution: str) -> List[dict]:
    """
      Retrieves aggregated time-series data for all machines for defined period.

      :param session: A database session object.
      :param start_date: The start date of the time period for which the data is being retrieved.
      :param end_date: The end date of the time period for which the data is being retrieved.
      :param resolution: The resolution.
      :return: A list of dictionaries representing the retrieved time-series data.
      """
    stmt = text("""
        SELECT generate_serires_query.machine_id AS machine_id,
            generate_serires_query.time_slot,
            COALESCE (main_query.energy_value, 0) AS energy_value
        FROM (
            SELECT DISTINCT id AS machine_id,
                generate_series(:start_date ::timestamp, :end_date ::timestamp - INTERVAL '1 second', :resolution) AS time_slot
            FROM machine
        ) AS generate_serires_query
        LEFT JOIN (
        SELECT machine_id,
            time_slot,
            energy_value
        FROM (
            SELECT machine_id,
            time_bucket(:resolution, created_at) AS time_slot,
            MAX(absolute_energy) -
            COALESCE(
                LAG(MAX(absolute_energy) FILTER (WHERE absolute_energy IS NOT NULL), 1)
                OVER (PARTITION BY machine_id ORDER BY time_bucket(:resolution, created_at)), 0
            ) AS energy_value
            FROM timeseries_data
            WHERE created_at >= :start_date ::timestamp - INTERVAL :resolution
            AND created_at < :end_date ::timestamp
            GROUP BY machine_id, time_slot
        ) AS subquery
        WHERE time_slot >= :start_date) AS main_query
        ON generate_serires_query.time_slot = main_query.time_slot
        AND generate_serires_query.machine_id = main_query.machine_id;
    """)
    stmt = stmt.bindparams(
        start_date=start_date.strftime('%Y-%m-%d %H:%M:%S'),
        end_date=end_date.strftime('%Y-%m-%d %H:%M:%S'),
        resolution=resolution
    )
    return session.execute(stmt).all()
