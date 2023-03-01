from typing import List, Optional

from sqlalchemy.orm import Session

from ..dblayer.tables import DaoMachine


async def save_machine(session: Session, machine_id, machine_type, cid: Optional[str] = None) -> DaoMachine:
    machine = DaoMachine(machine_id=machine_id, machine_type=machine_type, cid=cid if cid else None)
    session.add(machine)
    session.commit()
    return machine


async def fetch_machines(session: Session) -> List[DaoMachine]:
    """
    Retrieves all existed machines.

    :param session: A database session object.
    :return: A list of DaoMachine objects representing the machines.
    """
    return session.query(DaoMachine).all()


async def fetch_machine_by_id(session: Session, id: int) -> DaoMachine:
    """
    Retrieves a machine by its id.

    :param session: A database session object.
    :param id: The id of machine.
    :return: A DaoMachine object representing the machine.
    """
    return session.query(DaoMachine).filter_by(id=id).first()


async def fetch_machine_by_machine_id(session: Session, machine_id: str) -> DaoMachine:
    """
    Retrieves a machine by its public key.

    :param session: A database session object.
    :param machine_id: The public key of machine.
    :return: A DaoMachine object representing the machine.
    """
    return session.query(DaoMachine).filter_by(machine_id=machine_id).first()
