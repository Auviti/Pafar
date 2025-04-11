# models/__init__.py

# Import all models that inherit from Base
from .bookings import DailyBookings,WeeklyBookings,MonthlyBookings,QuarterlyBookings,YearlyBookings


from core.database import Base  # or wherever your Base is defined
