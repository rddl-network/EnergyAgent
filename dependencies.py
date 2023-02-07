import os

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database


class Config:
    def __init__(self):
        self.api_prefix = os.getenv('API_PREFIX') or ''
        self.db_type = os.environ.get('DATABASE_TYPE', 'mongodb')
        self.db_url = os.getenv('DB_URL') or 'postgresql://postgres:password@localhost:5432/energy'
        self.db_user = os.getenv('DB_USER') or 'postgres'
        self.db_password = os.getenv('DB_PASSWORD') or 'password'


config = Config()


def ensure_database():
    engine = create_engine(config.db_url)
    if not database_exists(engine.url):
        create_database(engine.url)


engine = create_engine(config.db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
