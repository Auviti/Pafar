from sqlalchemy import Integer, String, ForeignKey, Enum, DateTime, JSON, Float, CheckConstraint, Boolean, Text
from sqlalchemy.orm import mapped_column, Mapped, relationship, validates
from sqlalchemy.dialects.postgresql import TIMESTAMP

from core.database import Base, CHAR_LENGTH
from datetime import datetime, timezone
from enum import Enum as PyEnum
from uuid import UUID, uuid4
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

# Enum for Ticket Status
class TicketStatus(PyEnum):
    UPCOMING = "UPCOMING"
    ASSIGNED = "ASSIGNED"
    ONGOING = "ONGOING"
    COMPLETED = "COMPLETED"
    CANCELED = "CANCELED"

class TicketClass(PyEnum):
    ECONOMY = "ECONOMY"
    BUSINESS = "BUSINESS"
    FIRST_CLASS = "FIRST_CLASS"

class TicketType(PyEnum):
    ROUND = "ROUND"
    ONE_WAY = "ONE_WAY"
    MULTICITY = "MULTICITY"

# Ticket Model
class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[UUID] = mapped_column(UUIDType, primary_key=True, default=default)
    name: Mapped[str] = mapped_column(String(CHAR_LENGTH), nullable=False)

    status: Mapped[TicketStatus] = mapped_column(Enum(TicketStatus), nullable=False)
    ticket_class: Mapped[TicketClass] = mapped_column(Enum(TicketClass), default=TicketClass.ECONOMY)
    ticket_type: Mapped[TicketType] = mapped_column(Enum(TicketType), default=TicketType.ONE_WAY)

    vehicle_id: Mapped[str] = mapped_column(String(CHAR_LENGTH), nullable=False)

    trip_fare: Mapped[Float] = mapped_column(Float, nullable=False)
    passengers: Mapped[int] = mapped_column(Integer, nullable=False)

    startlocation: Mapped[str] = mapped_column(String(CHAR_LENGTH), nullable=False)
    currentlocation: Mapped[str] = mapped_column(String(CHAR_LENGTH), nullable=False)
    endlocation: Mapped[str] = mapped_column(String(CHAR_LENGTH), nullable=False)

    starts_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    ends_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

    suitcase: Mapped[Float] = mapped_column(Float, default=0.0, nullable=False, comment='0.02 per unit price for suitcase weight')
    handluggage: Mapped[Float] = mapped_column(Float, default=0.0, nullable=False, comment='0.02 per unit price for hand luggage weight')
    otherluggage: Mapped[Float] = mapped_column(Float, default=0.0, nullable=False, comment='0.02 per unit price for other luggage weight')

    __table_args__ = (
        CheckConstraint(suitcase >= 0, name="check_suitcase_weight_positive"),
        CheckConstraint(handluggage >= 0, name="check_handluggage_weight_positive"),
        CheckConstraint(otherluggage >= 0, name="check_otherluggage_weight_positive"),
    )

    @property
    def duration(self):
        """Calculate duration of the ticket (end - start)"""
        if self.starts_at and self.ends_at:
            return (self.ends_at - self.starts_at).total_seconds()
        return None

    @property
    def total_fare(self):
        """Calculate the total fare, considering luggage prices"""
        luggage_fare = 0.02 * (self.suitcase + self.handluggage + self.otherluggage)
        return self.trip_fare + luggage_fare

    def __repr__(self):
        return f"<Ticket(id={self.id}, startlocation={self.startlocation}, endlocation={self.endlocation}, duration={self.duration}, status={self.status}, fare_amount={self.total_fare})>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "status": self.status.value,
            "ticket_class": self.ticket_class.value,
            "ticket_type": self.ticket_type.value,
            "passengers": self.passengers,
            "vehicle_id": str(self.vehicle_id),
            "trip_fare": self.trip_fare,
            "startlocation": self.startlocation,
            "currentlocation": self.currentlocation,
            "endlocation": self.endlocation,
            "starts_at": self.starts_at.isoformat() if self.starts_at else None,
            "ends_at": self.ends_at.isoformat() if self.ends_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "suitcase": self.suitcase,
            "handluggage": self.handluggage,
            "otherluggage": self.otherluggage,
            "duration": self.duration,
            "total_fare": self.total_fare
        }
