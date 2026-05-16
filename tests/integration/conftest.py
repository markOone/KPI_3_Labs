import os
import sys
from pathlib import Path
import sqlite3
from decimal import Decimal

sqlite3.register_adapter(Decimal, float)

base_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(base_dir))

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from src.main import app 
from src.database.engine import db_helper
from src.infrastructure.database.models import Base 

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine_test = create_async_engine(TEST_DATABASE_URL, echo=False)
test_async_session = async_sessionmaker(engine_test, class_=AsyncSession, expire_on_commit=False)

async def override_get_db_session():
    async with test_async_session() as session:
        yield session

app.dependency_overrides[db_helper.get_db_session] = override_get_db_session

@pytest_asyncio.fixture(autouse=True)
async def prepare_database():
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac