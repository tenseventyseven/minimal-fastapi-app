import asyncio
import os

import pytest

from minimal_fastapi_app.core.db import get_engine
from minimal_fastapi_app.users.models import Base as UserBase
from minimal_fastapi_app.users.models import UserORM

# Always set the async driver for SQLite before any app import
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./app.db"


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create all tables before any tests run."""

    async def _create():
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(UserBase.metadata.create_all)

    asyncio.run(_create())
    yield
    # Optionally, drop tables after tests (uncomment if you want a clean DB)
    # async def _drop():
    #     engine = get_engine()
    #     async with engine.begin() as conn:
    #         await conn.run_sync(UserBase.metadata.drop_all)
    # asyncio.run(_drop())


@pytest.fixture(autouse=True)
def clean_users_table():
    """Truncate the users table before each test for isolation."""

    async def _truncate():
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.execute(UserORM.__table__.delete())

    asyncio.run(_truncate())
    yield
