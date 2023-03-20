from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from submodules.app_mypower_model.dblayer import tables
from ..dblayer import thing as thing_db


async def save_thing(session: Session, thing_id: str, thing_type: str, cid: Optional[str] = None) -> tables.Thing:
    """
    Saves a new thing with the given data.

    :param session: A database session object.
    :param thing_id: The public key of thing.
    :param thing_type: The type of the thing.
    :param cid: The cid of thing.
    :return: A Thing object representing the saved thing.
    :raises HTTPException: If a thing with the given ID already exists in the database.
    """
    thing = await thing_db.fetch_thing_by_thing_id(session, thing_id)
    if thing:
        raise HTTPException(status_code=400, detail="thing_id (public-key) exist.")

    return await thing_db.save_thing(session, thing_id, thing_type, cid)


async def fetch_thing_by_thing_id(session: Session, thing_id: str) -> tables.Thing:
    """
    Retrieves a thing by its public key.

    :param session: A database session object.
    :param thing_id: The public key of thing.
    :return: A Thing object representing the thing.
    :raises HTTPException: If a thing with the given ID already exists in the database.
    """
    thing = await thing_db.fetch_thing_by_thing_id(session, thing_id)
    if not thing:
        raise HTTPException(status_code=404, detail="Thing not found.")
    return thing


async def fetch_thing_by_id(session: Session, id: int) -> tables.Thing:
    """
    Retrieves a thing by its id.

    :param session: A database session object.
    :param id: The id of thing.
    :return: A Thing object representing the thing.
    :raises HTTPException: If a thing with the given ID already exists in the database.
    """
    thing = await thing_db.fetch_thing_by_id(session, id)
    if not thing:
        raise HTTPException(status_code=404, detail="Thing not found.")
    return thing


async def fetch_things(session: Session) -> List[tables.Thing]:
    """
    Retrieves all existed things.

    :param session: A database session object.
    :return: A list of Thing objects representing the things.
    """
    return await thing_db.fetch_things(session)
