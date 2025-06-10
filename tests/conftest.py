# Set the test database URL before any app imports
import os

os.environ["DATABASE_URL"] = (
    "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres_test"
)

# Now import the rest
from typing import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from minimal_fastapi_app.core.db import Base
from minimal_fastapi_app.projects import models as _project_models  # noqa: F401
from minimal_fastapi_app.users import models as _user_models  # noqa: F401


@pytest_asyncio.fixture(scope="session")
async def db_engine():
    """Create a single engine for the entire test session."""
    engine = create_async_engine(
        os.environ["DATABASE_URL"], echo=False, poolclass=NullPool
    )
    # Create all tables once at the beginning
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def session_factory(db_engine):
    """Create a single session factory for the entire test session."""
    return async_sessionmaker(db_engine, expire_on_commit=False, class_=AsyncSession)


# This should match the dependency used in your app/routes
async def get_test_db_session(session_factory) -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture(scope="session")
async def app(db_engine, session_factory):
    """Create app with dependency override for test DB session."""
    from minimal_fastapi_app.main import app as fastapi_app

    # Dependency override for get_db_session
    async def override_get_db_session():
        async with session_factory() as session:
            yield session

    fastapi_app.dependency_overrides.clear()
    from minimal_fastapi_app.core.db import get_db_session

    fastapi_app.dependency_overrides[get_db_session] = override_get_db_session
    yield fastapi_app
    fastapi_app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def db_session(session_factory):
    """Provide a clean database session for each test (transaction rollback)."""
    async with session_factory() as session:
        await session.begin()
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def client(app):
    """Provide HTTP client for each test."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
