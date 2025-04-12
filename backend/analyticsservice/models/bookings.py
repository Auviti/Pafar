from sqlalchemy import Enum, Integer, String, DateTime, ForeignKey, Boolean, Float, UUID as PGUUID, Text
from sqlalchemy.orm import mapped_column, Mapped, relationship
from core.database import Base, CHAR_LENGTH
from uuid import uuid4, UUID
from datetime import datetime
from typing import List, Optional
import enum
import sys


# Detect if using PostgreSQL for proper UUID support
if 'postgresql' in sys.argv:
    UUIDType = PGUUID(as_uuid=True)
    mappeditem = UUID
    default = uuid4
else:
    UUIDType = String(36)
    mappeditem = str
    default = lambda: str(uuid4())

# Enum for time intervals
class TimePeriod(enum.Enum):
    DAILY = "Daily"
    WEEKLY = "Weekly"
    MONTHLY = "Monthly"
    QUARTERLY = "Quarterly"
    YEARLY = "Yearly"


# Model for Daily Bookings
class DailyBookings(Base):
    __tablename__ = 'daily_bookings'

    id: Mapped[mappeditem] = mapped_column(UUIDType, primary_key=True, default=default)
    count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # Total bookings in that period
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)  # When the record was created
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # Last updated timestamp

    def __repr__(self):
        return f"<DailyBookings(id={self.id}, count={self.count}, created_at={self.created_at.isoformat()})>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "count": self.count,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


# Model for Weekly Bookings
class WeeklyBookings(Base):
    __tablename__ = 'weekly_bookings'

    id: Mapped[mappeditem] = mapped_column(UUIDType, primary_key=True, default=default)
    count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)  # Start date of the week
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)  # End date of the week

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<WeeklyBookings(id={self.id}, count={self.count}, start_date={self.start_date.isoformat()}, end_date={self.end_date.isoformat()})>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "count": self.count,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


# Model for Monthly Bookings
class MonthlyBookings(Base):
    __tablename__ = 'monthly_bookings'

    id: Mapped[mappeditem] = mapped_column(UUIDType, primary_key=True, default=default)
    count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    month: Mapped[int] = mapped_column(Integer, nullable=False)  # Month of the bookings (1-12)
    year: Mapped[int] = mapped_column(Integer, nullable=False)  # Year of the bookings (e.g., 2023)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<MonthlyBookings(id={self.id}, count={self.count}, month={self.month}, year={self.year})>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "count": self.count,
            "month": self.month,
            "year": self.year,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


# Model for Quarterly Bookings
class QuarterlyBookings(Base):
    __tablename__ = 'quarterly_bookings'

    id: Mapped[mappeditem] = mapped_column(UUIDType, primary_key=True, default=default)
    count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    quarter: Mapped[str] = mapped_column(String(10), nullable=False)  # Quarter value like "Q1", "Q2", etc.
    year: Mapped[int] = mapped_column(Integer, nullable=False)  # Year of the quarter

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<QuarterlyBookings(id={self.id}, count={self.count}, quarter={self.quarter}, year={self.year})>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "count": self.count,
            "quarter": self.quarter,
            "year": self.year,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


# Model for Yearly Bookings
class YearlyBookings(Base):
    __tablename__ = 'yearly_bookings'

    id: Mapped[mappeditem] = mapped_column(UUIDType, primary_key=True, default=default)
    count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    year: Mapped[int] = mapped_column(Integer, nullable=False)  # Year of the bookings

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<YearlyBookings(id={self.id}, count={self.count}, year={self.year})>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "count": self.count,
            "year": self.year,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }




class BookingLocationType(enum.Enum):
    CITY = "city"
    COUNTRY = "country"
    REGION = "region"

class BookingsByLocation(Base):
    __tablename__ = 'bookings_by_location'
    
    # Defining columns using the imported types
    id: Mapped[mappeditem] = mapped_column(UUIDType, primary_key=True, default=default)
    # Foreign key for Location
    location_id: Mapped[UUID] = mapped_column(ForeignKey('locations.id'), nullable=False)
    location_name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Enum for the location type
    location_type: Mapped[BookingLocationType] = mapped_column(Enum(BookingLocationType), nullable=False)
    
    # Booking count for this location
    booking_count: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Timestamps for creation and updates
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Optional relationship to Location model
    location = relationship('Location', back_populates='bookings')

    def __repr__(self):
        return f"<BookingsByLocation(location_name={self.location_name}, booking_count={self.booking_count})>"

# Sample of other models

class Location(Base):
    __tablename__ = 'locations'

    id: Mapped[mappeditem] = mapped_column(UUIDType, primary_key=True, default=default)
    # Name of the location (City, Region, or Country)
    name: Mapped[str] = mapped_column(String(CHAR_LENGTH), nullable=False)
    
    # Type of the location (City, Region, or Country)
    type: Mapped[BookingLocationType] = mapped_column(Enum(BookingLocationType), nullable=False)
    
    # Timestamps for creation and updates
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to bookings
    bookings = relationship('BookingsByLocation', back_populates='location')

    def __repr__(self):
        return f"<Location(name={self.name}, type={self.type})>"
