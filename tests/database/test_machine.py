import pytest

from app.dblayer import thing as thing_db
from app.dblayer.tables import Thing

pytest_plugins = ("pytest_asyncio",)


@pytest.mark.asyncio
async def test_save_thing(mocker):
    session = mocker.MagicMock()
    session.query.return_value.filter_by.return_value.first.return_value = None
    thing = await thing_db.save_thing(session, thing_id="thing_id 1", thing_type="test", cid="cid 1")
    assert isinstance(thing, Thing)
    assert thing.thing_id == "thing_id 1"
    assert thing.thing_type == "test"
    assert thing.cid == "cid 1"


@pytest.mark.asyncio
async def test_fetch_things(mocker):
    session = mocker.MagicMock()
    session.query.return_value.all.return_value = [Thing(thing_id="thing_id 2", thing_type="test")]
    thing = await thing_db.fetch_things(session)
    assert isinstance(thing[0], Thing)
    assert thing[0].thing_id == "thing_id 2"
    assert thing[0].thing_type == "test"


@pytest.mark.asyncio
async def test_fetch_thing_by_id(mocker):
    session = mocker.MagicMock()
    session.query.return_value.filter_by.return_value.first.return_value.thing = Thing(
        thing_id="thing_id 3", thing_type="test thing"
    )

    thing = await thing_db.fetch_thing_by_id(session, 0)
    thing.thing_id == "thing_id"
    thing.thing_id == "test thing"
