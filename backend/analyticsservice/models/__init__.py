# models/__init__.py

# Import all models that inherit from Base
from .bookings import DailyBookings,WeeklyBookings,MonthlyBookings,QuarterlyBookings,YearlyBookings

from core.database import Base,engine_db1  # or wherever your Base is defined

# Your async function for creating tables
async def create_tables():
    async with engine_db1.begin() as conn:
        # Ensure all models are in the Base
        await conn.run_sync(Base.metadata.create_all)

    print("Tables created successfully!")