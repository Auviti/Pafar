"""
Database utility functions for connection management and health checks.
"""
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from ..core.database import AsyncSessionLocal, engine

logger = logging.getLogger(__name__)


async def check_database_connection() -> bool:
    """
    Check if database connection is healthy.
    
    Returns:
        bool: True if connection is healthy, False otherwise
    """
    try:
        from ..core.database import get_session_factory
        session_factory = get_session_factory()
        async with session_factory() as session:
            await session.execute(text("SELECT 1"))
            return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False


async def create_database_tables():
    """
    Create all database tables if they don't exist.
    This is useful for initial setup and testing.
    """
    try:
        from ..core.database import Base, get_engine
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise


async def drop_database_tables():
    """
    Drop all database tables. Use with caution!
    This is mainly for testing purposes.
    """
    try:
        from ..core.database import Base, get_engine
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        logger.info("Database tables dropped successfully")
    except Exception as e:
        logger.error(f"Error dropping database tables: {e}")
        raise