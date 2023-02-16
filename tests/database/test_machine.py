from app.database.machine import (fetch_machine_by_id, fetch_machines,
                                  save_machine)
from app.database.schema import DaoMachine
from app.models.machine import MachineCreate


def test_save_machine(mocker):
    session = mocker.MagicMock()
    machine = MachineCreate(machine_id='machine_id 1', machine_type='test')
    session.query.return_value.filter_by.return_value.first.return_value = None
    dao_machine = save_machine(session, machine)
    assert isinstance(dao_machine, DaoMachine)
    assert dao_machine.machine_id == machine.machine_id
    assert dao_machine.machine_type == machine.machine_type


def test_fetch_machines(mocker):
    session = mocker.MagicMock()
    session.query.return_value.all.return_value = [DaoMachine(machine_id='machine_id 2', machine_type='test')]
    dao_machines = fetch_machines(session)
    assert isinstance(dao_machines[0], DaoMachine)
    assert dao_machines[0].machine_id == 'machine_id 2'
    assert dao_machines[0].machine_type == 'test'


def test_fetch_machine_by_id(mocker):
    session = mocker.MagicMock()
    session.query.return_value.filter_by.return_value.first.return_value.machine = \
        DaoMachine(machine_id='machine_id 3', machine_type='test machine')

    dao_machine = fetch_machine_by_id(session, 0)
    dao_machine.machine_id == 'machine_id'
    dao_machine.machine_id == 'test machine'
