"""
Database configuration and connection management.
"""
import logging
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker, AsyncEngine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import NullPool
from .config import settings

logger = logging.getLogger(__name__)

# Global variables for lazy initialization
engine: Optional[AsyncEngine] = None
AsyncSessionLocal: Optional[async_sessionmaker] = None

# Base class for models
Base = declarative_base()


def get_engine() -> AsyncEngine:
    """Get or create the database engine."""
    global engine
    if engine is None:
        database_url = settings.database_url
        
        # Handle different database types
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
        elif database_url.startswith("sqlite://"):
            database_url = database_url.replace("sqlite://", "sqlite+aiosqlite://")
        
        engine = create_async_engine(
            database_url,
            poolclass=NullPool,
            echo=settings.debug,
        )
    return engine


def get_session_factory() -> async_sessionmaker:
    """Get or create the session factory."""
    global AsyncSessionLocal
    if AsyncSessionLocal is None:
        AsyncSessionLocal = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session.
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database tables.
    """
    try:
        # Database table creation is handled by migrations
        logger.info("Database initialization called - using migrations for table creation")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise


async def close_db() -> None:
    """
    Close database connections.
    """
    if engine:
        await engine.dispose()
    logger.info("Database connections closed")