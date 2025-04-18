from sqlalchemy import Integer, String, ForeignKey, DateTime, Enum, Float, Boolean, JSON, Text
from sqlalchemy.orm import mapped_column, Mapped, relationship, validates
from core.database import Base, CHAR_LENGTH
from sqlalchemy.orm import mapped_column
from datetime import datetime
from enum import Enum as PyEnum
from uuid import uuid4 
from uuid import UUID
from typing import List, Optional
import sys



# Database type detection
if 'postgresql' in sys.argv:
    # Use native UUID for PostgreSQL
    UUIDType = UUID(as_uuid=True)
    mappeditem = UUID
    default = uuid4
else:
    # Use string representation for other databases
    UUIDType = String(36)
    mappeditem = str
    default = lambda: str(uuid4())

# Enum for Booking Status
class BookingStatus(PyEnum):
    PENDING = "Pending"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"
    IN_PROGRESS = "In Progress"

# Booking Model
class Booking(Base):
    __tablename__ = "bookings"

    # Booking ID (UUID as the primary key)
    id: Mapped[UUID] = mapped_column(UUIDType, primary_key=True, default=default)  # UUID with auto-generation
    ride_id: Mapped[UUID] = mapped_column(ForeignKey("rides.id"), nullable=False)  # Foreign key referencing User (UUID)
    code: Mapped[str] = mapped_column(String(CHAR_LENGTH), nullable=False)
    barcode: Mapped[str] = mapped_column(String(CHAR_LENGTH), nullable=False)
    user_id: Mapped[UUID] = mapped_column(Text, nullable=False)  # Foreign key referencing User (UUID)
    pick_up_location: Mapped[str] = mapped_column(String(CHAR_LENGTH), nullable=False)  # Pick-up location
    drop_off_location: Mapped[str] = mapped_column(String(CHAR_LENGTH), nullable=False)  # Drop-off location
    booking_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)  # Date and time of the booking
    booking_status: Mapped[BookingStatus] = mapped_column(Enum(BookingStatus), default=BookingStatus.PENDING)  # Booking status (Pending, Completed, etc.)
    fare_amount: Mapped[Float] = mapped_column(Float, nullable=False)  # Fare amount for the trip
    isprotected: Mapped[Boolean] = mapped_column(Boolean, default=False)  # Fare amount for the trip
    seats: Mapped[List[dict]] = mapped_column(JSON, nullable=False)

    # Relationship to Payment (One Booking can have multiple payments)
    payments: Mapped[List[dict]] = mapped_column(JSON, nullable=True)
    
    def __repr__(self):
        return f"<Booking(id={self.id}, user_id={self.user_id}, ride_id={self.ride_id}, booking_status={self.booking_status}, booking_time={self.booking_time})>"
