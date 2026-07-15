from __future__ import annotations

from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


def _sqlalchemy_database_url(database_url: str) -> str:
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+psycopg://", 1)
    return database_url


@lru_cache(maxsize=8)
def get_session_factory(database_url: str) -> sessionmaker[Session]:
    engine = create_engine(
        _sqlalchemy_database_url(database_url),
        pool_pre_ping=True,
    )
    return sessionmaker(bind=engine, expire_on_commit=False)
