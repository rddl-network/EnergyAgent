import os

from sqlalchemy import NUMERIC, TIMESTAMP, Column, ForeignKey, Integer, String, create_engine, event, text
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class Thing(Base):
    __tablename__ = "thing"
    id = Column(Integer, primary_key=True)
    thing_id = Column(String, unique=True, nullable=False, comment="the public key of the thing")
    thing_type = Column(String, nullable=False)
    cid = Column(String, nullable=True)


class TimeSeriesData(Base):
    __tablename__ = "timeseries_data"
    id = Column(Integer, autoincrement=True, primary_key=True)
    created_at = Column(TIMESTAMP, primary_key=True)
    cid = Column(String, nullable=True)
    absolute_energy = Column(NUMERIC, nullable=False)
    unit = Column(String, nullable=False)
    thing_id = Column(Integer, ForeignKey("thing.id"))


@event.listens_for(Base.metadata, "after_create")
def receive_after_create(target, connection, tables, **kw):
    """
    listen for the 'after_create' event and create the hypertable
    """
    if tables:
        engine = create_engine(get_db_url())
        Session = sessionmaker(engine)
        session = Session(bind=connection)
        session.execute(text("SELECT create_hypertable('timeseries_data','created_at');"))
        session.commit()
        print("The hypertable was created")


def get_db_url():
    db_user = os.getenv("DB_USER") or "postgres"
    db_password = os.getenv("DB_PASSWORD") or "password"
    db_host = os.environ.get("DB_HOST") or "timescaledb"
    db_name = os.environ.get("DB_NAME") or "energy"
    return f"postgresql://{db_user}:{db_password}@{db_host}/{db_name}"
