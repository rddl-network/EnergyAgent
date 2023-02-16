from sqlalchemy import (NUMERIC, TIMESTAMP, Column, Float, ForeignKey, Integer,
                        String)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class DaoMachine(Base):
    __tablename__ = 'machine'
    id = Column(Integer, primary_key=True)
    machine_id = Column(String, unique=True, nullable=False, comment="the public key of the machine")
    machine_type = Column(String, nullable=False)
    cid = Column(String, nullable=True)


class DaoTimeSeriesData(Base):
    __tablename__ = 'timeseries_data'
    id = Column(Integer, primary_key=True)
    timestamp = Column(TIMESTAMP, nullable=False)
    cid = Column(String, nullable=True)
    absolute_energy = Column(NUMERIC, nullable=False)
    unit = Column(String, nullable=False)
    machine_id = Column(Integer, ForeignKey('machine.id'))
