from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID
from enum import Enum

# Enum for Quarter values (Q1, Q2, Q3, Q4)
class QuarterEnum(str, Enum):
    Q1 = "Q1"
    Q2 = "Q2"
    Q3 = "Q3"
    Q4 = "Q4"

# Enum for Months (1 to 12)
class MonthEnum(int, Enum):
    JANUARY = 1
    FEBRUARY = 2
    MARCH = 3
    APRIL = 4
    MAY = 5
    JUNE = 6
    JULY = 7
    AUGUST = 8
    SEPTEMBER = 9
    OCTOBER = 10
    NOVEMBER = 11
    DECEMBER = 12


# Pydantic model for DailyBookings
class DailyBookingsBase(BaseModel):
    count: int

    class Config:
        from_attributes = True

# Pydantic models for input validation and response formatting
class DailyBookingCreateUpdate(DailyBookingsBase):
    count: int


class DailyBookings(DailyBookingsBase):
    id: UUID


# Pydantic model for WeeklyBookings
class WeeklyBookingsBase(BaseModel):
    count: int
    duration: int  # Number of days for the week (typically 7)
    start_date: datetime
    end_date: datetime

    class Config:
        from_attributes = True

class WeeklyBookingCreateUpdate(WeeklyBookingsBase):
    count: int
    duration: int
    start_date: datetime
    end_date: datetime

class WeeklyBookings(WeeklyBookingsBase):
    id: UUID


# Pydantic model for MonthlyBookings
class MonthlyBookingsBase(BaseModel):
    count: int
    month: MonthEnum  # Month as an enum (1 to 12)
    year: int

    class Config:
        from_attributes = True

class MonthlyBookingCreateUpdate(MonthlyBookingsBase):
    count: int
    month: MonthEnum
    year: int


class MonthlyBookings(MonthlyBookingsBase):
    id: UUID


# Pydantic model for QuarterlyBookings
class QuarterlyBookingsBase(BaseModel):
    count: int
    quarter: QuarterEnum  # Quarter as an enum (Q1, Q2, Q3, Q4)
    year: int

    class Config:
        from_attributes = True

class QuarterlyBookingCreateUpdate(QuarterlyBookingsBase):
    count: int
    quarter: QuarterEnum
    year: int

class QuarterlyBookings(QuarterlyBookingsBase):
    id: UUID


# Pydantic model for YearlyBookings
class YearlyBookingsBase(BaseModel):
    count: int
    year: int

    class Config:
        from_attributes = True

class YearlyBookingCreateUpdate(YearlyBookingsBase):
    count: int
    year: int

class YearlyBookings(YearlyBookingsBase):
    id: UUID

class BookingLocationTypeEnum(str, Enum):
    CITY = "city"
    COUNTRY = "country"
    REGION = "region"

class LocationBase(BaseModel):
    name: str
    type: BookingLocationTypeEnum

class LocationCreate(LocationBase):
    pass

class LocationUpdate(LocationBase):
    name: Optional[str] = None
    type: Optional[BookingLocationTypeEnum] = None

class Location(LocationBase):
    id: UUID

    class Config:
        from_attributes = True


class BookingsByLocationBase(BaseModel):
    location_name: str
    location_type: BookingLocationTypeEnum
    booking_count: int

class BookingsByLocationCreate(BookingsByLocationBase):
    location_id: UUID

class BookingsByLocationUpdate(BookingsByLocationBase):
    location_name: Optional[str] = None
    location_type: Optional[BookingLocationTypeEnum] = None
    booking_count: Optional[int] = None

class BookingsByLocation(BookingsByLocationBase):
    id: UUID
    location_id: UUID

    class Config:
        from_attributes = True