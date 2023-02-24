from datetime import datetime

from app.database.schema import DaoTimeSeriesData
from app.database.time_series_data import (
    fetch_time_series_data_by_id, fetch_time_series_data_by_machine_id,
    fetch_time_series_data_by_machine_id_in_range, save_time_series_data)
from app.models.time_series_data import TimeSeriesDataCreate


def test_save_time_series_data(mocker):
    session = mocker.MagicMock()
    data = TimeSeriesDataCreate(timestamp=datetime.now(), absolute_energy=0, unit='kWh', machine_id=0)
    dao_data = save_time_series_data(session, data)
    assert isinstance(dao_data, DaoTimeSeriesData)
    assert dao_data.created_at == data.timestamp
    assert dao_data.unit == 'kWh'
    assert dao_data.absolute_energy == '0'
    assert dao_data.machine_id == data.machine_id


def test_fetch_time_series_data_by_id(mocker):
    session = mocker.MagicMock()
    session.query.return_value.filter_by.return_value.first.return_value.data = DaoTimeSeriesData(
        timestamp=datetime.now(), absolute_energy=0, unit='kWh', machine_id=0)
    dao_data = fetch_time_series_data_by_id(session, 0)
    assert isinstance(dao_data, DaoTimeSeriesData)


def test_fetch_time_series_data_by_machine_id(mocker):
    session = mocker.MagicMock()
    session.query.return_value.filter_by.return_value.all.return_value = [
        DaoTimeSeriesData(timestamp=datetime.now(), absolute_energy=0, unit='kWh', machine_id=0)]

    dao_data = fetch_time_series_data_by_machine_id(session, 0)
    assert isinstance(dao_data[0], DaoTimeSeriesData)


def test_fetch_time_series_data_by_machine_id_in_range(mocker):
    session = mocker.MagicMock()
    session.query.return_value.filter_by.return_value.filter.return_value.all.return_value = [
        DaoTimeSeriesData(timestamp=datetime.now(), absolute_energy=0, unit='kWh', machine_id=0)]

    dao_data = fetch_time_series_data_by_machine_id_in_range(session, 0, datetime.now(), datetime.now())
    assert isinstance(dao_data[0], DaoTimeSeriesData)
