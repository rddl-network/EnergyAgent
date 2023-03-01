from datetime import datetime

from app.dblayer.tables import DaoTimeSeriesData
from app.dblayer.time_series_data import (fetch_time_series_data_by_id,
                                          fetch_time_series_data_by_machine_id,
                                          save_time_series_data)


def test_save_time_series_data(mocker):
    session = mocker.MagicMock()
    create_at = datetime.now()
    dao_data = save_time_series_data(session, machine_id=1, absolute_energy=0, unit='kWh', create_at=create_at, cid='cid 1')
    assert isinstance(dao_data, DaoTimeSeriesData)
    assert dao_data.created_at == create_at
    assert dao_data.unit == 'kWh'
    assert dao_data.absolute_energy == 0
    assert dao_data.machine_id == 1
    assert dao_data.cid == 'cid 1'


def test_fetch_time_series_data_by_id(mocker):
    session = mocker.MagicMock()
    session.query.return_value.filter_by.return_value.first.return_value.data = DaoTimeSeriesData(
        created_at=datetime.now(), absolute_energy=0, unit='kWh', machine_id=1)
    dao_data = fetch_time_series_data_by_id(session, 1)
    assert isinstance(dao_data, DaoTimeSeriesData)


def test_fetch_time_series_data_by_machine_id(mocker):
    session = mocker.MagicMock()
    session.query.return_value.filter_by.return_value.all.return_value = [
        DaoTimeSeriesData(created_at=datetime.now(), absolute_energy=0, unit='kWh', machine_id=1)]

    dao_data = fetch_time_series_data_by_machine_id(session, 0)
    assert isinstance(dao_data[0], DaoTimeSeriesData)
