import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.models  # noqa: F401 — registers all models on Base.metadata
from app.database import Base, get_session
from app.main import app

TEST_DATABASE_URL = (
    "postgresql+asyncpg://matchsnapper:matchsnapper@localhost:5432/matchsnapper_test"
)

engine = create_async_engine(TEST_DATABASE_URL)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def session():
    async with engine.connect() as conn:
        await conn.begin()
        maker = async_sessionmaker(
            conn,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )
        async with maker() as s:
            yield s
        await conn.rollback()


@pytest_asyncio.fixture
async def client(session):
    async def _override():
        yield session

    app.dependency_overrides[get_session] = _override
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
