from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from minimal_fastapi_app.core.config import get_settings


class Base(DeclarativeBase):
    """SQLAlchemy 2+ declarative base class."""

    pass


_engine = None
_sessionmaker = None


def get_engine():
    """Return the shared SQLAlchemy async engine (lazily initialized)."""
    global _engine
    if _engine is None:
        _engine = create_async_engine(get_settings().database_url, echo=False)
    return _engine


def get_async_session():
    """Return the shared SQLAlchemy async sessionmaker (lazily initialized)."""
    global _sessionmaker
    if _sessionmaker is None:
        _sessionmaker = async_sessionmaker(
            get_engine(), expire_on_commit=False, class_=AsyncSession
        )
    return _sessionmaker


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    session_factory = get_async_session()
    async with session_factory() as session:
        yield session
