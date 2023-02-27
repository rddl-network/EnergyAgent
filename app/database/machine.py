from typing import List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .schema import DaoMachine
from ..models.machine import MachineCreate


def save_machine(session: Session, machine: MachineCreate) -> DaoMachine:
    temp_machine = fetch_machine_by_machine_id(session, machine.machine_id)
    if temp_machine:
        raise HTTPException(status_code=400, detail='Machine_id (public-key) exist.')
    machine = DaoMachine(machine_id=machine.machine_id, machine_type=machine.machine_type,
                         cid=machine.cid if machine.cid else None)
    session.add(machine)
    session.commit()
    return machine


def fetch_machines(session: Session) -> List[DaoMachine]:
    return session.query(DaoMachine).all()


def fetch_machine_by_id(session: Session, id: int) -> DaoMachine:
    return session.query(DaoMachine).filter_by(id=id).first()


def fetch_machine_by_machine_id(session: Session, machine_id: str) -> DaoMachine:
    return session.query(DaoMachine).filter_by(machine_id=machine_id).first()
