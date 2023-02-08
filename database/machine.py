from typing import List

from sqlalchemy.orm import Session

from database.schema import DaoMachine
from models.machine import MachineCreate


def save_machine(session: Session, machine: MachineCreate) -> DaoMachine:
    machine = DaoMachine(name=machine.name, type=machine.type)
    session.add(machine)
    session.commit()
    return machine


def fetch_machines(session: Session) -> List[DaoMachine]:
    return session.query(DaoMachine).all()


def fetch_machine_by_id(session: Session, id: int) -> DaoMachine:
    return session.query(DaoMachine).filter_by(id=id).first().machine
