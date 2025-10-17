from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.settings import settings

SQLALCHEMY_DATABASE_URL = (
    f"postgresql://{settings.postgres.postgres_user}:{settings.postgres.postgres_password}"
    f"@{settings.postgres.postgres_host}:{settings.postgres.postgres_port}/{settings.postgres.postgres_database}"
)

engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Для Depends


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
