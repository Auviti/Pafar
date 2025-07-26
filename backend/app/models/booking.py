"""
Booking model for trip reservations and seat management.
"""
import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, String, DateTime, ForeignKey, DECIMAL, Integer, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base


class BookingStatus(str, enum.Enum):
    """Booking status enumeration."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class PaymentStatus(str, enum.Enum):
    """Payment status enumeration."""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class Booking(Base):
    """Booking model for trip reservations."""
    
    __tablename__ = "bookings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    trip_id = Column(UUID(as_uuid=True), ForeignKey("trips.id"), nullable=False)
    seat_numbers = Column(JSON, nullable=False)
    total_amount = Column(DECIMAL(10, 2), nullable=False)
    status = Column(Enum(BookingStatus), default=BookingStatus.PENDING, nullable=False)
    booking_reference = Column(String(20), unique=True, nullable=False, index=True)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="bookings")
    trip = relationship("Trip", back_populates="bookings")
    payments = relationship("Payment", back_populates="booking")
    reviews = relationship("Review", back_populates="booking")
    
    @property
    def seat_count(self) -> int:
        """Get number of seats booked."""
        return len(self.seat_numbers) if self.seat_numbers else 0
    
    def __repr__(self) -> str:
        return f"<Booking(id={self.id}, reference={self.booking_reference}, status={self.status})>"