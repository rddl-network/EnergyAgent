from database.machine import save_machine, fetch_machines, fetch_machine_by_id
from models.machine import MachineCreate
from database.schema import DaoMachine


def test_save_machine(mocker):
    session = mocker.MagicMock()
    machine = MachineCreate(name='test', type='test')
    dao_machine = save_machine(session, machine)
    assert isinstance(dao_machine, DaoMachine)
    assert dao_machine.name == machine.name
    assert dao_machine.type == machine.type


def test_fetch_machines(mocker):
    session = mocker.MagicMock()
    session.query.return_value.all.return_value = [DaoMachine(name='test', type='test')]
    dao_machines = fetch_machines(session)
    assert isinstance(dao_machines[0], DaoMachine)
    assert dao_machines[0].name == 'test'
    assert dao_machines[0].type == 'test'


def test_fetch_machine_by_id(mocker):
    session = mocker.MagicMock()
    session.query.return_value.filter_by.return_value.first.return_value.machine = DaoMachine(name='test', type='test')

    dao_machine = fetch_machine_by_id(session, 0)
    assert isinstance(dao_machine, DaoMachine)
