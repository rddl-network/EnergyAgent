import os
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import create_database, database_exists

from submodules.app_mypower_model.dblayer import Base


class Config:
    def __init__(self):
        self.db_user = os.getenv("DB_USER") or "postgres"
        self.db_password = os.getenv("DB_PASSWORD") or "password"
        self.db_host = os.environ.get("DB_HOST") or "timescaledb"
        self.db_port = os.environ.get("DB_PORT") or "5432"
        self.db_name = os.environ.get("DB_NAME") or "energy"
        self.grpc_host = os.environ.get("GRPC_HOST") or "192.168.68.68"
        self.grpc_port = os.environ.get("GRPC_PORT") or "50051"
        self.device = os.environ.get("DEVICE") or "WN"
        self.selection = os.environ.get("SELECTION") or "mock"
        self.verify_signature = bool(os.environ.get("VERIFY_SIGNATURE")) or False
        self.interval = int(os.environ.get("INTERVAL") or "15")
        self.thing_id = (os.environ.get("THING_ID") or "st-energy-meter")

        # build the database url
        self.db_url = f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
        self.grpc_endpoint = f"{self.grpc_host}:{self.grpc_port}"


config = Config()


def ensure_database():
    print(f"Ensuring database {config.db_name} exists at {config.db_url}")
    engine = create_engine(config.db_url)
    if not database_exists(engine.url):
        create_database(engine.url)
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)


def get_db():
    engine = create_engine(config.db_url)
    session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return session_local()


@contextmanager
def db_context():
    db = get_db()
    try:
        yield db
    finally:
        db.close()
