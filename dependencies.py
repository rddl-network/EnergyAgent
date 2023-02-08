import os

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database


class Config:
    def __init__(self):
        self.api_prefix = os.getenv('API_PREFIX') or ''
        self.db_type = os.environ.get('DATABASE_TYPE', 'mongodb')
        self.db_user = os.getenv('DB_USER') or 'postgres'
        self.db_password = os.getenv('DB_PASSWORD') or 'password'
        self.db_host = os.environ.get("DB_HOST") or 'localhost:5432'
        self.db_name = os.environ.get("DB_NAME") or 'energy'

        # build the database url
        self.db_url = f'postgresql://{self.db_user}:{self.db_password}@{self.db_host}/{self.db_name}'


config = Config()


def ensure_database():
    print(f"Ensuring database {config.db_name} exists at {config.db_url}")
    engine = create_engine(config.db_url)
    if not database_exists(engine.url):
        create_database(engine.url)


def get_db():
    engine = create_engine(config.db_url)
    session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = session_local()
    try:
        yield db
    finally:
        db.close()
