from typing import List, Optional

from sqlalchemy.orm import Session

from ..dblayer.tables import Thing


async def save_thing(session: Session, thing_id: int, thing_type: str, cid: Optional[str] = None) -> Thing:
    """
    Insert a thing object to DB.

    :param session: A database session object.
    :param thing_id: The public key of thing.
    :param thing_type: The type of thing.
    :param cid: The CID of the thing.
    :return: The inserted thing.
    """
    thing = Thing(thing_id=thing_id, thing_type=thing_type, cid=cid if cid else None)
    session.add(thing)
    session.commit()
    return thing


async def fetch_things(session: Session) -> List[Thing]:
    """
    Retrieves all existed things.

    :param session: A database session object.
    :return: A list of Thing objects.
    """
    return session.query(Thing).all()


async def fetch_thing_by_id(session: Session, id: int) -> Thing:
    """
    Retrieves a thing by its id.

    :param session: A database session object.
    :param id: The id of thing.
    :return: A Thing object.
    """
    return session.query(Thing).filter_by(id=id).first()


async def fetch_thing_by_thing_id(session: Session, thing_id: str) -> Thing:
    """
    Retrieves a thing by its public key.

    :param session: A database session object.
    :param thing_id: The public key of thing.
    :return: A Thing object.
    """
    return session.query(Thing).filter_by(thing_id=thing_id).first()
