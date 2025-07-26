"""
Pytest configuration and fixtures for testing.
"""
import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.database import Base, get_db
from app.core.redis import RedisClient
from app.main import app


# Test database URL (SQLite in memory)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
    echo=False
)

# Create test session factory
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestSessionLocal() as session:
        yield session
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    class MockRedis:
        def __init__(self):
            self.data = {}
        
        async def get(self, key: str):
            return self.data.get(key)
        
        async def setex(self, key: str, time, value):
            self.data[key] = value
            return True
        
        async def delete(self, key: str):
            if key in self.data:
                del self.data[key]
                return True
            return False
        
        async def exists(self, key: str):
            return key in self.data
    
    return MockRedis()


@pytest.fixture
def override_get_db(db_session):
    """Override database dependency for testing."""
    async def _override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()