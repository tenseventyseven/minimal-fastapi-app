from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from minimal_fastapi_app.core.config import get_settings

Base = declarative_base()

# Create engine and sessionmaker as singletons for thread safety and reuse
_engine = create_async_engine(get_settings().database_url, echo=False, future=True)
_async_session_factory = async_sessionmaker(
    _engine, expire_on_commit=False, class_=AsyncSession
)


def get_engine():
    """Return the singleton SQLAlchemy async engine."""
    return _engine


def get_async_session():
    """Return the singleton SQLAlchemy async sessionmaker."""
    return _async_session_factory
