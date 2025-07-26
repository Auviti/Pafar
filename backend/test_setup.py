"""
Test script to verify database and Redis setup.
"""
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings
from app.core.database import Base, init_db
from app.core.redis import redis_client
from app.models import user, booking, fleet, payment, tracking


async def test_database_connection():
    """Test database connection and table creation."""
    print("🗄️  Testing database connection...")
    
    try:
        # Create test engine
        engine = create_async_engine(settings.DATABASE_URL, echo=True)
        
        # Test connection
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        print("✅ Database connection successful")
        print(f"   Database URL: {settings.DATABASE_URL}")
        
        # List all tables
        async with engine.begin() as conn:
            result = await conn.run_sync(lambda sync_conn: sync_conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall())
            tables = [row[0] for row in result]
            print(f"   Tables created: {', '.join(tables)}")
        
        await engine.dispose()
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


async def test_redis_connection():
    """Test Redis connection."""
    print("\n🔴 Testing Redis connection...")
    
    try:
        await redis_client.connect()
        
        # Test basic operations
        await redis_client.set("test_key", "test_value", 60)
        value = await redis_client.get("test_key")
        
        if value == "test_value":
            print("✅ Redis connection successful")
            print(f"   Redis URL: {settings.REDIS_URL}")
            print("   Basic operations working")
        else:
            print("❌ Redis basic operations failed")
            return False
        
        # Clean up
        await redis_client.delete("test_key")
        await redis_client.disconnect()
        return True
        
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print("   Make sure Redis is running on localhost:6379")
        return False


async def test_environment_variables():
    """Test required environment variables."""
    print("\n🔧 Testing environment variables...")
    
    required_vars = [
        "SECRET_KEY",
        "DATABASE_URL"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not getattr(settings, var, None):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("   Create a .env file with the required variables")
        return False
    else:
        print("✅ All required environment variables are set")
        return True


async def main():
    """Run all setup tests."""
    print("🚀 Testing Pafar Backend Setup\n")
    
    # Test environment variables
    env_ok = await test_environment_variables()
    
    # Test database
    db_ok = await test_database_connection()
    
    # Test Redis
    redis_ok = await test_redis_connection()
    
    print(f"\n📊 Setup Test Results:")
    print(f"   Environment: {'✅' if env_ok else '❌'}")
    print(f"   Database: {'✅' if db_ok else '❌'}")
    print(f"   Redis: {'✅' if redis_ok else '❌'}")
    
    if all([env_ok, db_ok, redis_ok]):
        print("\n🎉 All systems ready! You can start the FastAPI server.")
        print("   Run: uvicorn app.main:app --reload")
    else:
        print("\n⚠️  Some systems need attention before starting the server.")


if __name__ == "__main__":
    asyncio.run(main())