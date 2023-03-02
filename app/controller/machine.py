from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..dblayer import machine as machine_db
from ..dblayer import tables


async def save_machine(session: Session, machine_id: str, machine_type: str, cid: Optional[str] = None) -> tables.DaoMachine:
    """
    Saves a new machine with the given data.

    :param session: A database session object.
    :param machine_id: The public key of machine.
    :param machine_type: The type of the machine.
    :param cid: The cid of machine.
    :return: A DaoMachine object representing the saved machine.
    :raises HTTPException: If a machine with the given ID already exists in the database.
    """
    machine = await machine_db.fetch_machine_by_machine_id(session, machine_id)
    if machine:
        raise HTTPException(status_code=400, detail='Machine_id (public-key) exist.')

    return await machine_db.save_machine(session, machine_id, machine_type, cid)


async def fetch_machine_by_machine_id(session: Session, machine_id: str) -> tables.DaoMachine:
    """
    Retrieves a machine by its public key.

    :param session: A database session object.
    :param machine_id: The public key of machine.
    :return: A DaoMachine object representing the machine.
    :raises HTTPException: If a machine with the given ID already exists in the database.
    """
    machine = await machine_db.fetch_machine_by_machine_id(session, machine_id)
    if not machine:
        raise HTTPException(status_code=404, detail='Machine not found.')
    return machine


async def fetch_machine_by_id(session: Session, id: int) -> tables.DaoMachine:
    """
    Retrieves a machine by its id.

    :param session: A database session object.
    :param id: The id of machine.
    :return: A DaoMachine object representing the machine.
    :raises HTTPException: If a machine with the given ID already exists in the database.
    """
    machine = await machine_db.fetch_machine_by_id(session, id)
    if not machine:
        raise HTTPException(status_code=404, detail='Machine not found.')
    return machine


async def fetch_machines(session: Session) -> List[tables.DaoMachine]:
    """
    Retrieves all existed machines.

    :param session: A database session object.
    :return: A list of DaoMachine objects representing the machines.
    """
    return await machine_db.fetch_machines(session)
