from datetime import datetime

import pytest

from app.dblayer import time_series_data as time_series_data_db
from app.dblayer.tables import TimeSeriesData

pytest_plugins = ("pytest_asyncio",)


@pytest.mark.asyncio
async def test_save_time_series_data(mocker):
    session = mocker.MagicMock()
    create_at = datetime.now()
    dao_data = await time_series_data_db.save_time_series_data(
        session, thing_id=1, absolute_energy=0, unit="kWh", create_at=create_at, cid="cid 1"
    )
    assert isinstance(dao_data, TimeSeriesData)
    assert dao_data.created_at == create_at
    assert dao_data.unit == "kWh"
    assert dao_data.absolute_energy == 0
    assert dao_data.thing_id == 1
    assert dao_data.cid == "cid 1"


@pytest.mark.asyncio
async def test_fetch_time_series_data_by_id(mocker):
    session = mocker.MagicMock()
    session.query.return_value.filter_by.return_value.first.return_value.data = TimeSeriesData(
        created_at=datetime.now(), absolute_energy=0, unit="kWh", thing_id=1
    )
    dao_data = await time_series_data_db.fetch_time_series_data_by_id(session, 1)
    assert isinstance(dao_data, TimeSeriesData)


@pytest.mark.asyncio
async def test_fetch_time_series_data_by_thing_id(mocker):
    session = mocker.MagicMock()
    session.query.return_value.filter_by.return_value.all.return_value = [
        TimeSeriesData(created_at=datetime.now(), absolute_energy=0, unit="kWh", thing_id=1)
    ]

    dao_data = await time_series_data_db.fetch_time_series_data_by_thing_id(session, 0)
    assert isinstance(dao_data[0], TimeSeriesData)
