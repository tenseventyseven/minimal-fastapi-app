from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from minimal_fastapi_app.core.config import get_settings

Base = declarative_base()


def get_engine():
    """Create a new SQLAlchemy async engine using the current settings."""
    return create_async_engine(get_settings().database_url, echo=False, future=True)


def get_async_session():
    """Create a new SQLAlchemy async sessionmaker using the current settings."""
    engine = get_engine()
    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
