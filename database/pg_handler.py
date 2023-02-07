from sqlalchemy import Column, String, JSON, Float, DateTime
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class DbData(Base):
    __tablename__ = 'data'
    cid = Column(String, primary_key=True)
    timestamp = Column(DateTime)
    kwh = Column(Float)


class DbMachine(Base):
    __tablename__ = 'machine'
    cid = Column(String, primary_key=True)
    machine = Column(JSON)


def save_data(session: Session, cid, data):
    data = DbData(cid=cid, data=data)
    session.add(data)
    session.commit()


def save_machine(session: Session, cid, machine):
    machine = DbMachine(cid=cid, machine=machine)
    session.add(machine)
    session.commit()


def get_data_by_cid(session: Session, cid):
    return session.query(DbData).filter_by(cid=cid).first().data


def get_machine_by_cid(session: Session, cid):
    return session.query(DbMachine).filter_by(cid=cid).first().machine


def get_data_in_range(session: Session, cid, start, end):
    return session.query(DbData).filter_by(cid=cid).filter(DbData.timestamp.between(start, end)).all()
