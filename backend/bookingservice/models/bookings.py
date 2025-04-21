from sqlalchemy import Integer, String, ForeignKey, DateTime, Enum, Float, Boolean, JSON, Text
from sqlalchemy.orm import mapped_column, Mapped, relationship, validates
from core.database import Base, CHAR_LENGTH
from sqlalchemy.dialects.postgresql import TIMESTAMP
from datetime import datetime, timezone
from enum import Enum as PyEnum
from uuid import uuid4 
from uuid import UUID
from typing import List, Optional
import sys

# Database type detection
if 'postgresql' in sys.argv:
    UUIDType = UUID(as_uuid=True)
    mappeditem = UUID
    default = uuid4
else:
    UUIDType = String(CHAR_LENGTH)
    mappeditem = str
    default = lambda: str(uuid4())


# Booking Model
class Booking(Base):
    __tablename__ = "bookings"

    # Booking ID (UUID as the primary key)
    id: Mapped[UUID] = mapped_column(UUIDType, primary_key=True, default=default)  # UUID with auto-generation
    ticket_id: Mapped[UUID] = mapped_column(ForeignKey("tickets.id"), nullable=False)  # Foreign key referencing User (UUID)
    code: Mapped[str] = mapped_column(String(CHAR_LENGTH), nullable=False)
    barcode: Mapped[Text] = mapped_column(Text, nullable=False)
    user_id: Mapped[UUID] = mapped_column(UUIDType, nullable=False)  # Foreign key referencing User (UUID)
    pick_up_location: Mapped[str] = mapped_column(String(CHAR_LENGTH), nullable=False)  # Pick-up location
    drop_off_location: Mapped[str] = mapped_column(String(CHAR_LENGTH), nullable=False)  # Drop-off location
    fare_amount: Mapped[Float] = mapped_column(Float, nullable=False)  # Fare amount for the trip
    isprotected: Mapped[Boolean] = mapped_column(Boolean, default=False)  # Fare amount for the trip
    seats: Mapped[List[dict]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))


    # Relationship to Payment (One Booking can have multiple payments)
    payments: Mapped[List[dict]] = mapped_column(JSON, nullable=True)
    
    def __repr__(self):
        return f"<Booking(id={self.id}, user_id={self.user_id}, ticket_id={self.ticket_id})>"
    
    # Method to convert the model instance to a dictionary
    def to_dict(self):
        return {
            "id": str(self.id),
            "ticket_id": str(self.ticket_id),
            "code": self.code,
            "barcode": self.barcode,
            "user_id": str(self.user_id),
            "pick_up_location": self.pick_up_location,
            "drop_off_location": self.drop_off_location,
            "fare_amount": self.fare_amount,
            "isprotected": self.isprotected,
            "seats": self.seats,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "payments": self.payments
        }