import pytest

from app.dblayer import machine as machine_db
from app.dblayer.tables import DaoMachine

pytest_plugins = ('pytest_asyncio',)


@pytest.mark.asyncio
async def test_save_machine(mocker):
    session = mocker.MagicMock()
    session.query.return_value.filter_by.return_value.first.return_value = None
    dao_machine = await machine_db.save_machine(session, machine_id='machine_id 1', machine_type='test', cid='cid 1')
    assert isinstance(dao_machine, DaoMachine)
    assert dao_machine.machine_id == 'machine_id 1'
    assert dao_machine.machine_type == 'test'
    assert dao_machine.cid == 'cid 1'


@pytest.mark.asyncio
async def test_fetch_machines(mocker):
    session = mocker.MagicMock()
    session.query.return_value.all.return_value = [DaoMachine(machine_id='machine_id 2', machine_type='test')]
    dao_machines = await machine_db.fetch_machines(session)
    assert isinstance(dao_machines[0], DaoMachine)
    assert dao_machines[0].machine_id == 'machine_id 2'
    assert dao_machines[0].machine_type == 'test'


@pytest.mark.asyncio
async def test_fetch_machine_by_id(mocker):
    session = mocker.MagicMock()
    session.query.return_value.filter_by.return_value.first.return_value.machine = \
        DaoMachine(machine_id='machine_id 3', machine_type='test machine')

    dao_machine = await machine_db.fetch_machine_by_id(session, 0)
    dao_machine.machine_id == 'machine_id'
    dao_machine.machine_id == 'test machine'
