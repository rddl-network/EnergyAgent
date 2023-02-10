from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Integer

Base = declarative_base()


class DaoMachine(Base):
    __tablename__ = 'machine'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    type = Column(String)


class DaoTimeSeriesData(Base):
    __tablename__ = 'timeseries_data'
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime)
    kwh = Column(Float)
    machine_id = Column(Integer, ForeignKey('machine.id'))
    