from typing import List

from sqlalchemy.orm import Session

from app.database.schema import DaoMachine
from app.models.machine import MachineCreate


def save_machine(session: Session, machine: MachineCreate) -> DaoMachine:
    machine = DaoMachine(machine_id=machine.machine_id, machine_type=machine.machine_type)
    session.add(machine)
    session.commit()
    return machine


def fetch_machines(session: Session) -> List[DaoMachine]:
    return session.query(DaoMachine).all()


def fetch_machine_by_id(session: Session, id: int) -> DaoMachine:
    return session.query(DaoMachine).filter_by(id=id).first()
