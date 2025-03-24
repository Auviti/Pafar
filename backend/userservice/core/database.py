from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from fastapi import Depends

from core.config import settings

Base = declarative_base()
CHAR_LENGTH=255
# First database engine
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///db1.db"  # For SQLite, update with the actual URI if necessary.
engine_db1 = create_async_engine(str(settings.SQLALCHEMY_DATABASE_URI), echo=True)

# Second database engine
engine_db2 = create_async_engine('sqlite+aiosqlite:///db2.db', echo=True)

# Session factory for the first database (Async)
AsyncSessionDB1 = sessionmaker(
    bind=engine_db1, 
    class_=AsyncSession, 
    expire_on_commit=False, 
)

# Session factory for the second database (Async)
AsyncSessionDB2 = sessionmaker(
    bind=engine_db2, 
    class_=AsyncSession, 
    expire_on_commit=False, 
)

# Dependency to get the async session for the first database
async def get_db1():
    async with AsyncSessionDB1() as session:
        yield session  # Session will automatically close at the end of the async with block

# Dependency to get the async session for the second database
async def get_db2():
    async with AsyncSessionDB2() as session:
        yield session  # Session will automatically close at the end of the async with block
